import platform
import sys
import subprocess
import plistlib
import os
import glob

if platform.system() != "Darwin":
    print("This script is only meant to be run on macOS!")
    sys.exit()

try:
    import py_sip_xnu
except:
    print("Could not import py_sip_xnu! Installing py_sip_xnu...")
    subprocess.run("python3 -m pip install py_sip_xnu".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        import py_sip_xnu
    except:
        print("Failed to install py_sip_xnu! Please install it manually.")
        sys.exit()

# Thanks to OCLP for some of the code
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/resources/sys_patch/sys_patch.py

# TODO: Add Ventura support
mac_version = str(platform.mac_ver()[0].split('.')[0])
if mac_version < '12':
    print(f"macOS version {mac_version} is not supported!")
    sys.exit()
elif mac_version == '12':
    print("macOS Monterey detected! Proceeding...")
elif mac_version == '13':
    print("macOS Ventura is unsupported as of now.")
    sys.exit()
else:
    print(f"Unknown macOS version ({mac_version}) detected!")
    sys.exit()

SLEX5000HWLibs = "/System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX5000HWServices.kext/Contents/PlugIns/AMDRadeonX5000HWLibs.kext"
SLEX6000Framebuffer = "/System/Volumes/Update/mnt1/System/Library/Extensions/AMDRadeonX6000Framebuffer.kext"

kext_dir = sys.path[0]
X50000HWLibsPath = kext_dir + "/" + "AMDRadeonX5000HWLibs.kext"
X6000FramebufferPath = kext_dir + "/" + "AMDRadeonX6000Framebuffer.kext"

if os.path.exists(X50000HWLibsPath) and os.path.exists(X6000FramebufferPath):
    pass
else:
    print("No Kexts found in script directory! Searching subdirectories...")
    try:
        X50000HWLibsPath = kext_dir + "/" + glob.glob("**/AMDRadeonX5000HWLibs.kext")[0]
        X6000FramebufferPath = kext_dir + "/" + glob.glob("**/AMDRadeonX6000Framebuffer.kext")[0]
    except:
        print("AMDRadeonX5000HWLibs.kext and/or AMDRadeonX6000Framebuffer.kext not found in the script directory or any subdirectories!")
        print("Because of copyright limitations, these files cannot be shared publicly on the repository.")
        print("This means you need to find the means to get these files either by yourself from a Big Sur installation or downloaded from somewhere else.")
        sys.exit()

    if os.path.exists(X50000HWLibsPath) and os.path.exists(X6000FramebufferPath):
        pass
    else:
        print("AMDRadeonX5000HWLibs.kext and/or AMDRadeonX6000Framebuffer.kext not found in the script directory or any subdirectories!")
        print("Because of copyright limitations, these files cannot be shared publicly on the repository.")
        print("This means you need to find the means to get these files either by yourself from a Big Sur installation or downloaded from somewhere else.")
        sys.exit()

print(f"AMDRadeonX5000HWLibs found in: {X50000HWLibsPath}")
print(f"AMDRadeonX6000Framebuffer found in: {X6000FramebufferPath}")

# Checking Secure Boot status
if subprocess.run("nvram 94b73556-2197-4702-82a8-3e1337dafbfb:AppleSecureBootPolicy".split(), stdout=subprocess.PIPE).stdout.decode().split("%")[1].strip() == '00':
    print("Apple Secure Boot is Disabled! Proceeding...")
else:
    print("Apple Secure Boot is enabled! It has to be turned off in order to continue.")
    print("Please set SecureBootModel to Disabled.")
    sys.exit() 

# Checking SIP status
if (py_sip_xnu.SipXnu().get_sip_status().can_edit_root and py_sip_xnu.SipXnu().get_sip_status().can_load_arbitrary_kexts):
    print("Compatible SIP value detected! Proceeding...")
else:
    print("Your SIP value is too low! It needs to be at least 0x803.")
    print("That means csr-active-config has to be set to at least 03080000.")
    print("If this has already been done, you might also need to reset NVRAM.")
    sys.exit()

choice = input("The script is ready to start. Type \"I am sure that I want to downgrade my root volume\" if you're sure you want to proceed: ")
if choice == "I am sure that I want to downgrade my root volume":
    print("Proceeding with replacing kexts.")
else:
    print("Exiting...")
    sys.exit()

# Get the root volume
root_partition = plistlib.loads(subprocess.run("diskutil info -plist /".split(), stdout=subprocess.PIPE).stdout.decode().strip().encode())["DeviceIdentifier"]
if root_partition.count("s") > 1:
    root_partition = root_partition[:-2]

print(f"Root partition found: {root_partition}")

print("Please enter your password when you are asked to.")
# Mount the root volume
result = subprocess.run(f"sudo /sbin/mount_apfs -R /dev/{root_partition} /System/Volumes/Update/mnt1".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
if result.returncode != 0:
    print("Failed to mount root volume!")
    print(result.stdout.decode())
    print("")
    sys.exit()

print("Root volume successfully mounted!")

# Backing up original kexts
if not os.path.exists(f"{kext_dir}/Backups"):
    os.mkdir(f"{kext_dir}/Backups")

subprocess.run(f"sudo cp -Rf {SLEX5000HWLibs} {kext_dir}/Backups/Original_AMDRadeonX5000HWLibs.kext".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"sudo cp -Rf {SLEX5000HWLibs} {kext_dir}/Backups/Original_AMDRadeonX6000FrameBuffer.kext".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# rm -rf X5000HWLibs & X6000FB
subprocess.run(f"sudo rm -rf {SLEX5000HWLibs}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"sudo rm -rf {SLEX6000Framebuffer}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("Kexts successfully deleted!")

# cp -R X5000HWLibs & X6000FB
result1 = subprocess.run(f"sudo cp -R {X50000HWLibsPath} {SLEX5000HWLibs}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
result2 = subprocess.run(f"sudo cp -R {X6000FramebufferPath} {SLEX6000Framebuffer}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if result1.returncode != 0 or result2.returncode != 0:
    print("Failed to copy kexts!!")
    print(result1.stdout.decode())
    print("----------------")
    print(result2.stdout.decode())
    print("")   
    sys.exit()
print("Kexts successfully replaced!")

# Fix permissions
subprocess.run(f"sudo chmod -Rf 755 {X50000HWLibsPath}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"sudo chown -Rf root:wheel {X50000HWLibsPath}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

subprocess.run(f"sudo chmod -Rf 755 {X6000FramebufferPath}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
subprocess.run(f"sudo chown -Rf root:wheel {X6000FramebufferPath}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("Kext permissions successfully fixed!")

# Rebuild KC
result = subprocess.run("sudo kmutil install --volume-root /System/Volumes/Update/mnt1 --update-all --variant-suffix release".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if result.returncode != 0:
    print("Failed to rebuild KC!")
    print(result.stdout.decode())
    print("")
    sys.exit()
print("Successfully rebuilt KC!")

# Create system volume snapshot
result = subprocess.run("sudo bless --folder /System/Volumes/Update/mnt1/System/Library/CoreServices --bootefi --create-snapshot".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

if result.returncode != 0:
    print("Failed to create system volume snapshot!!")
    print(result.stdout.decode())
    print("")
    sys.exit()
print("Successfully created a new APFS volume snapshot!")

# Unmount root drive
# No big deal if this fails, it's just a cleanup step
result = subprocess.run(f"sudo /sbin/umount /System/Volumes/Update/mnt1".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

print("Successfully replaced the required kexts!")
sys.exit(0)