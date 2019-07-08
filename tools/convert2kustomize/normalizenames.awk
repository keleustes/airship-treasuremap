/name: osh_/ {
	gsub("_","-")
}

/name: ucp_/ {
	gsub("_","-")
}

/name: airship_ssh_public_key/ {
	gsub("_","-")
}

/name: airsloop_crypt_password/ {
	gsub("_","-")
}

/name: airsloop_ssh_public_key/ {
	gsub("_","-")
}

/name: ceph_fsid/ {
	gsub("_","-")
}

/name: ceph_swift_keystone_password/ {
	gsub("_","-")
}

/name: compute_r720xd/ {
	gsub("_","-")
}

/name: DELL_HP_Generic/ {
	gsub("_","-")
}

/name: dell_r720xd/ {
	gsub("_","-")
}

/name: ipmi_admin_password/ {
	gsub("_","-")
}

/name: MY_USER_ssh_public_key/ {
	gsub("_","-")
}

/name: postgresql_airflow_celery_db/ {
	gsub("_","-")
}

/name: private_docker_key/ {
	gsub("_","-")
}

/name: service_client/ {
	gsub("_","-")
}

/name: service_peer/ {
	gsub("_","-")
}

/name: tenant_ceph_fsid/ {
	gsub("_","-")
}

{
	print $0;
}
