# NootedRed on Monterey

Using NRed on macOS Monterey requires a downgrade of 2 kexts: AMDRadeonX5000HWLibs and AMDRadeonX6000Framebuffer, because Apple removed the logic for our APUs from the Monterey+ versions. This script automates the whole process of downgrading. 

## Prerequisites

To use this script, you need to partially disable SIP: csr-active-config -> 03080000 or higher, and Apple Secure Boot: SecureBootModel -> Disabled.
This will weaken macOS' security by a little bit. It will enable installing unsigned kext extensions and modifying the file system of macOS.
You will also not be able to download any delta OTA updates, so when you want to update macOS, you will need to download the full 12GB update.
It is up to each person to decide if this compromise is worth it.

# Credits

Apple for macOS
Visual and NyanCatTW1 for NootedRed
Dortania for OpenCore Legacy Patcher
