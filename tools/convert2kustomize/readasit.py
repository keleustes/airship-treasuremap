#!/usr/bin/python3

# Copyright 2018 AT&T Network Cloud Team
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

import yaml
import requests
import sys
import json
import logging
import os
import argparse
import copy
import yaml
import glob
import csv
import re
from collections import OrderedDict


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


def build_var(name, objrefkind, objrefname, path):
    objref = {}
    objref["kind"] = objrefkind
    objref["name"] = objrefname
    if "Deckhand" in objrefkind:
        objref["apiVersion"] = "deckhand.airshipit.org/v1alpha1"
    if "Pegleg" in objrefkind:
        objref["apiVersion"] = "pegleg.airshipit.org/v1alpha1"
    if "Armada" in objrefkind:
        objref["apiVersion"] = "armada.airshipit.org/v1alpha1"
    if "Shipyard" in objrefkind:
        objref["apiVersion"] = "shipyard.airshipit.org/v1alpha1"
    if "Drydock" in objrefkind:
        objref["apiVersion"] = "drydock.airshipit.org/v1alpha1"
    fieldref = {}
    # fieldref["fieldpath"] = path.replace(".","/")
    fieldref["fieldpath"] = path
    var = {}
    var["name"] = name
    var["objref"] = objref
    var["fieldref"] = fieldref
    return var


def build_varref(name, objrefkind, path):
    var = {}
    var["kind"] = objectrefkkind
    var["path"] = path
    return var


def add_key(key, node, varname, thepattern):
    fullkey = key.pop(0)
    fullkey = fullkey.replace("[", " ").replace("]", "")
    keyparts = fullkey.split(" ")
    thekey = keyparts[0]
    theindex = -1
    if len(keyparts) == 2:
        theindex = int(keyparts[1])
        if thekey not in node:
            node[thekey] = []
        if not isinstance(node[thekey], list):
            print("List issue with " + varname + " " + str(theindex) + " " + thekey)
            return
        else:
            currentlen = len(node[thekey])

        if (theindex >= currentlen):
            for i in range(currentlen, theindex + 1):
                node[thekey].append({})

    if (len(key) == 0):
        if (thepattern):
            if thekey not in node:
                if (thepattern == "DB_NAME") and (thekey == "path"):
                    node[thekey] = "/" + varname
                else:
                    print("Pattern issue with " + varname + " " + thepattern + " " + thekey + " " + str(theindex))
                    node[thekey] = {"pattern-boggus": thepattern, "varname-boggus": varname}
            else:
                if (theindex != -1):
                    node[thekey][theindex] = node[thekey][theindex].replace(thepattern, varname)
                else:
                    node[thekey] = node[thekey].replace(thepattern, varname)
        else:
            if (theindex != -1):
                node[thekey][theindex] = varname
            else:
                node[thekey] = varname
    else:
        if (theindex != -1):
            add_key(key, node[thekey][theindex], varname, thepattern)
        else:
            if thekey not in node:
                node[thekey] = {}
            elif not isinstance(node[thekey], dict):
                # boggus replacement
                org = node[thekey]
                node[thekey] = {"parent-inline": org}

            add_key(key, node[thekey], varname, thepattern)


def load_file(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}
    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)

        docs2 = list(docs)
        for doc in docs2:
            if ("substitutions" in doc["metadata"]):
                if (doc["kind"] not in varrefs):
                    varrefs[doc["kind"]] = {}
                for entry in doc["metadata"]["substitutions"]:
                    if entry["src"]["path"] != ".":
                        varpath = "spec" + entry["src"]["path"].replace("[", "._").replace("]", "_")
                        varname = ".".join([entry["src"]["kind"], entry["src"]["name"].replace("_", "-"), varpath])
                    else:
                        varpath = "spec"
                        varname = ".".join([entry["src"]["kind"], entry["src"]["name"].replace("_", "-"), varpath])
                    vars[varname] = build_var(varname, entry["src"]["kind"], entry["src"]["name"].replace("_", "-"), varpath)

                    if (isinstance(entry["dest"], list)):
                        for subdest in entry["dest"]:
                            dest = subdest["path"].split(".")
                            dest[0] = "spec"
                            thepattern = None
                            if ("pattern" in subdest):
                                thepattern = subdest["pattern"].replace("'", "").replace("(", "").replace(")", "")

                            varrefs[doc["kind"]]["/".join(dest).replace("[", "/_").replace("]", "_")] = doc["kind"]
                            add_key(dest, doc, "$(" + varname + ")", thepattern)
                    else:
                        dest = entry["dest"]["path"].split(".")
                        dest[0] = "spec"
                        thepattern = None
                        if ("pattern" in entry["dest"]):
                            thepattern = entry["dest"]["pattern"].replace("'", "").replace("(", "").replace(")", "")

                        varrefs[doc["kind"]]["/".join(dest).replace("[", "/_").replace("]", "_")] = doc["kind"]
                        add_key(dest, doc, "$(" + varname + ")", thepattern)
                doc["metadata"].pop("substitutions")

    # Save the list of vars to add to the kustomization.yaml
    if False:
        varlist = []
        for key, value in vars.items():
            varlist.append(value)
        sortedlist = sorted(varlist, key=lambda k: k['name'])
        with open("kustomization.vars.yaml", 'w') as stream:
            yaml.dump(sortedlist, stream, default_flow_style=False)

    # Save the list of varref to add to the kustomizeconfig/crd.yaml
    if False:
        for key, value in varrefs.items():
            with open("res/" + key + ".yaml", 'w') as stream:
                varlist = []
                for key2, value2 in value.items():
                    varlist.append({"path": key2, "kind": value2})
                sortedlist = sorted(varlist, key=lambda k: k['path'])
                yaml.dump(sortedlist, stream, default_flow_style=False)

    return docs2


