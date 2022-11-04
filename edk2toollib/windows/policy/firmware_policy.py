# @file
#
# Library to parse/manage/build unsigned firmware policy blobs
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

# spell-checker:ignore QWORD

"""A Firmware policy management tools.

Summary:
A firmware policy is conceptually a set of key value pair "rules".
Rules can be 1-time actions, states persistent while the policy is in effect,
or targeting information describing the machine where the policy is applicable

Each key is composed of a UINT32 RootKey followed by String SubKeyName & ValueName
For example:
  RootKey = 0xEF100000
  SubKeyName = "PolicyGroupFoo"
  ValueName = "TpmClear"
  MyExampleKey = EF100000_PolicyGroupFoo_TpmClear

Each value has a type that can be primitive or a variable-length structure.

##
The firmware policy binary, pack(1), little endian, is as follows:

UINT16   FormatVersion
UINT32   PolicyVersion
GUID     PolicyPublisher
UINT16   Reserved1Count  # 0
         Reserved1[Reserved1Count]   # not present, not supported by this library
UINT32   OptionFlags     # 0
UINT16   Reserved2Count  # 0
UINT16   RulesCount
         Reserved2[Reserved2Count]   # not present for FW policies, partial support by this library
RULE     Rules[RulesCount]  # inline, not a pointer, see class Rule below
BYTE     ValueTable[]  #inline, not a pointer
##

##
A RULE structure is as follows

UINT32 RootKey
UINT32 OffsetToSubKeyName  # ValueTable offset
UINT32 OffsetToValueName   # ValueTable offset
UINT32 OffsetToValue       # ValueTable offset to a PolicyValueType + PolicyValue
##

##
Each Rule corresponds to 3 entries in the ValueTable
Rules may, however, re-use identical ValueTable entries to save space
For example, multiple Rules with the same SubKeyName may report the same SubKeyNameOffset

PolicyString SubKeyName  # may or may not be NULL terminated, usually not
PolicyString Valuename   # may or may not be NULL terminated, usually not
PolicyValue              # Begins with a UINT16 PolicyValueType, followed by the actual value, may be NULL terminated
##

##
Conventions

    _init__ constructors are to be used when creating new objects from desired values.
    When the number of parameters is small, __init__ may also take a stream parameter
    which will be deserialized to initialize the object in lieu of the other parameters.
    When the number of parameters is large, initialization from stream is factored out
    into a separate class method FromFileStream().  This overhead did not seem merited
    when the number of overall parameters was small.
##
"""

import io
import struct
import uuid
from typing import BinaryIO

STRICT = False


