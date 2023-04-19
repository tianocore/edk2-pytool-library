# Windows Firmware Policy Library

This library supports creation and analysis of Windows Firmware Policy binaries
(unsigned)  

## Usage info

### To deserialize an unsigned firmware policy binary file and print its contents

1. Construct a ```FirmwarePolicy()``` using a binary file stream as a parameter
1. Inspect data members
1. Invoke the ```Print()``` method on it

### To create a firmware policy binary file

1. Device targeting information must first be read from the target device (not
   covered here).
1. Construct a Dictionary with keys 'Manufacturer', 'Product', 'SerialNumber',
   'OEM_01', 'OEM_02', & 'Nonce' populated with the targeting values read from
   the device.  
1. Construct an default ```FirmwarePolicy()``` object, then call

   ```SetDeviceTarget(target_dictionary)```

   to populate it with the targeting information
1. Bitwise OR the desired ```FirmwarePolicy.FW_POLICY_VALUE_foo``` values into
   an integer and pass to ```SetDevicePolicy(64_bit_device_policy)```
1. The FirmwarePolicy object is now ready, serialize it to a file stream using

   ```SerializeToStream(your_file_stream)```

1. For consumption by a secure device, sign the policy using instructions found
   elsewhere

## How to Use

```python
from edk2toollib.windows.policy.firmware_policy import FirmwarePolicy

# to create an object from file and print its contents
policy = FirmwarePolicy(fs=policy_file_stream) # construct from file stream
policy.Print()


# or to create a policy and save to file
policy = FirmwarePolicy()

deviceTarget = {
   'Manufacturer': manufacturer_read_from_device,
   'Product': product_make_read_from_device,
   'SerialNumber': sn_read_from_device,
   'OEM_01': '',  # Yours to define, or not use (NULL string)
   'OEM_02': '',
   'Nonce': nonce_read_from_device
   }
policy.SetDeviceTarget(TargetInfo)

devicePolicy = \
    FirmwarePolicy.FW_POLICY_VALUE_ACTION_SECUREBOOT_CLEAR \
    + FirmwarePolicy.FW_POLICY_VALUE_ACTION_TPM_CLEAR
policy.SetDevicePolicy(devicePolicy)

policy.SerializeToStream(stream=your_file_stream)
```
