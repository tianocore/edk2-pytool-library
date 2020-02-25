# @file
#
# Library to parse/manage/build unsigned firmware policy blobs
#
# Copyright (c), Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
# A firmware policy is conceptually a set of key value pair "rules".
# Rules can be 1-time actions, states persistent while the policy is in effect,
# or targeting information describing the machine where the policy is applicable
#
# Each key is composed of a UINT32 RootKey followed by String SubKeyName & ValueName
# For example:
#   RootKey = 0xEF100000
#   SubKeyName = "PolicyGroupFoo"
#   ValueName = "TpmClear"
#   MyExampleKey = EF100000\PolicyGroupFoo\TpmClear
#
# Each value has a type that can be primitive or a variable-length structure.
#
##
# The policy binary, pack(1), little endian
##
# UINT16   FormatVersion
# UINT32   PolicyVersion
# GUID     PolicyPublisher
# UINT16   Reserved1Count  # 0
#          Reserved1[Reserved1Count]   # not present
# UINT32   OptionFlags     # 0
# UINT16   Reserved2Count  # 0
# UINT16   RulesCount
#          Reserved2[Reserved2Count]   # not present
# RULE     Rules[RulesCount]  # inline, not a pointer, see class Rule below
# BYTE     ValueTable[]  #inline, not a pointer
#
##
# The RULE structure is as follows
##
# UINT32 RootKey
# UINT32 OffsetToSubKeyName  # ValueTable offset
# UINT32 OffsetToValueName   # ValueTable offset
# UINT32 OffsetToValue       # ValueTable offset to a PolicyValueType + PolicyValue
#
##
# Each Rule corresponds to 3 entries in the ValueTable
# Rules may, however, re-use identical ValueTable entries to save space
# For example, multiple Rules with the same SubKeyName may report the same SubKeyNameOffset
##
# PolicyString SubKeyName  # may or may not be NULL terminated, usually not
# PolicyString Valuename   # may or may not be NULL terminated, usually not
# PolicyValue              # Begins with a UINT16 PolicyValueType, followed by the actual value, may be NULL terminated
#
##

import io
import struct
import uuid

STRICT = False


# Class for storing, serializing, deserializing, & printing RULE elements
class Rule(object):
    StructFormat = '<IIII'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self, RootKey, SubKeyName, ValueName, Value,
                 OffsetToSubKeyName=0, OffsetToValueName=0, OffsetToValue=0):
        self.RootKey = RootKey
        self.OffsetToSubKeyName = OffsetToSubKeyName
        self.OffsetToValueName = OffsetToValueName
        self.OffsetToValue = OffsetToValue
        self.SubKeyName = SubKeyName
        self.ValueName = ValueName
        self.Value = Value

    def __eq__(self, other):
        if (self.RootKey == other.RootKey
            # Rule table offset are not considered for equivalency
            and self.SubKeyName == other.SubKeyName
            and self.ValueName == other.ValueName
                and self.Value == other.Value):
            return True
        else:
            return False

    # Incoming fs should be pointing to Rule structure
    # vtoffset is the offset in fs to the ValueTable
    @classmethod
    def FromFileStream(cls, fs, vtoffset):
        if fs is None or vtoffset is None:
            raise Exception('Invalid File stream or Value Table offset')
        (RootKey, OffsetToSubKeyName,
         OffsetToValueName, OffsetToValue) = struct.unpack(
             cls.StructFormat, fs.read(cls.StructSize))

        orig_offset = fs.tell()
        SubKeyName = PolicyString(
            fs=fs, offset=vtoffset + OffsetToSubKeyName)
        ValueName = PolicyString(
            fs=fs, offset=vtoffset + OffsetToValueName)
        Value = PolicyValue.FromFileStream(fs=fs, offset=vtoffset + OffsetToValue)
        fs.seek(orig_offset)
        return cls(RootKey=RootKey, OffsetToSubKeyName=OffsetToSubKeyName,
                   OffsetToValueName=OffsetToValueName, OffsetToValue=OffsetToValue,
                   SubKeyName=SubKeyName, ValueName=ValueName, Value=Value)

    def Print(self, prefix=''):
        print('%sRule' % (prefix,))
        print('%s  RootKey:  %x' % (prefix, self.RootKey))
        print('%s  SubKeyNameOffset:  %x' % (prefix, self.OffsetToSubKeyName))
        print('%s  ValueNameOffset:  %x' % (prefix, self.OffsetToValueName))
        print('%s  ValueOffset:  %x' % (prefix, self.OffsetToValue))
        self.SubKeyName.Print(prefix=prefix + '  SubKeyName ')
        self.ValueName.Print(prefix=prefix + '  ValueName ')
        self.Value.Print(prefix=prefix + '  ')

    def Serialize(self, ruleOut, valueOut, offsetInVT):
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


