#!/usr/bin/env python3

# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# versions.yaml file updater tool
#
# Being run in directory with versions.yaml, will create versions.new.yaml,
# with updated git commit id's to the latest HEAD in references of all
# charts.
#
# In addition to that, the tool updates references to the container images
# with the tag, equal to the latest image which exists on quay.io
# repository and is available for download.
#

import argparse
import datetime
from functools import reduce
import json
import logging
import operator
import os
import requests
import sys
import time

try:
    import git
    import yaml
except ImportError as e:
    sys.exit("Failed to import git/yaml libraries needed to run" +
             "this tool %s" % str(e))

descr_text = "Being run in directory with versions.yaml, will create \
            versions.new.yaml, with updated git commit id's to the \
            latest HEAD in references of all charts. In addition to \
            that, the tool updates references to the container images \
            with the tag, equal to the latest image which exists on \
            quay.io repository and is available for download."
parser = argparse.ArgumentParser(description=descr_text)

# Dictionary containing container image repository url to git url mapping
#
# We expect that each image in container image repository has image tag which
# equals to the git commit id of the HEAD in corresponding git repository.
#
# NOTE(roman_g): currently this is not the case, and image is built/tagged not
# on every merge, and there could be a few hours delay between merge and image
# re-built and published due to the OpenStack Foundation Zuul infrastructure
# being overloaded.
image_repo_git_url = {
    # airflow image is built from airship-shipyard repository
    'quay.io/airshipit/airflow': 'https://opendev.org/airship/shipyard',
    'quay.io/airshipit/armada': 'https://opendev.org/airship/armada',
    'quay.io/airshipit/deckhand': 'https://opendev.org/airship/deckhand',
    # yes, divingbell image is just Ubuntu 16.04 image, and we don't check it's tag
    #'docker.io/ubuntu': 'https://opendev.org/airship/divingbell',
    'quay.io/airshipit/drydock': 'https://opendev.org/airship/drydock',
    # maas-{rack,region}-controller images are built from airship-maas repository
    'quay.io/airshipit/maas-rack-controller': 'https://opendev.org/airship/maas',
    'quay.io/airshipit/maas-region-controller': 'https://opendev.org/airship/maas',
    'quay.io/airshipit/pegleg': 'https://opendev.org/airship/pegleg',
    'quay.io/airshipit/promenade': 'https://opendev.org/airship/promenade',
    'quay.io/airshipit/shipyard': 'https://opendev.org/airship/shipyard',
    # sstream-cache image is built from airship-maas repository
    'quay.io/airshipit/sstream-cache': 'https://opendev.org/airship/maas',
    'quay.io/attcomdev/nagios': 'https://github.com/att-comdev/nagios',
    'quay.io/attcomdev/prometheus-openstack-exporter':
        'https://github.com/att-comdev/prometheus-openstack-exporter'
}

logging.basicConfig(level=logging.INFO)

# Temporary dict of git url's and cached commit id's: {'git_url': 'commit_id'}
global git_url_commit_ids
git_url_commit_ids = {}
# Temporary dict of image repo's and status of image on quay.io
global image_repo_status
image_repo_status = {}
dict_path = None


def __represent_multiline_yaml_str():
    """Compel ``yaml`` library to use block style literals for multi-line
    strings to prevent unwanted multiple newlines.

    """

    yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str

    def repr_str(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(
                'tag:yaml.org,2002:str', data, style='|')
        return dumper.org_represent_str(data)

    yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)


__represent_multiline_yaml_str()


def inverse_dict(dic):
    """Accepts dictionary, returns dictionary where keys become values,
    and values become keys"""
    new_dict = {}
    for k, v in dic.items():
        new_dict[v] = k
    return new_dict


git_url_image_repo = inverse_dict(image_repo_git_url)


# https://stackoverflow.com/a/35585837
def lsremote(url, remote_ref):
    """Accepts git url and remote reference, returns git commit id."""
    git_commit_id_remote_ref = {}
    g = git.cmd.Git()
    logging.info("Fetching %s %s reference...", url, remote_ref)
    hash_ref_list = g.ls_remote(url, remote_ref).split('\t')
    git_commit_id_remote_ref[hash_ref_list[1]] = hash_ref_list[0]
    return git_commit_id_remote_ref[remote_ref]


