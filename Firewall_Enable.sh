#! /bin/bash
./vic-machine-linux update firewall \
--target https://vc1.gsslabs.org/Default-DC \
--user administrator@vsphere.local \
--compute-resource Default-CL \
--thumbprint=B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--allow