##
# Class for storing, serializing, deserializing, & printing PolicyValue Types
##
class PolicyValueType():
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
        if Type not in self.SupportedValueTypes:
            ErrorMessage = ('Unsupported ValueType: %x' % Type)
            print(ErrorMessage)
            if STRICT:
                raise Exception(ErrorMessage)

        self.vt = Type

    # if offset is not specified, fs is assumed pointing at the PolicyValueType struct
    @classmethod
    def FromFileStream(cls, fs, offset=None):
        if offset:
            fs.seek(offset)
        else:
            offset = fs.tell()
        valueType = struct.unpack('<H', fs.read(2))[0]
        return cls(valueType)

    def Print(self, prefix=''):
        print('%s%s%s' % (prefix, 'ValueType: ', self.vt))

    def Serialize(self, valueOut):
        valueOut += struct.pack(self.StructFormat, self.vt)

    def Get(self):
        return self.vt


##
# Class for storing, serializing, deserializing, & printing PolicyString Types
# NOTE: This type is used both in the keys as SubKeyName and ValueName and it
#       can be a value.  When used as a value, a NULL may follow the string, but
#       the NULL will not be included in the string size
##
class PolicyString():
    #
    # 16-bit, little endian, size of the string in _bytes_
    # followed by a UTF-16LE string, no NULL terminator
    #
    # Example of "PlatformID"
    # \x14\x00P\x00l\x00a\x00t\x00f\x00o\x00r\x00m\x00I\x00D\x00
    #
    # The trailing \x00 is not a NULL, it is UTF-16LE encoding of "D"

    def __init__(self, fs=None, offset=None, String=None):
        if not fs:
            if String:
                self.String = String
            else:
                self.String = ''
            return
        else:
            if offset:
                fs.seek(offset)
            StringLength = struct.unpack('<H', fs.read(2))[0]
            self.String = bytes.decode(
                fs.read(StringLength), encoding='utf_16_le')
            if (len(self.String) != (StringLength / 2)):
                raise Exception('String length mismatch')

    def Print(self, prefix=''):
        print('%s%s%s' % (prefix, 'String:  ', self.String))

    def Serialize(self, valueOut):
        b = str.encode(self.String, encoding='utf_16_le')
        size = struct.pack('<H', len(b))
        valueOut += size + b


##
# Class for storing, serializing, deserializing, & printing policy values
# Typically handles privitive types iteself, or delegates to other classes
# for non-primitive structures, e.g. PolicyString
##
class PolicyValue():
    def __init__(self, valueType, value):
        self.valueType = valueType
        self.value = value

    def __eq__(self, other):
        if (self.valueType == other.valueType and self.value == other.value):
            return True
        else:
            return False

    # if offset is not specified, fs is assumed pointing at the PolicyValue struct
    @classmethod
    def FromFileStream(cls, fs, offset=None):
        if offset:
            fs.seek(offset)
        else:
            offset = fs.tell()
        valueType = PolicyValueType.FromFileStream(fs=fs, offset=offset)

        if valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_STRING:
            value = PolicyString(fs=fs)
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_DWORD:
            value = struct.unpack('<I', fs.read(4))[0]
        elif valueType.Get() is PolicyValueType.POLICY_VALUE_TYPE_QWORD:
            value = struct.unpack('<Q', fs.read(8))[0]
        else:
            value = 'Value Type not supported'
            if STRICT:
                raise Exception(value)
        return cls(valueType=valueType, value=value)

    def GetValueType(self):
        return self.valueType

    def Print(self, prefix=''):
        self.valueType.Print(prefix=prefix)
        if isinstance(self.value, int):
            print('%s%s0x%x' % (prefix, 'Value:  ', self.value))
        elif (self.valueType.vt == PolicyValueType.POLICY_VALUE_TYPE_STRING):
            self.value.Print(prefix + 'Value: ')
        else:
            print('%s%s"%s"' % (prefix, 'Value:  ', str(self.value)))

    def Serialize(self, valueOut):

        self.valueType.Serialize(valueOut)

        vt = self.valueType.Get()
        if vt is PolicyValueType.POLICY_VALUE_TYPE_STRING:
            self.value.Serialize(valueOut)
            # NOTE: add a NULL here for consistency with shipped policy code
            valueOut += struct.pack('<H', 0x0000)
        elif vt is PolicyValueType.POLICY_VALUE_TYPE_DWORD:
            valueOut += struct.pack('<I', self.value)
        elif vt is PolicyValueType.POLICY_VALUE_TYPE_QWORD:
            valueOut += struct.pack('<Q', self.value)
        else:
            self.value = 'Type not supported'
            if STRICT:
                raise Exception('Value Type not supported')