def get_commit_id(url):
    """Accepts url of git repo and returns corresponding git commit hash"""
    # If we don't have this git url in our url's dictionary,
    # fetch latest commit ID and add new dictionary entry
    logging.debug('git_url_commit_ids: %s', git_url_commit_ids)
    if url not in git_url_commit_ids:
        logging.debug("git url: %s" +
                      " is not in git_url_commit_ids dict;" +
                      " adding it with HEAD commit id", url)
        git_url_commit_ids[url] = lsremote(url, 'HEAD')

    return git_url_commit_ids[url]


def get_image_tag(image):
    """Get latest image tag from quay.io,
    returns 0 (image not hosted on quay.io), True, or False
    """
    if not image.startswith('quay.io/'):
        logging.info("Unable to verify if image %s" +
                     " is in containers repository: only quay.io is" +
                     " supported at the moment", image)
        return 0

    # If we don't have this image in our images's dictionary,
    # fetch latest tag and add new dictionary entry
    logging.debug('image_repo_status: %s', image_repo_status)
    if image not in image_repo_status:
        logging.debug("image: %s" +
                      " is not in image_repo_status dict;" +
                      " adding it with latest tag", image)
        image_repo_status[image] = get_image_latest_tag(image)

    return image_repo_status[image]


def get_image_latest_tag(image):
    """Get image tags from quay.io,
    returns latest image tag matching filter, or latest image tag if filter is not
    matched or not set, or 0 if a problem occured.
    """

    attempt = 0
    max_attempts = 5

    hash_image = image.split('/')
    url = 'https://quay.io/api/v1/repository/{}/{}/tag/'
    url = url.format(hash_image[1], hash_image[2])
    logging.info("Fetching tags for image %s (%s)...", image, url)

    while attempt < max_attempts:
        attempt = attempt + 1
        try:
            res = requests.get(url, timeout=5)
            if res.ok:
                break
        except requests.exceptions.Timeout:
            logging.warning("Timed out fetching url %s for %d attempt(s)", url, attempt)
            time.sleep(1)
        except requests.exceptions.TooManyRedirects:
            logging.error("Failed to fetch url %s, TooManyRedirects", url)
            return 0
        except requests.exceptions.RequestException as e:
            logging.error("Failed to fetch url %s, error: %s", url, e)
            return 0
    if attempt == max_attempts:
        logging.error("Failed to connect to quay.io for %d attempt(s)", attempt)
        return 0

    if res.status_code != 200:
        logging.error("Image %s is not available on quay.io or " +
                      "requires authentication", image)
        return 0

    try:
        res = res.json()
    except json.decoder.JSONDecodeError: # pylint: disable=no-member
        logging.error("Unable to parse response from quay.io (%s)", res.url)
        return 0

    try:
        possible_tag = None
        for tag in res['tags']:
            # skip images which are old (have 'end_ts'), and
            # skip images tagged with "*latest*" or "*master*"
            if 'end_ts' in tag or any(i in tag['name'] for i in ('latest', 'master')):
                continue

            # simply return first found tag is we don't have filter set
            if not tag_filter:
                return tag['name']

            # return tag matching filter, if we have filter set
            if tag_filter in tag['name']:
                return tag['name']

            logging.info("Skipping tag %s as not matching to the filter %s",
                        tag['name'], tag_filter)
            if not possible_tag:
                possible_tag = tag['name']

        if possible_tag:
            logging.info("Couldn't find better tag than %s", possible_tag)
            return possible_tag

    except KeyError:
        logging.error("Unable to parse response from quay.io (%s)", res.url)
        return 0

    logging.error("Image without end_ts in path %s not found", image)
    return 0


# https://stackoverflow.com/a/14692747
def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    get_by_path(root, items[:-1])[items[-1]] = value


