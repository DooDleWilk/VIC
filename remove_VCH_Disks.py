#!/usr/bin/env python

from pyVmomi import vmodl, vim
from tools import cli, tasks, service_instance


def isVCH(virtual_machine):
    if virtual_machine.summary.config.guestFullName is not None:
        if "Photon - VCH" in virtual_machine.summary.config.guestFullName:
            return True
    return False


def getHardDiskAmount(vm):
    hdd_Amount = 0
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualDisk) \
                and 'Hard disk ' in dev.deviceInfo.label:
            hdd_Amount += 1
    return hdd_Amount


def detach_disk_from_vm(vm, disk_number):
    """
    Detach first class disk from vm
    """
    hdd_label = 'Hard disk ' + str(disk_number)
    virtual_hdd_device = None
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualDisk) \
                and dev.deviceInfo.label == hdd_label:
            virtual_hdd_device = dev
    if not virtual_hdd_device:
        raise RuntimeError('Virtual {} could not '
                           'be found.'.format(virtual_hdd_device))

    virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_hdd_spec.operation = \
        vim.vm.device.VirtualDeviceSpec.Operation.remove
    virtual_hdd_spec.device = virtual_hdd_device

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [virtual_hdd_spec]
    task = vm.ReconfigVM_Task(spec=spec)
    return task


def main():

    parser = cli.Parser()
    parser.add_custom_argument('--datacenter', required=False, help='Scan only this Datacenter')
    parser.add_custom_argument('--fix', required=False, help='Automatically detach Hard Disk(s).')
    args = parser.get_args()
    si = service_instance.connect(args)

    Cluster_List = []
    VCH_List = []

    try:
        # First gathering of the inventory for Cluster list population
        content = si.RetrieveContent()

        children = content.rootFolder.childEntity
        for child in children:  # Iterate though DataCenters
            datacenter = child
            if args.datacenter is not None and datacenter.name.upper() != args.datacenter.upper():
                continue

            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in the DC
                print("Listing Clusters...")
                Cluster_List.append(cluster)

        # For each Cluster, we refresh the view of the inventory, which might have changed...
        for cluster_in_list in Cluster_List:
            content = si.RetrieveContent()

            children = content.rootFolder.childEntity
            for child in children:  # Iterate though DataCenters
                datacenter = child
                if args.datacenter is not None and datacenter.name.upper() != args.datacenter.upper():
                    continue

                clusters = datacenter.hostFolder.childEntity
                for cluster in clusters:  # Iterate through the clusters in the DC
                    if cluster == cluster_in_list:
                        print("-- Cluster:", cluster.name)
                        print("Listing VCHs with at least one Disk attached...")
                        hosts = cluster.host  # Variable to make pep8 compliance
                        for host in hosts:  # Iterate through Hosts in the Cluster
                            hostname = host.summary.config.name
                            vms = host.vm
                            for vm in vms:  # Iterate through each VM on the host
                                if isVCH(vm):
                                    for dev in vm.config.hardware.device:
                                        if isinstance(dev, vim.vm.device.VirtualDisk) and "Hard disk " in dev.deviceInfo.label:
                                            VCH_List.append(vm)
                                            break

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    for VCH in VCH_List:
        print("Processing", VCH.summary.config.name)

        # Count the amount of Hard Disk per VCH
        hdd_Amount = getHardDiskAmount(VCH)

        if args.fix and args.fix.upper() == "TRUE":
            # Detach them one by one
            for disk_Number in range(hdd_Amount, 0, -1):
                print("Removing Hard Disk", str(disk_Number))
                task = detach_disk_from_vm(VCH, disk_Number)
                tasks.wait_for_tasks(si, [task])
        else:
            print("Found", hdd_Amount, "Hard Disk(s) attached.\n")

    return 0


# Start program
if __name__ == "__main__":
    main()
