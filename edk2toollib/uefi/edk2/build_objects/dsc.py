# @file recipe.py
# Data model for the EDK II DSC
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

# There will be some overlap between the objects for DSC's and Recipes
import logging
DEFAULT_SECTION_TYPE = "COMMON"

class dsc:
    def __init__(self, file_path):
        self.file_path = file_path  # The EDK2 path to this particular DSC
        self.skus = set()
        self.components = {}
        self.libraries = {}
        self.library_classes = {}
        self.build_options = {}
        self.pcds = {}
        self.defines = set()
    
    def __eq__(self, other):
        ''' This doesn't check for a perfect copy of everything '''
        ''' this is mainly focused on does it define the same things '''
        if type(other) is not dsc:
            return False
        if other.skus != self.skus:
            return False
        if other.components != self.components:
            return False
        if other.library_classes != self.library_classes:
            return False
        if other.build_options != self.build_options:
            return False        
        if other.pcds != self.pcds:
            return False        
        if other.defines != self.defines:
            return False
        return True

dsc_module_types = ["COMMON", "BASE", "SEC", "PEI_CORE", "PEIM", "DXE_CORE", "DXE_DRIVER",
                    "DXE_RUNTIME_DRIVER", "DXE_SAL_DRIVER", "DXE_SMM_DRIVER", "SMM_CORE", "UEFI_DRIVER", "UEFI_APPLICATION", "USER_DEFINED"]


class dsc_section_type:
    def __init__(self, arch="common", module_type="common"):
        self.arch = arch.upper()
        self.module_type = module_type.upper()
        if self.module_type not in dsc_module_types:
            raise ValueError(f"{module_type} is not a proper module type")

    def __hash__(self):
        arch = "*" if (self.arch == "COMMON" or self.arch == "DEFAULT") else self.arch
        return hash((arch, self.module_type))

    def __eq__(self, other):
        if type(other) is not dsc_section_type:
            return False
        arch = "*" if (self.arch == "COMMON" or self.arch == "DEFAULT") else self.arch
        arch2 = "*" if (other.arch == "COMMON" or other.arch == "DEFAULT") else other.arch
        return self.module_type == other.module_type or arch == arch2

    def __repr__(self):
        attributes = f".{self.arch}.{self.module_type}"
        return attributes


class dsc_buildoption_section_type(dsc_section_type):
    def __init__(self, arch="common", codebase="common", module_type="common"):
        super().__init__(arch, module_type)
        self.codebase = codebase.upper()
        if codebase not in ["COMMON", "EDK", "EDKII"]:
            raise ValueError(f"{codebase} is not a valid codebase type")

    def __hash__(self):
        return hash((super().__hash__(), self.codebase))

    def __eq__(self, other):
        if type(other) is not dsc_buildoption_section_type:
            return False
        return other.module_type == self.module_type and other.codebase == self.codebase and other.module_type == self.module_type

    def __repr__(self):
        return f"{self.arch}.{self.codebase}.{self.module_type}"


dsc_pcd_types = ["FEATUREFLAG", "PATCHABLEINMODULE", "FIXEDATBUILD", "DYNAMIC", "DYNAMICEX",
                 "DYNAMICDEFAULT", "DYNAMICHII", "DYNAMICVPD", "DYNAMICEXHII", "DYNAMICEXVPD"]


class dsc_pcd_section_type():
    def __init__(self, pcdtype, arch="common", sku="DEFAULT"):
        self.arch = arch.upper()
        self.pcd_type = pcdtype.upper()
        if self.pcd_type not in dsc_pcd_types:
            raise ValueError(f"{pcdtype} is not a proper PCD type")
        self.sku = sku.upper()

    def __hash__(self):
        return hash((self.arch, self.pcd_type))

    def __repr__(self):
        return f"Pcds{self.pcd_type}.{self.arch}.{self.sku}"

    def __eq__(self, other):
        if type(other) is not dsc_pcd_section_type:
            return False
        return self.pcd_type == other.pcd_type and self.arch == other.arch


class sku_id:
    ''' contains the data for a sku '''

    def __init__(self, id=0, name="DEFAULT", parent="DEFAULT", source_info=None):
        self.id = id
        self.name = name
        self.parent = parent  # the default parent is default
        self.source_info = source_info

    def __eq__(self, other):
        if type(other) is not sku_id:
            return False
        return self.id == other.id or self.name == other.name

    def __hash__(self):
        # we return zero because we want all the skus to hash to the same bucket
        # this won't be performant for large numbers of skus, which hopefully won't happen
        # we instead rely on __eq__ since we want to collide on two different attributes
        # since we want to make sure names and id's are unique
        return 0

    def __repr__(self):
        return f"{self.id}|{self.name}|{self.parent}"


class component:
    ''' Contains the data for a component for the EDK build system to build '''

    def __init__(self, inf, phases: list = [], source_info=None):

        self.libraries = set()  # a list of libraries that this component uses
        self.pcds = set()  # a set of PCD's that
        self.inf = inf  # the EDK2 relative path to the source INF
        self.source_info = source_info

    def __eq__(self, other):
        if (type(other) is not component):
            return False
        return self.inf == other.inf # TODO: should this be case insensitive?

    def __hash__(self):
        return hash(self.inf)

    def __repr__(self):
        source = str(self.source_info) if source_info is not None else ""
        return f"{self.inf} @ {source}"


class definition:
    ''' contains the information on a definition. '''

    def __init__(self, name, value, local=False, source_info=None):
        ''' Local means DEFINE is in front and is localized to that particular section'''
        self.name = name
        self.value = value
        self.local = local
        self.source_info = source_info

    def __repr__(self):
        string = ""
        if self.local:
            string = "DEFINE "
        string += f"{self.name} = {self.value} @ {self.source_info}"
        return string

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if (type(other) is not definition):
            return False
        return other.name == self.name