class Rule(object):
    """Class for managing Rule structures.

    Class for storing, serializing, deserializing, & printing RULE elements
    """
    StructFormat = '<IIII'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self, RootKey: int, SubKeyName: str, ValueName: str,
                 Value, OffsetToSubKeyName: int = 0, OffsetToValueName: int = 0,
                 OffsetToValue: int = 0) -> None:
        """Inits the Rule Object.

        Args:
            RootKey (int): The root key value
            SubKeyName (str): the subkey name
            ValueName (str): Name of the rule value
            Value (PolicyValue): The value.
            OffsetToSubKeyName (:obj:`int`, optional): Offset to read the subkey name
            OffsetToValueName (:obj:`int`, optional): Offset to read the value name
            OffsetToValue (:obj:`int`, optional): Offset to read the value
        """
        self.RootKey = RootKey
        self.OffsetToSubKeyName = OffsetToSubKeyName
        self.OffsetToValueName = OffsetToValueName
        self.OffsetToValue = OffsetToValue
        self.SubKeyName = SubKeyName
        self.ValueName = ValueName
        self.Value = PolicyValue(Value.valueType, Value.value)

    def __eq__(self, other) -> bool:
        """Rule table offsets are not considered for equivalency, only the actual key/value."""
        if (self.RootKey == other.RootKey
            and self.SubKeyName == other.SubKeyName
            and self.ValueName == other.ValueName
                and self.Value == other.Value):
            return True
        else:
            return False

    @classmethod
    def FromFsAndVtOffset(cls, fs: BinaryIO, vtOffset: int):
        """Construct a Rule initialized from a deserialized stream and vtOffset.

        Args:
            fs (BinaryIO): File stream to read from
            vtOffset (int ): offset in fs to get the ValueTable

        Raises:
            (Exception): Invalid File Stream or value table offset
        """
        if fs is None or vtOffset is None:
            raise Exception('Invalid File stream or Value Table offset')
        (RootKey, OffsetToSubKeyName,
         OffsetToValueName, OffsetToValue) = struct.unpack(
             cls.StructFormat, fs.read(cls.StructSize))

        orig_offset = fs.tell()
        SubKeyName = PolicyString.FromFileStream(fs=fs, fsOffset=vtOffset + OffsetToSubKeyName)
        ValueName = PolicyString.FromFileStream(fs=fs, fsOffset=vtOffset + OffsetToValueName)
        Value = PolicyValue.FromFileStream(fs=fs, fsOffset=vtOffset + OffsetToValue)
        fs.seek(orig_offset)
        return cls(RootKey=RootKey, OffsetToSubKeyName=OffsetToSubKeyName,
                   OffsetToValueName=OffsetToValueName, OffsetToValue=OffsetToValue,
                   SubKeyName=SubKeyName, ValueName=ValueName, Value=Value)

    @classmethod
    def FromFsAndVtBytes(cls, fs: BinaryIO, vt: bytes):
        """Contstruct a Rule initialized from a deserialized stream and value table.

        Args:
            fs (BinaryIO): File stream to read from
            vt (bytes): bytes representing a value table

        Raises:
            (Exception): Invalid File Stream or value table
        """
        if fs is None or vt is None:
            raise Exception('Invalid File stream or Value Table offset')
        (RootKey, OffsetToSubKeyName,
         OffsetToValueName, OffsetToValue) = struct.unpack(
             cls.StructFormat, fs.read(cls.StructSize))
        SubKeyName = PolicyString.FromBytes(vt, OffsetToSubKeyName)
        ValueName = PolicyString.FromBytes(vt, OffsetToValueName)
        Value = PolicyValue.FromBytes(vt, OffsetToValue)
        return cls(RootKey=RootKey, OffsetToSubKeyName=OffsetToSubKeyName,
                   OffsetToValueName=OffsetToValueName, OffsetToValue=OffsetToValue,
                   SubKeyName=SubKeyName, ValueName=ValueName, Value=Value)

    def Print(self, prefix: str = ''):
        """Prints the contents of the Rule.

        Args:
            prefix (:obj:`str`, optional): Prefix to put in front of print statement.
        """
        print('%sRule' % (prefix,))
        print('%s  RootKey:  %x' % (prefix, self.RootKey))
        print('%s  SubKeyNameOffset:  %x' % (prefix, self.OffsetToSubKeyName))
        print('%s  ValueNameOffset:  %x' % (prefix, self.OffsetToValueName))
        print('%s  ValueOffset:  %x' % (prefix, self.OffsetToValue))
        self.SubKeyName.Print(prefix=prefix + '  SubKeyName ')
        self.ValueName.Print(prefix=prefix + '  ValueName ')
        self.Value.Print(prefix=prefix + '  ')

    def Serialize(self, ruleOut: bytearray, valueOut: bytearray, offsetInVT: int):
        """Serialize Rule.

        Args:
            ruleOut (bytearray): serialized Reserved2 rule
            valueOut (bytearray): not currently used
            offsetInVT (int): not currently used
        """
        self.OffsetToSubKeyName = offsetInVT
        localArray = bytearray()
        self.SubKeyName.Serialize(valueOut=localArray)
        valueOut += localArray

        self.OffsetToValueName = self.OffsetToSubKeyName + len(localArray)
        localArray = bytearray()
        self.ValueName.Serialize(valueOut=localArray)
        valueOut += localArray

        self.OffsetToValue = self.OffsetToValueName + len(localArray)
        localArray = bytearray()
        self.Value.Serialize(valueOut=localArray)
        valueOut += localArray

        ruleOut += struct.pack(self.StructFormat, self.RootKey, self.OffsetToSubKeyName,
                               self.OffsetToValueName, self.OffsetToValue)