##
# Reserved2: For testing non-firmware, legacy policies
##
class Reserved2(object):
    # Not used by UEFI, partial implementation follows
    StructFormat = '<III'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self, vtoffset, fs=None):
        if fs is None:
            self.ObjectType = None
            self.Element = 0
            self.OffsetToValue = 0  # offset in value table
        else:
            self.PopulateFromFileStream(fs, vtoffset)

        errorMessage = 'Reserved2 not fully supported'
        if (STRICT is True):
            raise Exception(errorMessage)

    def PopulateFromFileStream(self, fs, vtoffset):
        if fs is None:
            raise Exception('Invalid File stream')
        (self.ObjectType, self.Element, self.OffsetToValue) = struct.unpack(
            self.StructFormat, fs.read(self.StructSize))

    def Print(self, prefix=''):
        print('%sReserved2' % prefix)
        print('%s  ObjectType:  %x' % (prefix, self.ObjectType))
        print('%s  Element:  %x' % (prefix, self.Element))
        print('%s  ValueOffset:  %x' % (prefix, self.OffsetToValue))

    def Serialize(self, ruleOut, valueOut=None, offsetInVT=0):
        ruleOut += struct.pack(self.StructFormat, self.ObjectType,
                               self.Element, self.OffsetToValue)

        # Reserved2 serialization not supported, need to build ValueTable
        if (self.ObjectType is not None):
            errorMessage = 'Reserved2 not fully supported'
            if (STRICT is True):
                raise Exception(errorMessage)
            print(errorMessage)


##
# Class for storing, serializing, deserializing, & printing Firmware Policy structures
# Typically handles privitive types iteself, or delegates to other classes
# for non-primitive structures, e.g. Rule, PolicyValue, PolicyString
##
class FirmwarePolicy(object):
    FixedStructFormat = '<HI16sHIHH'  # omits Reserved1 array
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

    # Defined Policy Actions
    FW_POLICY_VALUE_ACTION_SECUREBOOT_CLEAR = 0x0000000000000001
    FW_POLICY_VALUE_ACTION_TPM_CLEAR = 0x0000000000000002

    # Defined Policy States
    FW_POLICY_VALUE_STATE_DISABLE_SPI_LOCK = 0x0000000000010000

    def __init__(self, fs=None):
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
        else:
            self.PopulateFromFileStream(fs)

    # AddRule does not update the valuetable, use Serialize to do that
    def AddRule(self, regRule):
        # de-dupe
        for rule in self.Rules:
            if (rule == regRule):
                return False
        self.Rules.append(regRule)
        self.RulesCount += 1
        return True

    def SetDevicePolicy(self, policy):
        policyVT = PolicyValueType(Type=PolicyValueType.POLICY_VALUE_TYPE_QWORD)
        SubKeyName = PolicyString(String=self.FW_POLICY_SUB_KEY_NAME)
        ValueName = PolicyString(String=self.FW_POLICY_VALUE_NAME)
        Value = PolicyValue(valueType=policyVT, value=policy)
        rule = Rule(RootKey=self.FW_POLICY_ROOT_KEY,
                    SubKeyName=SubKeyName,
                    ValueName=ValueName, Value=Value)
        self.AddRule(rule)

    def SetDeviceTarget(self, target):
        # target should be a dictionary of ValueName/Value pairs
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

    def Serialize(self, output):
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
        output.write(serial)

    def PopulateFromFileStream(self, fs):
        if fs is None:
            raise Exception('Invalid File stream')

        begin = fs.tell()
        fs.seek(0, io.SEEK_END)
        end = fs.tell()  # end is offset after last byte
        fs.seek(begin)
        size = end - begin

        if(size < self.POLICY_BLOB_MIN_SIZE):
            raise Exception('Policy is too small')

        self.FormatVersion = struct.unpack('<H', fs.read(2))[0]
        if(self.FormatVersion > self.POLICY_FORMAT_VERSION):
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
        self.ValueTable = bytearray(fs.read(self.ValueTableSize))
        fs.seek(saved_fs)

        # resume parsing the variable length structures using table offset
        self.Reserved2 = []
        for i in range(self.Reserved2Count):
            self.Reserved2.append(
                Reserved2(fs=fs, vtoffset=self.ValueTableOffset))

        self.Rules = []
        for i in range(self.RulesCount):
            RegRule = Rule.FromFileStream(fs=fs, vtoffset=self.ValueTableOffset)
            self.Rules.append(RegRule)

        self.ValueTable = fs.read()

    def Print(self):
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
            rule.Print(prefix='  ')
        for rule in self.Rules:
            rule.Print(prefix='  ')
        print('  Valuetable')
        print(self.ValueTable)
        return
