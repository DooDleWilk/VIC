#! /bin/bash
./vic-machine-linux debug \
--target vcsa1.gsslabs.org \
--user administrator@vsphere.local \
--password 'VMware123!' \
--compute-resource Default-CL \
--thumbprint B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--enable-ssh \
--rootpw 'VMware123!' \
--name VCH00-00