class PolicyValueType():
    """Class for managing PolicyValueTypes.

    Class for storing, serializing, deserializing, & printing PolicyValue Types
    """
    StructFormat = '<H'
    StructSize = struct.calcsize(StructFormat)

    POLICY_VALUE_TYPE_STRING = 0
    POLICY_VALUE_TYPE_BOOL = 1
    POLICY_VALUE_TYPE_DWORD = 2
    POLICY_VALUE_TYPE_DWORD_RANGE = 3
    POLICY_VALUE_TYPE_DWORD_CHOICE = 4
    POLICY_VALUE_TYPE_QWORD = 5
    POLICY_VALUE_TYPE_QWORD_RANGE = 6
    POLICY_VALUE_TYPE_QWORD_CHOICE = 7
    POLICY_VALUE_TYPE_OPTION = 8
    POLICY_VALUE_TYPE_MULTI_STRING = 9
    POLICY_VALUE_TYPE_BINARY = 10

    SupportedValueTypes = {POLICY_VALUE_TYPE_DWORD,
                           POLICY_VALUE_TYPE_QWORD,
                           POLICY_VALUE_TYPE_STRING}

    def __init__(self, Type):
        """Inits the PolicyValueType.

        Args:
            Type: POLICY_VALUE_TYPE_*

        Raises:
            (Exception): Unsupported ValueType

        """
        if Type not in self.SupportedValueTypes:
            ErrorMessage = ('Unsupported ValueType: %x' % Type)
            print(ErrorMessage)
            if STRICT:
                raise Exception(ErrorMessage)

        self.vt = Type

    @classmethod
    def FromFileStream(cls, fs: BinaryIO, fsOffset: int = None):
        """Load a Policy Value Type from a file stream.

        NOTE: if fsOffset is not specified, stream fs position is at beginning of struct.

        Args:
            fs (BinaryIO): filestream to read
            fsOffset (:obj:`int`, optional): offset to start reading from
        """
        if fsOffset:
            fs.seek(fsOffset)
        valueType = struct.unpack(cls.StructFormat, fs.read(cls.StructSize))[0]
        return cls(valueType)

    @classmethod
    def FromBytes(cls, b: bytes, bOffset: int = 0):
        """Inits a PolicyStringValue from a filestream.

        Args:
            b (bytes): bytes to read
            bOffset (:obj:`int`, optional): Offset to start reading from.
        """
        valueType = struct.unpack_from(cls.StructFormat, b, bOffset)[0]
        return cls(valueType)

    def Print(self, prefix: str = ''):
        """Prints the contents of the Policy String Type.

        Args:
            prefix (:obj:`str`, optional): Prefix to put in front of print statement.
        """
        print('%s%s%s' % (prefix, 'ValueType: ', self.vt))

    def Serialize(self, valueOut: bytearray):
        """Serialize the Policy String Type.

        Args:
            valueOut (bytearray): serialized object
        """
        valueOut += struct.pack(self.StructFormat, self.vt)

    def Get(self):
        """Returns the value type."""
        return self.vt


