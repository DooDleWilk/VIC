#! /bin/bash
./vic-machine-linux inspect config \
--target vcsa1.gsslabs.org \
--user administrator@vsphere.local \
--password 'VMware123!' \
--thumbprint B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--name VCH00-00
