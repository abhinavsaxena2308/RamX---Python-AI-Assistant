"""List all audio devices to understand the structure"""
from pycaw.pycaw import AudioUtilities

devices = AudioUtilities.GetAllDevices()
print(f"Total devices: {len(devices)}\n")

for i, device in enumerate(devices):
    print(f"Device {i}:")
    print(f"  FriendlyName: {device.FriendlyName}")
    print(f"  ID: {device.id}")
    print(f"  State: {device.state}")
    print(f"  Type: {type(device)}")
    print(f"  Has _dev: {hasattr(device, '_dev')}")
    print()