class PolicyString():
    r"""Class for managing PolicyString structures.

    Class for storing, serializing, deserializing, & printing PolicyString Types
    NOTE: This type is used both in the keys as SubKeyName and ValueName and it
        can be a value.  When used as a value, a NULL may follow the string, but
        the NULL will not be included in the string size

    16-bit, little endian, size of the string in _bytes_
    followed by a UTF-16LE string, no NULL terminator

    Example of "PlatformID"
    \x14\x00P\x00l\x00a\x00t\x00f\x00o\x00r\x00m\x00I\x00D\x00

    The trailing \x00 is not a NULL, it is UTF-16LE encoding of "D"
    """
    StringLengthFormat = '<H'
    StringLengthSize = struct.calcsize(StringLengthFormat)

    def __init__(self, String: str = None):
        """Inits PolicyStructure.

        Args:
            String (:obj:`str`, optional): String to set
        """
        if String:
            self.String = String
        else:
            self.String = ''
        return

    @classmethod
    def FromFileStream(cls, fs: BinaryIO, fsOffset: int = None):
        """Inits a PolicyString from a file stream.

        Args:
            fs (BinaryIO): File stream to read
            fsOffset (:obj:`int`, optional): Offset to start reading from.

        Raises:
            (Exception): string length mismatch
        """
        if fsOffset:
            fs.seek(fsOffset)
        StringLength = struct.unpack(cls.StringLengthFormat, fs.read(cls.StringLengthSize))[0]
        LocalString = bytes.decode(
            fs.read(StringLength), encoding='utf_16_le')
        if (len(LocalString) != (StringLength / 2)):
            raise Exception('String length mismatch')
        return cls(String=LocalString)

    @classmethod
    def FromBytes(cls, b: bytes, bOffset: int = 0):
        """Inits a PolicyString from a filestream.

        Args:
            b (bytes): bytes to read
            bOffset (:obj:`int`, optional): Offset to start reading from.

        Raises:
            (Exception): string length mismatch
        """
        StringLength = struct.unpack_from(cls.StringLengthFormat, b, bOffset)[0]
        bOffset += struct.calcsize(cls.StringLengthFormat)
        LocalString = bytes.decode(
            b[bOffset: bOffset + StringLength], encoding='utf_16_le')
        if (len(LocalString) != (StringLength / 2)):
            raise Exception('String length mismatch')
        return cls(String=LocalString)

    def Print(self, prefix: str = ''):
        """Prints the contents of the Policy String.

        Args:
            prefix (:obj:`str`, optional): Prefix to put in front of print statement.
        """
        print('%s%s%s' % (prefix, 'String:  ', self.String))

    def Serialize(self, valueOut: bytearray):
        """Serialize the Policy String.

        Args:
            valueOut (bytearray): serialized object
        """
        b = str.encode(self.String, encoding='utf_16_le')
        size = struct.pack(self.StringLengthFormat, len(b))
        valueOut += size + b


class PolicyValue():
    """Class for managing PolicyValue structures.

    Class for storing, serializing, deserializing, & printing policy values
    Typically handles primitive types itself, or delegates to other classes
    for non-primitive structures, e.g. PolicyString

    Attributes:
        valueType (PolicyValueType): Policy Value Type
        value (struct): Policy String, dword, qword
    """
    def __init__(self, valueType, value):
        """Inits a Policy Value.

        Args:
            valueType (PolicyValueType): Policy Value Type
            value (struct): Policy value string, dword, or qword
        """
        self.valueType = valueType
        self.value = value

    @classmethod
    def FromFileStream(cls, fs: BinaryIO, fsOffset: int = None):
        """Load a Policy Value from a file stream.

        NOTE: if fsOffset is not specified, stream fs position is at beginning of struct.

        Args:
            fs (BinaryIO): filestream to read
            fsOffset (:obj:`int`, optional): offset to start reading from

        Raises:
            (Exception): if STRICT is True, unsupported PolicyValueType
        """
        if fsOffset:
            fs.seek(fsOffset)
        else:
            fsOffset = fs.tell()
        valueType = PolicyValueType.FromFileStream(fs=fs, fsOffset=fsOffset)

        if valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_STRING:
            value = PolicyString.FromFileStream(fs=fs)
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_DWORD:
            value = struct.unpack('<I', fs.read(4))[0]
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_QWORD:
            value = struct.unpack('<Q', fs.read(8))[0]
        else:
            value = 'Value Type not supported'
            if STRICT:
                raise Exception(value)
        return cls(valueType=valueType, value=value)

    @classmethod
    def FromBytes(cls, b: bytes, bOffset: int = 0):
        """Load a Policy Value from bytes.

        Args:
            b (bytes): bytes to parse
            bOffset (:obj:`int`, optional): offset to start at.
        """
        valueType = PolicyValueType.FromBytes(b, bOffset)
        bOffset += PolicyValueType.StructSize

        if valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_STRING:
            value = PolicyString.FromBytes(b, bOffset)
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_DWORD:
            value = struct.unpack_from('<I', b, bOffset)[0]
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_QWORD:
            value = struct.unpack_from('<Q', b, bOffset)[0]
        else:
            value = 'Value Type not supported'
            if STRICT:
                raise Exception(value)

        return cls(valueType=valueType, value=value)

    def GetValueType(self):
        """Returns the value type."""
        return self.valueType

    def Print(self, prefix: str = ''):
        """Prints the contents of the object.

        Args:
            prefix (:obj:`str`, optional): Prefix to put in front of print statement.
        """
        self.valueType.Print(prefix=prefix)
        if isinstance(self.value, int):
            print('%s%s0x%x' % (prefix, 'Value:  ', self.value))
        elif (self.valueType.vt == PolicyValueType.POLICY_VALUE_TYPE_STRING):
            self.value.Print(prefix + 'Value: ')
        else:
            print('%s%s"%s"' % (prefix, 'Value:  ', str(self.value)))

    def Serialize(self, valueOut: bytearray):
        """Serializes the object to valueOut.

        Args:
            ValueOut (bytearray): object to write bytes to.

        Raises:
            (Exception): Value Type not supported.
        """
        self.valueType.Serialize(valueOut)

        vt = self.valueType.Get()
        if vt is PolicyValueType.POLICY_VALUE_TYPE_STRING:
            self.value.Serialize(valueOut)
            """ NOTE: add a NULL here for consistency with server-side code """
            valueOut += struct.pack('<H', 0x0000)
        elif vt is PolicyValueType.POLICY_VALUE_TYPE_DWORD:
            valueOut += struct.pack('<I', self.value)
        elif vt is PolicyValueType.POLICY_VALUE_TYPE_QWORD:
            valueOut += struct.pack('<Q', self.value)
        else:
            print('Type not supported')
            if STRICT:
                raise Exception('Value Type not supported')