def remove_metadata(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}
    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)

        docs2 = list(docs)
        for doc in docs2:
            if ("substitutions" in doc["metadata"]):
                doc["metadata"].pop("substitutions")

    return docs2


def move_namespace(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}
    res = {}
    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)
        res = move_namespace_dict(list(docs, filename))
    return res


def move_namespace_dict(docs2, filename):
    for doc in docs2:
        name = doc["metadata"]["name"]
        kind = doc["kind"]
        if ("namespace" in doc["spec"]):
            if ("-htk" in doc["spec"]["namespace"]) or ("helm-toolkit" in doc["spec"]["namespace"]):
                doc["metadata"]["namespace"] = "pegleg"
            else:
                doc["metadata"]["namespace"] = doc["spec"]["namespace"]
            doc["spec"].pop("namespace")
        if ("namespace" not in doc["metadata"]):
            if ("Pegleg" in kind):
                doc["metadata"]["namespace"] = "pegleg"
            elif ("Deckhand" in kind):
                doc["metadata"]["namespace"] = "pegleg"
            elif ("Drydock" in kind):
                doc["metadata"]["namespace"] = "drydock"
            elif ("Promenade" in kind):
                doc["metadata"]["namespace"] = "drydock"
            elif ("Shipyard" in kind):
                doc["metadata"]["namespace"] = "shipyard"
            elif ("ArmadaManifest" in kind):
                doc["metadata"]["namespace"] = "shipyard"
            elif ("ArmadaChartGroup" in kind):
                doc["metadata"]["namespace"] = "shipyard"
            else:
                if ("tenant" in filename):
                    doc["metadata"]["namespace"] = "tenant-ceph"
                elif ("ucp" in filename):
                    doc["metadata"]["namespace"] = "ucp"
                elif ("osh" in filename):
                    doc["metadata"]["namespace"] = "osh-infra"
                elif ("openstack" in filename):
                    doc["metadata"]["namespace"] = "openstack"
                elif ("kubernetes" in filename):
                    doc["metadata"]["namespace"] = "kube-system"
                else:
                    doc["metadata"]["namespace"] = "boggus"

    return docs2


def add_namespace(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}
    res = {}
    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)
        res = add_namespace_dict(list(docs), filename)
    return res


def add_namespace_dict(docs2, filename):
    for doc in docs2:
        name = doc["metadata"]["name"]
        kind = doc["kind"]
        if ("namespace" not in doc["metadata"]):
            if ("Pegleg" in kind):
                doc["metadata"]["namespace"] = "pegleg"
            elif ("Deckhand" in kind):
                doc["metadata"]["namespace"] = "deckhand"
            elif ("Promenade" in kind):
                doc["metadata"]["namespace"] = "promenade"
            elif ("Shipyard" in kind):
                doc["metadata"]["namespace"] = "shipyard"
            else:
                if ("tenant" in filename):
                    doc["metadata"]["namespace"] = "tenant-ceph"
                elif ("ucp" in filename):
                    doc["metadata"]["namespace"] = "ucp"
                elif ("osh" in filename):
                    doc["metadata"]["namespace"] = "osh-infra"
                elif ("openstack" in filename):
                    doc["metadata"]["namespace"] = "openstack"
                elif ("kubernetes" in filename):
                    doc["metadata"]["namespace"] = "kube-system"
                else:
                    doc["metadata"]["namespace"] = "boggus"
        # print("{} {} in {}".format(kind, name, doc["metadata"]["namespace"]))

    return docs2


def find_key(key, node):
    thekey = key.pop(0)
    theindex = -1
    if thekey.startswith('_') and thekey.endswith('_'):
        theindex = int(thekey.replace("_", ""))

    if (len(key) == 0):
        if (theindex != -1):
            return node[theindex]
        else:
            return node[thekey]
    else:
        if (theindex != -1):
            return find_key(key, node[theindex])
        else:
            return find_key(key, node[thekey])