class library:
    ''' Contains the data for a specific EDK library'''
    def __init__(self, inf: str, source_info=None):
        self.inf = inf
        self.source_info = source_info
    
    def __eq__(self, other):
        if type(other) is not library:
            return False
        return self.inf == other.inf
    
    def __hash__(self):
        return hash(self.inf) #TODO how to figure out if they hash to the same spot?
    
    def __repr__(self):
        return f"{self.inf} @ {self.source_info}"

class library_class:
    ''' Contains the data for a specific EDK2 library class'''

    def __init__(self, libraryclass: str, inf: str, source_info=None):
        self.libraryclass = libraryclass
        self.inf = inf
        self.source_info = source_info

    def __eq__(self, other):
        if (type(other) is not library_class):
            return False
        if (self.libraryclass.lower() == "null"):
            return self.inf == other.inf
        return self.libraryclass.lower() == other.libraryclass.lower()

    def __hash__(self):
        # if we're a null lib, we want the hash to be based on the inf path
        if (self.libraryclass.lower() == "null"):
            return hash(self.inf)
        else:
            return hash(self.libraryclass)

    def __repr__(self):
        return f"{self.libraryclass}|{self.inf} @ {self.source_info}"


class pcd:
    ''' Contains the data for a specific pcd '''
    ''' PcdTokenSpaceGuidCName.PcdCName|Value '''

    def __init__(self, namespace, name, value, source_info=None):
        self.namespace = namespace
        self.name = name
        self.value = value
        self.source_info = source_info

    def __eq__(self, other):
        if not issubclass(other.__class__, pcd):
            return False
        return self.namespace == other.namespace and self.name == other.name

    def __hash__(self):
        return hash(f"{self.namespace}.{self.name}")

    def __repr__(self):
        return f"{self.namespace}.{self.name} = {self.value} @ {self.source_info}"


class pcd_typed(pcd):
    ''' PcdTokenSpaceGuidCName.PcdCName|Value[|DatumType[|MaximumDatumSize]] '''

    def __init__(self, namespace, name, value, datum_type, max_size=0, source_info=None):
        super().__init__(namespace, name, value, source_info)
        self.datum_type = datum_type
        self.max_size = int(max_size)

    def __repr__(self):
        return f"{self.namespace}.{self.name} = {self.value} |{self.datum_type}|{self.max_size} @ {self.source_info}"


pcd_variable_attributes = ["NV", "BS", "RT", "RO"]


class pcd_variable(pcd):
    ''' PcdTokenSpaceGuidCName.PcdCName|VariableName|VariableGuid|VariableOffset[|HiiDefaultValue[|HiiAttrubte]] '''

    def __init__(self, namespace, name, var_name, var_guid, var_offset, default=None, attributes=[], source_info=None):
        super().__init__(namespace, name, "", source_info)
        self.var_name = var_name
        self.var_guid = var_guid
        self.var_offset = var_offset
        self.default = default

        if type(attributes) is str:
            attributes = attributes.split(",")
        attributes = [str(x).upper().strip() for x in attributes]
        if any([x not in pcd_variable_attributes for x in attributes]):
            raise ValueError(f"Invalid PcdHiiAttribute values: {attributes}")
        self.attributes = attributes

    def __repr__(self):
        return f"{self.namespace}.{self.name} = {self.var_name} |{self.var_guid}|{self.var_offset}|{self.default}|{self.attributes} @ {self.source_info}"


class build_option:
    ''' Contains the data for a build option '''
    ''' EX: MSFT:*_*_*_CC_FLAGS = /D MDEPKG_NDEBUG '''
    # {FAMILY}:{TARGET}_{TAGNAME}_{ARCH}_{TOOLCODE}_{ATTRIBUTE}

    def __init__(self, tool_code, attribute, data, target="*", tagname="*", arch="*", family=None, replace=False, source_info=None):
        """
        tool_code - The tool code must be one of the defined tool codes in the Conf/tools_def.txt file. The flags defined in this section are appended to flags defined in the tools_def.txt file for individual tools.
        attribute - for example flags, dpath, path
        data - the actual flags or path you want to set
        target - DEBUG, RELEASE, or other
        tagname - the tool chain tag
        arch - ARM, AARCH64, IA32, X64, etc
        family - Conf/tools_def.txt defines FAMILY as one of MSFT, INTEL or GCC. Typically, this field is used to help the build tools determine whether the line is used for Microsoft style Makefiles or the GNU style Makefile
        replace - whether or not this replaces the default from tools_def, if this is false, we append
        """
        self.family = family
        self.target = target
        self.tagname = tagname
        self.arch = arch
        self.tool_code = tool_code
        self.attribute = attribute
        self.replace = replace
        self.data = data
        self.source_info = source_info

    def __eq__(self, other):
        if (type(other) is not build_option):
            return False
        if self.family != other.family:
            return False
        if self.target != other.target:
            return False
        if self.tagname != other.tagname:
            return False
        if self.arch != other.arch:
            return False
        if self.tool_code != other.tool_code:
            return False
        if self.attribute != other.attribute:
            return False
        return True

    def __hash__(self):
        return hash(self.__repr__(False))

    def __repr__(self, include_data=True):
        rep = "" if self.family is None else f"{self.family}:"
        rep += "_".join((self.target, self.tagname, self.arch, self.tool_code, self.attribute))
        if include_data:
            rep += f"= {self.data}"
        return rep


class source_info:
    def __init__(self, file: str, lineno: int = None):
        self.file = file
        self.lineno = lineno

    def __repr__(self):
        if self.lineno is None:
            return self.file
        return f"{self.file}:{self.lineno}"