class Reserved2(object):
    """Class for managing Reserved2 structures.

    For testing non-firmware, legacy policies
    Implementation can do basic parsing of rules but not values
    For test purposes only
    """
    StructFormat = '<III'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self, fs: BinaryIO = None, vtOffset: int = 0):
        """Initializes the Reserved2 structure.

        Args:
            fs (:obj:`BinaryIO`, optional): initialize with a filestream
            vtOffset (:obj:`int`, optional): used if populating from a filestream
        """
        if fs is None:
            self.ObjectType = 0
            self.Element = 0
            self.OffsetToValue = vtOffset
        else:
            self.PopulateFromFileStream(fs, vtOffset)

        errorMessage = 'Reserved2 not fully supported'
        if (STRICT is True):
            raise Exception(errorMessage)

    def PopulateFromFileStream(self, fs: BinaryIO, vtOffset: int = 0):
        """Initializes the Reserved2 structure from a filestream.

        Args:
            fs (BinaryIO): file stream to read from
            vtOffset (int): not currently used

        Raises:
            (Exception): Invalid File stream
            (Exception): if STRICT is True, cannot deserialize reserved2 values
        """
        if fs is None:
            raise Exception('Invalid File stream')
        (self.ObjectType, self.Element, self.OffsetToValue) = struct.unpack(
            self.StructFormat, fs.read(self.StructSize))

        errorMessage = 'Reserved2 PopulateFromFileStream does not deserialize Reserved2 values'
        print(errorMessage)
        if (STRICT is True):
            raise Exception(errorMessage)

    def Print(self, prefix: str = ''):
        """Prints the Reserved2 structure.

        Args:
            prefix(:obj:`str`, optional): prefix to append when printing to terminal
        """
        print('%sReserved2' % prefix)
        print('%s  ObjectType:  %x' % (prefix, self.ObjectType))
        print('%s  Element:  %x' % (prefix, self.Element))
        print('%s  ValueOffset:  %x' % (prefix, self.OffsetToValue))

    def Serialize(self, ruleOut: bytearray, valueOut: bytearray = None, offsetInVT: int = 0):
        """Serialize Reserved2 rule.

        Args:
            ruleOut (bytearray): serialized Reserved2 rule
            valueOut (bytearray): not currently used
            offsetInVT (int): not currently used

        Raises:
            (Exception): if STRICT is True, value serialization not supported
        """
        ruleOut += struct.pack(self.StructFormat, self.ObjectType, self.Element, self.OffsetToValue)
        errorMessage = 'Reserved2 value serialization not supported'
        print(errorMessage)
        if (STRICT is True):
            raise Exception(errorMessage)