def check_var_or_substitution(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}

    with open("kustomization.vars.yaml", 'r') as stream:
        vars = yaml.load(stream)

    realvars = []
    realsubs = []

    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)

        docs2 = list(docs)

        for var in vars:
            path = var["fieldref"]["fieldpath"]
            name = var["name"]
            objkind = var["objref"]["kind"]
            objname = var["objref"]["name"]

            found = None
            for doc in docs2:
                if (doc["kind"] == objkind) and (doc["metadata"]["name"] == objname):
                    found = doc
                    continue

            if found:
                print("Found " + name)
                res = find_key(path.split("."), found)
                if isinstance(res, dict):
                    realsubs.append(var)
                else:
                    realvars.append(var)
            else:
                print("Unknown " + name)

    sortedlist = sorted(realvars, key=lambda k: k['name'])
    with open("kustomization.realvars.yaml", 'w') as stream:
        yaml.dump(sortedlist, stream, default_flow_style=False)
    sortedlist = sorted(realsubs, key=lambda k: k['name'])
    with open("kustomization.realsubs.yaml", 'w') as stream:
        yaml.dump(sortedlist, stream, default_flow_style=False)

    return docs2


def extract_keys(thedict, prefix):
    res = []
    for key, value in thedict.items():
        current = prefix + "." + key
        if isinstance(value, dict):
            res.extend(extract_keys(value, current))
        else:
            res.append(current)
    return res


def extract_values_syntax(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    docs2 = []
    vars = {}
    varrefs = {}
    with open(filename, 'r') as stream:
        try:
            docs = yaml.load_all(stream)
        except yaml.YAMLError as exc:
            print(exc)
        docs2 = list(docs)
        for doc in docs2:
            if (doc["kind"] == "ArmadaChart") and ("values" in doc["spec"]):
                if (isinstance(doc["spec"]["values"], dict)):
                    print("\n".join(extract_keys(doc["spec"]["values"], "")))

    return docs2


def extract_one_value_yaml(filename):
    """
    TBD
    Args:
       tbd
    Returns:
       tbd
    """
    doc = []
    with open(filename, 'r') as stream:
        try:
            doc = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
        if (isinstance(doc, dict)):
            print("\n".join(extract_keys(doc, "")))

    return doc


def save_file(filename, docs):
    with open(filename, 'w') as stream:
        yaml.safe_dump_all(docs,
                           stream,
                           explicit_start=True,
                           explicit_end=False,
                           default_flow_style=False)


def add_to_structdict(structname, structdict):
    if (structname not in structdict):
        structdict[structname] = []


def generate_go_struct(structname, fields):
    print('type {} struct {}'.format(structname, '{'))
    for field in fields:
        print('    {}'.format(field))
    print('{}'.format('}'))
    print('')


# Simple script to generate set of go struct that could be
# used to refine the ArmadaChartValue field
def to_go(filepath):
    structdict = {}
    structname = "AV"
    add_to_structdict(structname, structdict)
    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            # Create a line as follow:
            # Upgrade *ArmadaUpgrade `json:"upgrade,omitempty"`
            fieldname = line.strip()
            camelcase = ''.join(x for x in fieldname.replace("_", " ").title() if not x.isspace())
            substructname = structname + camelcase
            structdict[structname].append('// {} contains tbd'.format(fieldname))
            structdict[structname].append('{} *{} `json:"{},omitempty"`'.format(camelcase, substructname, fieldname))
            add_to_structdict(substructname, structdict)
            line = fp.readline()
            cnt += 1
    for structname, fields in structdict.items():
        generate_go_struct(structname, fields)

    return structdict


if __name__ == "__main__":
    __represent_multiline_yaml_str()
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--command',
                        help="Command to run",
                        type=str, choices=["extract_subst", "remove_metadata", "move_namespace", "add_namespace", "check", "values", "onevalue", "togo"],
                        default="extract_subst")
    parser.add_argument('-f', '--filename',
                        help="filename",
                        type=str,
                        default="airship.yaml")

    args = parser.parse_args()

    if (args.command == "extract_subst"):
        docs = load_file(args.filename)
        docs2 = move_namespace_dict(docs, args.filename)
        docs3 = add_namespace_dict(docs2, args.filename)
        save_file(args.filename + ".new", docs3)
    elif (args.command == "remove_metadata"):
        docs = remove_metadata(args.filename)
        save_file(args.filename + ".simple", docs)
    elif (args.command == "move_namespace"):
        docs = move_namespace(args.filename)
        save_file(args.filename + ".simple", docs)
    elif (args.command == "add_namespace"):
        docs = add_namespace(args.filename)
        save_file(args.filename + ".simple", docs)
    elif (args.command == "check"):
        docs = check_var_or_substitution(args.filename)
    elif (args.command == "values"):
        docs = extract_values_syntax(args.filename)
    elif (args.command == "onevalue"):
        docs = extract_one_value_yaml(args.filename)
    elif (args.command == "togo"):
        docs = to_go(args.filename)
    else:
        pass
