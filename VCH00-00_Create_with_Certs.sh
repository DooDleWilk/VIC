#! /bin/bash
./vic-machine-linux create \
--target https://vcsa1.gsslabs.org/Default-DC \
--user administrator@vsphere.local \
--password 'VMware123!' \
--compute-resource Default-CL \
--bridge-network Bridge00-00_PortGroup \
--public-network Public-00 \
--public-network-ip 192.168.100.50/24 \
--public-network-gateway 192.168.100.254 \
--dns-server 192.168.0.10 \
--container-network Container-Net_192.168.120.0:Net-120 \
--container-network-gateway Container-Net_192.168.120.0:192.168.123.254/22 \
--container-network-ip-range Container-Net_192.168.120.0:192.168.120.0/22 \
--container-network-dns Container-Net_192.168.120.0:192.168.0.10 \
--container-network-firewall Container-Net_192.168.120.0:open \
--volume-store iSCSI-2/VCH00-00-vol:default \
--image-store iSCSI-2/VCH00-00-img \
--insecure-registry vicappliance00.gsslabs.org \
--insecure-registry 192.168.100.40 \
--tls-cname vch00-00 \
--tls-ca /root/CustCerts/rootCA.cer \
--tls-server-cert /root/CustCerts/certnew.cer \
--tls-server-key /root/CustCerts/new_vch00-00.key \
--thumbprint=B1:3B:26:61:B9:3B:92:1F:21:7E:75:B3:DA:02:D8:FE:FE:C3:39:81 \
--name VCH00-00