# Based on http://nvie.com/posts/modifying-deeply-nested-structures/
def traverse(obj, dict_path=None):
    """Accepts Python dictionary with values.yaml contents,
    updates it with latest git commit id's.
    """
    logging.debug('traverse: dict_path: %s, object type: %s, object: %s',
                  dict_path, type(obj), obj)

    if dict_path is None:
        dict_path = []

    if isinstance(obj, dict):
        # It's a dictionary element
        logging.debug('this object is a dictionary')

        for k, v in obj.items():
            # If value v we are checking is a dictionary itself, and this
            # dictionary contains key named 'type', and a value of key 'type'
            # equals 'git', then
            if isinstance(v, dict) and 'type' in v and v['type'] == 'git':

                old_git_commit_id = v['reference']
                git_url = v['location']

                if skip_list and k in skip_list:
                    logging.info("Ignoring chart %s, it is in a skip list (%s)", k, git_url)
                    continue

                new_git_commit_id = get_commit_id(git_url)

                # Update git commit id in reference field of dictionary
                if old_git_commit_id != new_git_commit_id:
                    logging.info("Updating git reference for chart %s from %s to %s (%s)",
                                 k, old_git_commit_id, new_git_commit_id,
                                 git_url)
                    v['reference'] = new_git_commit_id
                else:
                    logging.info("Git reference %s for chart %s is already up to date (%s)",
                                 old_git_commit_id, k, git_url)
            else:
                logging.debug("value %s inside object is not a dictionary, or it does not " +
                              "contain key \'type\' with value \'git\', skipping", v)

            # Traverse one level deeper
            traverse(v, dict_path + [k])
    elif isinstance(obj, list):
        # It's a list element
        logging.debug('this object is a list')

        for elem in obj:
            # TODO: Do we have any git references or container image tags in
            # versions.yaml which are inside lists? Probably not.
            traverse(elem, dict_path + [[]])
    else:
        # It's already a value
        logging.debug('this object is a value')
        v = obj

        # Searching for container image repositories, we are only intrested in
        # strings; there could also be booleans or other types we are not interested in.
        if isinstance(v, str):
            for image_repo in image_repo_git_url:
                if image_repo in v:
                    logging.debug('image_repo %s is in %s string', image_repo, v)

                    # hash_v: {'&whatever repo_url', 'git commit id tag'}
                    # Note: 'image' below could contain not just image, but also
                    # '&ref host.domain/path/image'
                    hash_v = v.split(":")
                    image, old_image_tag = hash_v

                    if skip_list and image.endswith(skip_list):
                        logging.info("Ignoring image %s, it is in a skip list", image)
                        continue

                    new_image_tag = get_image_tag(image)
                    if new_image_tag == 0:
                        logging.error("Failed to get image tag for %s", image)
                        sys.exit(1)

                    # Update git commit id in tag of container image
                    if old_image_tag != new_image_tag:
                        logging.info("Updating git commit id in " +
                                     "tag of container image %s from %s to %s",
                                     image, old_image_tag, new_image_tag)
                        set_by_path(versions_data_dict, dict_path, image + ':' + new_image_tag)

                    else:
                        logging.info("Git tag %s for container " +
                                     "image %s is already up to date",
                                     old_image_tag, image)
                else:
                    logging.debug('image_repo %s is not in %s string, skipping', image_repo, v)
        else:
            logging.debug('value %s is not string, skipping', v)


if __name__ == '__main__':
    """Small Main program
    """

    parser.add_argument('--in-file', default='versions.yaml',
                        help='/path/to/versions.yaml input file; default - "./versions.yaml"')
    parser.add_argument('--out-file', default='versions.yaml',
                        help='name of output file; default - "versions.yaml" (overwrite existing)')
    parser.add_argument('--skip',
                        help='comma-delimited list of images and charts to skip during the update')
    parser.add_argument('--tag-filter',
                        help='e.g. "ubuntu"; update would use image ref. tags on quay.io matching the filter')

    args = parser.parse_args()
    in_file = args.in_file
    out_file = args.out_file
    if args.skip:
        skip_list = tuple(args.skip.strip().split(","))
        logging.info("Skip list: %s", skip_list)
    else:
        skip_list = None

    tag_filter = args.tag_filter
    logging.info("Tag filter: %s", tag_filter)

    if os.path.basename(out_file) != out_file:
        logging.error("Name of the output file must not contain path, " +
                      "but only the file name.")
        print("\n")
        parser.print_help()
        sys.exit(1)

    if os.path.isfile(in_file):
        out_file = os.path.join(os.path.dirname(os.path.abspath(in_file)), out_file)
        with open(in_file, 'r') as f:
            f_old = f.read()
            versions_data_dict = yaml.safe_load(f_old)
    else:
        logging.error("Can\'t find versions.yaml file.")
        print("\n")
        parser.print_help()
        sys.exit(1)

    # Traverse loaded yaml and change it
    traverse(versions_data_dict)

    with open(out_file, 'w') as f:
        if os.path.samefile(in_file, out_file):
            logging.info("Overwriting %s", in_file)
        f.write(yaml.safe_dump(versions_data_dict,
                               default_flow_style=False,
                               explicit_end=True, explicit_start=True,
                               width=4096))
        logging.info("New versions.yaml created as %s", out_file)
