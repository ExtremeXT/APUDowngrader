import platform
import sys
import py_sip_xnu
import subprocess
import plistlib
import os

# Thanks to OCLP for some of the code
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/resources/sys_patch/sys_patch.py

# Error code 1 = unsupported OS
# Error code 2 = insufficient SIP value
# Error code 3 = Failed to rebuild KC
# Error code 4 = Failed to create snapshot

if os.path.exists("AMDRadeonX5000HWLibs.kext") and os.path.exists("AMDRadeonX6000Framebuffer.kext"):
    X50000HWLibsPath = "AMDRadeonX5000HWLibs.kext"
    X6000FramebufferPath = "AMDRadeonX6000Framebuffer.kext"
    
mac_version = platform.mac_ver()[0].split('.')[0]
if mac_version < 12:
    print(f"macOS version {mac_version} is not supported!")
    sys.exit(1)
elif mac_version == 12:
    print(f"macOS Monterey detected! Proceeding...")
elif mac_version == 13:
    print("macOS Ventura is unsupported as of now.")
    sys.exit(1)
else:
    print(f"Unknown macOS version ({mac_version}) detected!")
    sys.exit(1)

# Checking SIP status
if not (py_sip_xnu.SipXnu().get_sip_status().can_edit_root and py_sip_xnu.SipXnu().get_sip_status().can_load_arbitrary_kexts):
    print("Your SIP value is not sufficiently disabled! It needs to be at least 0x803.")
    print("That means csr-active-config has to be set to at least 03080000.")
    print("If this has already been done, you might also need to reset NVRAM.")
    sys.exit(2)

choice = input("The script is ready to start. Press Y if you're sure you want to proceed.")
if choice != "Y":
    sys.exit(0)

# Get the root volume
root_partition_info = plistlib.loads(subprocess.run("diskutil info -plist /".split(), stdout=subprocess.PIPE).stdout.decode().strip().encode())
root_mount_path = root_partition_info["DeviceIdentifier"]
root_mount_path = root_mount_path[:-2] if root_mount_path.count("s") > 1 else root_mount_path

# Mount the root volume
subprocess.call(f'/sbin/mount_apfs -R /dev/{root_mount_path} /System/Volumes/Update/mnt1')

# rm -rf X5000HWLibs & X6000FB
subprocess.run("sudo rm -rf /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX5000HWServices.kext/Contents/PlugIns/AMDRadeonX5000HWLibs.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run("sudo rm -rf /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX6000Framebuffer.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# cp -R X5000HWLibs & X6000FB
subprocess.run(f"sudo cp -R {X50000HWLibsPath} /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX5000HWServices.kext/Contents/PlugIns/AMDRadeonX5000HWLibs.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"sudo cp -R {X6000FramebufferPath} /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX6000Framebuffer.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Fix permissions
subprocess.run(f"chmod -Rf 755 /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX5000HWServices.kext/Contents/PlugIns/AMDRadeonX5000HWLibs.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"chown -Rf root:wheel /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX5000HWServices.kext/Contents/PlugIns/AMDRadeonX5000HWLibs.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

subprocess.run(f"chmod -Rf 755 /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX6000Framebuffer.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"chown -Rf root:wheel /System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX6000Framebuffer.kext", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# Rebuild KC
result = subprocess.run(f"sudo kmutil install --volume-root /System/Volumes/Update/mnt1", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# kmutil notes:
# - will return 71 on failure to build KCs
# - will return 31 on 'No binaries or codeless kexts were provided'
# - will return -10 if the volume is missing (ie. unmounted by another process)
if result.returncode != 0:
    print("Failed to rebuild KC!")
    print(f"Error code: {result.returncode}")
    print(result.stdout.decode())
    print("")
    sys.exit(3)

# Create system volume snapshot
result = subprocess.run(f"sudo bless --folder /System/Volumes/Update/mnt1/System/Library/CoreServices --bootefi --create-snapshot", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if result.returncode != 0:
    print("Failed to create system volume snapshot!!")
    print(f"Error code: {result.returncode}")
    print(result.stdout.decode())
    print("")
    sys.exit(4)

print("Successfully replaced the required kexts!")
sys.exit(0)