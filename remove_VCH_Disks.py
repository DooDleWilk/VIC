#!/usr/bin/env python

from pyVmomi import vmodl, vim
from tools import cli, tasks, service_instance


def isVCH(virtual_machine):
    if "Photon - VCH" in virtual_machine.summary.config.guestFullName:
        return True
    else:
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
    parser.add_custom_argument('--fix', required=False, help='Automatically detach Hard Disk(s).')
    args = parser.get_args()
    si = service_instance.connect(args)

    VCH_List = []

    try:
        content = si.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        view_type = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        container_view = content.viewManager.CreateContainerView(
            container, view_type, recursive)

        children = container_view.view

        print("Listing VCHs with at least one Disk attached...")
        for child in children:
            if isVCH(child):
                for dev in child.config.hardware.device:
                    if isinstance(dev, vim.vm.device.VirtualDisk) and "Hard disk " in dev.deviceInfo.label:
                        VCH_List.append(child)
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