class FirmwarePolicy(object):
    """Class for managing Firmware Policy structures.

    Manages storing, serializing, deserializing, & printing Firmware Policy structures

    Typically handles primitive types itself, or delegates to other classes
    for non-primitive structures, e.g. Rule, PolicyValue, PolicyString
    """
    FixedStructFormat = '<HI16sHIHH'  # omits completely unsupported Reserved1 array
    FixedStructSize = struct.calcsize(FixedStructFormat)

    POLICY_BLOB_MIN_SIZE = 32  # bytes
    POLICY_FORMAT_VERSION = 2
    POLICY_VERSION = 1
    POLICY_PUBLISHER = uuid.UUID('5AE6F808-8384-4EB9-A23A-0CCC1093E3DD')  # Do NOT change
    FW_POLICY_ROOT_KEY = 0xEF100000
    FW_POLICY_SUB_KEY_NAME_TARGET = 'Target'
    FW_POLICY_SUB_KEY_NAME = 'UEFI'
    FW_POLICY_VALUE_NAME = 'Policy'
    FW_POLICY_TYPE = PolicyValueType.POLICY_VALUE_TYPE_QWORD
    FW_POLICY_VALUE_DEFINED_MASK = 0x00000000FFFFFFFF
    FW_POLICY_VALUE_OEM_MASK = 0xFFFFFFFF00000000
    FW_POLICY_VALUE_ACTIONS_MASK = 0x0000FFFF0000FFFF
    FW_POLICY_VALUE_STATES_MASK = 0xFFFF0000FFFF0000

    """Defined Policy Actions"""
    FW_POLICY_VALUE_ACTION_SECUREBOOT_CLEAR = 0x0000000000000001
    FW_POLICY_VALUE_ACTION_TPM_CLEAR = 0x0000000000000002

    FW_POLICY_VALUE_ACTION_STRINGS = {
        FW_POLICY_VALUE_ACTION_SECUREBOOT_CLEAR: "Clear UEFI Secure Boot Keys",
        FW_POLICY_VALUE_ACTION_TPM_CLEAR: "Clear the Trusted Platform Module (TPM)"
    }

    """Defined Policy States"""
    FW_POLICY_VALUE_STATE_TBD = 0x0000000000010000

    FW_POLICY_VALUE_STATE_STRINGS = {
        FW_POLICY_VALUE_STATE_TBD: "To Be Defined Placeholder"
    }

    def __init__(self, fs: BinaryIO = None):
        """Initializes a Firmware Policy object.

        Args:
            fs (:obj:`BinaryIO`, optional): Initializes from a Filestream.
        """
        if fs is None:
            self.FormatVersion = self.POLICY_FORMAT_VERSION
            self.PolicyVersion = self.POLICY_VERSION
            self.PolicyPublisher = self.POLICY_PUBLISHER
            self.Reserved1Count = 0
            self.Reserved1 = []
            self.OptionFlags = 0
            self.Reserved2Count = 0
            self.RulesCount = 0
            self.Reserved2 = []
            self.Rules = []
            self.ValueTableSize = 0
            self.ValueTableOffset = 0
            self.ValueTable = []
            self.ValueTableFromFile = None
            self.parseValueTableViaBytes = True
        else:
            self.FromFileStream(fs)

    def AddRule(self, regRule: Rule) -> bool:
        """Adds a rule to the Firmware Policy object representation.

        WARNING: Does not update the valuetable, use Serialize to do that after all rules are added.

        Args:
            regRule (Rule): rule to add

        Returns:
            (bool): True if added, False if it already existed.
        """
        for rule in self.Rules:
            if (rule == regRule):
                return False
        self.Rules.append(regRule)
        self.RulesCount += 1
        return True

    def SetDevicePolicy(self, policy: int):
        """Adds a Rule for the 64-bit policy value bitfield.

        NOTE: The "key" is a well-known constant assigned in the body of this method

        Args:
            policy (int): the 64-bit bitfield value for associated key.
        """
        policyVT = PolicyValueType(Type=PolicyValueType.POLICY_VALUE_TYPE_QWORD)
        SubKeyName = PolicyString(String=self.FW_POLICY_SUB_KEY_NAME)
        ValueName = PolicyString(String=self.FW_POLICY_VALUE_NAME)
        Value = PolicyValue(valueType=policyVT, value=policy)
        rule = Rule(RootKey=self.FW_POLICY_ROOT_KEY,
                    SubKeyName=SubKeyName,
                    ValueName=ValueName, Value=Value)
        self.AddRule(rule)

    def SetDeviceTarget(self, target: dict):
        """Sets the device target dictionary.

        Args:
            target (dict): ValueName/Value pairs
        """
        for k, v in target.items():
            ValueName = PolicyString(String=k)
            if k == "Nonce":
                policyVT = PolicyValueType(Type=PolicyValueType.POLICY_VALUE_TYPE_QWORD)
                Value = PolicyValue(valueType=policyVT, value=v)
            else:
                policyVT = PolicyValueType(Type=PolicyValueType.POLICY_VALUE_TYPE_STRING)
                Value = PolicyValue(valueType=policyVT, value=PolicyString(String=v))
            rule = Rule(RootKey=self.FW_POLICY_ROOT_KEY,
                        SubKeyName=PolicyString(String=self.FW_POLICY_SUB_KEY_NAME_TARGET),
                        ValueName=ValueName, Value=Value)
            self.AddRule(rule)

    def SerializeToStream(self, stream: BinaryIO):
        """Serializes the Firmware Policy to a stream.

        Args:
            stream (BinaryIO): stream to write to
        """
        ba = bytearray()
        self.Serialize(output=ba)
        stream.write(ba)

    def Serialize(self, output: bytearray):
        """Serializes the Firmware Policy to a bytearray.

        Args:
            output (bytearray): bytearray to write to.
        """
        if (self.Reserved1Count > 0):
            ErrorMessage = 'Reserved1 not supported'
            if (STRICT is True):
                raise Exception(ErrorMessage)
            print(ErrorMessage)

        fixedSizeHeader = struct.pack(self.FixedStructFormat,
                                      self.FormatVersion, self.PolicyVersion, self.PolicyPublisher.bytes_le,
                                      self.Reserved1Count, self.OptionFlags,
                                      self.Reserved2Count, self.RulesCount)

        Reserved2Offset = len(fixedSizeHeader)
        Reserved2Size = self.Reserved2Count * Reserved2.StructSize
        RulesOffset = Reserved2Offset + Reserved2Size
        RulesSize = self.RulesCount * Rule.StructSize
        self.ValueTableOffset = RulesOffset + RulesSize

        offsetInVT = 0
        ruleArray = bytearray()
        valueArray = bytearray()

        for i in range(self.Reserved2Count):
            rule = bytearray()
            value = bytearray()
            self.Reserved2[i].Serialize(ruleOut=rule, valueOut=value, offsetInVT=offsetInVT)
            ruleArray += rule
            valueArray += value
            offsetInVT += len(value)

        for i in range(self.RulesCount):
            rule = bytearray()
            value = bytearray()
            self.Rules[i].Serialize(ruleOut=rule, valueOut=value, offsetInVT=offsetInVT)
            ruleArray += rule
            valueArray += value
            offsetInVT += len(value)

        serial = bytearray(fixedSizeHeader)
        serial += ruleArray

        self.ValueTableOffset = len(serial)
        self.ValueTableSize = len(valueArray)
        self.ValueTable = valueArray

        serial += valueArray
        output += serial
        self.ValueTableFromFile = False

    def FromFileStream(self, fs: BinaryIO, parseByBytes: bool = True):
        """Initializes the Firmware Policy from a FileStream.

        Args:
            fs (BinaryIO): Filestream to read from
            parseByBytes (:obj:`bool`, optional): whether to parse the value table by bytes or offset

        Raises:
            (Exception): an invalid file stream was provided.
        """
        if fs is None:
            raise Exception('Invalid File stream')

        self.parseValueTableViaBytes = parseByBytes

        begin = fs.tell()
        fs.seek(0, io.SEEK_END)
        end = fs.tell()  # end is offset after last byte
        fs.seek(begin)
        size = end - begin

        if (size < self.POLICY_BLOB_MIN_SIZE):
            raise Exception('Policy is too small')

        self.FormatVersion = struct.unpack('<H', fs.read(2))[0]
        if (self.FormatVersion > self.POLICY_FORMAT_VERSION):
            print("Policy Format Version %x is not supported" %
                  self.FormatVersion)
            raise Exception('Policy Format Version is newer than supported')

        self.PolicyVersion = struct.unpack('<I', fs.read(4))[0]
        PolicyPublisher = struct.unpack(
            '<16s', fs.read(struct.calcsize('<16s')))[0]
        self.PolicyPublisher = uuid.UUID(bytes_le=PolicyPublisher)

        self.Reserved1Count = struct.unpack('<H', fs.read(2))[0]
        if (STRICT and (self.Reserved1Count > 0)):
            raise Exception('Reserved1 not supported')
        self.Reserved1 = []
        for i in range(self.Reserved1Count):
            Reserved1 = struct.unpack(
                '<16s', fs.read(struct.calcsize('<16s')))[0]
            self.Reserved1.append(uuid.UUID(bytes_le=Reserved1))

        self.OptionFlags = struct.unpack('<I', fs.read(4))[0]

        self.Reserved2Count = struct.unpack('<H', fs.read(2))[0]
        self.RulesCount = struct.unpack('<H', fs.read(2))[0]

        # now we pause our parsing to bounds check the variable size structures
        Reserved2Offset = fs.tell()
        Reserved2Size = self.Reserved2Count * Reserved2.StructSize
        if ((Reserved2Offset + Reserved2Size) > end):
            raise Exception('Reserved2 larger than buffer')

        RulesOffset = Reserved2Offset + Reserved2Size
        RulesSize = self.RulesCount * Rule.StructSize
        if ((RulesOffset + RulesSize) > end):
            raise Exception('Rules larger than buffer')

        self.ValueTableOffset = RulesOffset + RulesSize
        self.ValueTableSize = end - self.ValueTableOffset
        saved_fs = fs.tell()
        fs.seek(self.ValueTableOffset)
        self.ValueTable = bytes(fs.read(self.ValueTableSize))
        self.ValueTableFromFile = True
        fs.seek(saved_fs)

        # resume parsing the variable length structures using table offset
        self.Reserved2 = []
        for i in range(self.Reserved2Count):
            self.Reserved2.append(
                Reserved2(fs=fs, vtOffset=self.ValueTableOffset))

        self.Rules = []
        for i in range(self.RulesCount):
            if self.parseValueTableViaBytes is True:
                RegRule = Rule.FromFsAndVtBytes(fs=fs, vt=self.ValueTable)
            else:
                RegRule = Rule.FromFsAndVtOffset(fs=fs, vtOffset=self.ValueTableOffset)
            self.Rules.append(RegRule)

    def PrintDevicePolicy(self, devicePolicy: int, prefix: str = ''):
        """Prints the device policy."""
        prefix = prefix + '    '
        for bit in self.FW_POLICY_VALUE_ACTION_STRINGS.keys():
            if (devicePolicy & bit) != 0:
                print(prefix + self.FW_POLICY_VALUE_ACTION_STRINGS[bit])

    def Print(self) -> None:
        """Prints the firmware policy structure."""
        prefix = '  '
        print('Firmware Policy')
        print('  FormatVersion:    %x' % self.FormatVersion)
        print('  PolicyVersion:    %x' % self.PolicyVersion)
        print('  PolicyPublisher:  %s' % self.PolicyPublisher)
        print('  Reserved1Count:   %x' % self.Reserved1Count)
        for item in self.Reserved1:
            print('   Reserved1:        %s' % item)
        print('  OptionFlags:  %x' % self.OptionFlags)
        print('  Reserved2Count:  %x' % self.Reserved2Count)
        print('  RulesCount:  %x' % self.RulesCount)
        print('  ValueTableSize:  %x' % self.ValueTableSize)
        print('  ValueTableOffset:  %x' % self.ValueTableOffset)
        for rule in self.Reserved2:
            rule.Print(prefix=prefix)
        for rule in self.Rules:
            rule.Print(prefix=prefix)
            if (rule.RootKey == self.FW_POLICY_ROOT_KEY
                and rule.SubKeyName.String == self.FW_POLICY_SUB_KEY_NAME
                    and rule.ValueName.String == self.FW_POLICY_VALUE_NAME):
                print(prefix + '  Device Policy:')
                self.PrintDevicePolicy(devicePolicy=rule.Value.value, prefix=prefix)
        print('  Valuetable')
        print(self.ValueTable)
        return
