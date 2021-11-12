#! /bin/bash
./vic-machine-linux configure \
--target vcsa1.gsslabs.org \
--user administrator@vsphere.local \
--password 'VMware123!' \
--container-network Container-Net_192.168.120.0:Net-120 \
--container-network-gateway Container-Net_192.168.120.0:192.168.120.254/24 \
--container-network-ip-range Container-Net_192.168.120.0:192.168.120.0/24 \
--container-network-dns Container-Net_192.168.120.0:192.168.0.10 \
--container-network-firewall Container-Net_192.168.120.0:open \
--container-network Management-DVS:Net-MGMT \
--container-network-firewall Management-DVS:open \
--thumbprint=B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--name VCH00-00
