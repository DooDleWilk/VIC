#! /bin/bash
./vic-machine-linux configure \
--target vcsa1.gsslabs.org \
--user administrator@vsphere.local \
--password 'VMware123!' \
--volume-store iSCSI-2/VCH00-00-vol:default \
--volume-store 'nfs://192.168.0.120/mnt/NFSProd?uid=0&gid=0:nfs-direct' \
--volume-store 'nfs://192.168.0.152/export?uid=0&gid=0:nfs-ubuntu' \
--thumbprint=B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--name VCH00-00
