# @file dsc.py
# Data model for the EDK II DSC
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Data model for the EDK II DSC."""
# There will be some overlap between the objects for DSC files and FDF files
import collections
from typing import Any, Optional

DEFAULT_SECTION_TYPE = "COMMON"


class dsc_set(set):
    """a DSC set object."""
    def __init__(self, allowed_classes: list=None) -> 'dsc_set':
        """Initializes an empty set."""
        if allowed_classes is None:
            allowed_classes = []
        self._allowed_classes = set(allowed_classes)

    def add(self, item: Any) -> None:  # noqa: ANN401
        """Adds the item to the set.

        Raises:
            (ValueError): if the type is not allowed to be added.
        """
        if len(self._allowed_classes) > 0 and type(item) not in self._allowed_classes:
            raise ValueError(f"Cannot add {type(item)} to restricted set: {self._allowed_classes}")
        if item in self:
            super().discard(item)
            # NEXTVER: get add the old_item to item
        super().add(item)


class dsc_dict(collections.OrderedDict):
    """A dictionary that allows specific classes as headers and sections."""

    def __init__(
        self,
        allowed_key_classes: Optional[str]=None,
        allowed_value_classes: Optional[Any]=None # noqa: ANN401
    ) -> 'dsc_dict':
        """Initializes a dsc_dict."""
        if allowed_key_classes is None:
            allowed_key_classes = []
        if allowed_value_classes is None:
            allowed_value_classes = []
        self._allowed_key_classes = set(allowed_key_classes)
        self._allowed_value_classes = set(allowed_value_classes)

    def __missing__(self, key: int) -> str:
        """Describes how to handle a missing key.

        Makes a new dsc_set if allowed.

        Raises:
            (KeyError): If not allowed
        """
        if len(self._allowed_value_classes) > 0:  # if we have specified allowed value classes, make a new dsc_set
            self[key] = dsc_set(self._allowed_value_classes)
            return self[key]
        raise KeyError(key)

    def __setitem__(self, key: int, val: str) -> None:
        """Setting a key value pair in the Ordered Dictionary.

        Raises:
            (ValueError): Adding a invalid key to restricted set
            (ValueError): Adding a invalid set to a restricted dict
            (ValueError): Adding a section that already exists
        """
        if len(self._allowed_key_classes) > 0 and type(key) not in self._allowed_key_classes:
            raise ValueError(f"Cannot add {type(key)} to restricted set: {self._allowed_key_classes}")

        if len(self._allowed_value_classes) > 0:
            if isinstance(val, set) and len(val) == 0:  # if it's an empty set, convert it to a dsc_set
                val = dsc_set(allowed_classes=self._allowed_value_classes)
            if isinstance(val, dsc_set):
                if val._allowed_classes != self._allowed_value_classes:
                    raise ValueError(
                        f"Cannot add set:{val._allowed_classes} to restricted dict: {self._allowed_value_classes}")
            elif type(val) not in self._allowed_value_classes:
                raise ValueError(f"Cannot add {type(val)} to restricted dict: {self._allowed_value_classes}")
        if key in self:
            # NEXTVER merge these together?
            raise ValueError(f"Cannot add section {key} since it already exists")
        dict.__setitem__(self, key, val)


class dsc:
    """Class representing a DSC."""
    def __init__(self, file_path: Optional[str]=None) -> 'dsc':
        """Inits dsc type."""
        # The EDK2 path to this particular DSC, if is is None it means it was created from a stream and has no file
        self.file_path = file_path
        # parameters added for clarity
        self.skus = dsc_set(allowed_classes=[definition, sku_id])  # this is a set of SKUs
        self.components = dsc_dict(allowed_key_classes=[dsc_section_type, ],
                                   allowed_value_classes=[component, definition])
        self.libraries = dsc_dict(allowed_key_classes=[dsc_section_type, ],
                                  allowed_value_classes=[library, definition])
        self.library_classes = dsc_dict(allowed_key_classes=[dsc_section_type, ],
                                        allowed_value_classes=[library_class, definition])
        self.build_options = dsc_dict(allowed_key_classes=[dsc_buildoption_section_type, ],
                                      allowed_value_classes=[build_option, definition])
        self.pcds = dsc_dict(allowed_key_classes=[dsc_pcd_section_type, ],
                             allowed_value_classes=[pcd, pcd_typed, pcd_variable])
        self.defines = dsc_set(allowed_classes=[definition, ])
        self.default_stores = dsc_set(allowed_classes=[definition, default_store])

        # NEXTVER: should we populate the default information into the DSC object?
        # FOR EXAMPLE: default_stores and skus

    def __eq__(self, other: 'dsc') -> bool:
        """Enables equality comparisons (a == b).

        Warning:
            This doesn't check for a perfect copy of everything
            this is mainly focused on does it define the same things
        """
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


class dsc_section_type:
    """dsc section type.

    Attributes:
        arch (str): architecture
        module_type (str): module type
    """
    dsc_module_types = ["COMMON", "BASE", "SEC", "PEI_CORE", "PEIM", "DXE_CORE",
                        "DXE_DRIVER", "DXE_RUNTIME_DRIVER", "DXE_SAL_DRIVER",
                        "DXE_SMM_DRIVER", "SMM_CORE", "UEFI_DRIVER",
                        "UEFI_APPLICATION", "USER_DEFINED"]

    def __init__(self, arch: str="common", module_type: str="common") -> 'dsc_section_type':
        """Inits dsc section type."""
        self.arch = arch.upper().strip()
        self.module_type = module_type.upper().strip()
        if not dsc_section_type.IsValidModuleType(self.module_type):
            raise ValueError(f"{module_type} is not a proper module type for dsc section")

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        arch = "*" if (self.arch == "COMMON" or self.arch == "DEFAULT") else self.arch
        return hash((arch, self.module_type))

    def __eq__(self, other: 'dsc_section_type') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not dsc_section_type:
            return False
        arch = "*" if (self.arch == "COMMON" or self.arch == "DEFAULT") else self.arch
        arch2 = "*" if (other.arch == "COMMON" or other.arch == "DEFAULT") else other.arch
        return self.module_type == other.module_type or arch == arch2

    def __repr__(self) -> str:
        """A string representation of the object."""
        attributes = f".{self.arch}.{self.module_type}"
        return attributes

    @classmethod
    def IsValidModuleType(cls: 'dsc_section_type', name: str) -> bool:
        """If the module type is valid or not."""
        return name in cls.dsc_module_types


class dsc_buildoption_section_type(dsc_section_type):
    """Build option section type.

    Attributes:
        codebase (:obj:`str`, optional): the codebase type

    Examples:
        ```
        BuildOptions.$(arch).CodeBase.Edk2ModuleType
        BuildOptions.$(arch).CodeBase
        BuildOptions.common.CodeBase
        BuildOptions.$(arch)
        BuildOptions.common
        BuildOptions
        ```
    """
    def __init__(
        self, arch: str="common",
        codebase: str="common",
        module_type: str="common"
    ) -> 'dsc_buildoption_section_type':
        """Inits dsc build option section type."""
        super().__init__(arch, module_type)
        self.codebase = codebase.upper().strip()
        if not self.IsValidCodeBase(self.codebase):
            raise ValueError(f"{codebase} is not a valid codebase type")

    @classmethod
    def IsValidCodeBase(cls: 'dsc_buildoption_section_type', codebase: str) -> bool:
        """Determines if codebase is valid.

        Args:
            codebase: codebase

        Returns:
            (bool): True if COMMON, EDK, EDKII else false
        """
        return codebase in ["COMMON", "EDK", "EDKII"]

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash((super().__hash__(), self.codebase))

    def __eq__(self, other: 'dsc_buildoption_section_type') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not dsc_buildoption_section_type:
            return False
        if not (other.module_type == self.module_type and other.codebase == self.codebase):
            return False
        return other.module_type == self.module_type

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.arch}.{self.codebase}.{self.module_type}"


dsc_pcd_types = ["FEATUREFLAG", "PATCHABLEINMODULE", "FIXEDATBUILD", "DYNAMIC", "DYNAMICEX",
                 "DYNAMICDEFAULT", "DYNAMICHII", "DYNAMICVPD", "DYNAMICEXHII", "DYNAMICEXVPD"]


class dsc_pcd_section_type():
    """This class is uses to define the PCD section type inside a component.

    Attributes:
        pcdtype: pcd type
        arch: defaults to common
        sku: defaults to DEFAULT
        store: if none, we don't have anything done
    """
    def __init__(
        self,
        pcdtype: str,
        arch: str="common",
        sku: str="DEFAULT",
        store: Optional[str]=None
    ) -> 'dsc_pcd_section_type':
        """Inits the dsc_pcd_section object."""
        # if store is none, then we don't have anything done
        self.arch = arch.upper().strip()
        self.pcd_type = pcdtype.upper().strip()
        self.default_store = None if store is None else store.strip()
        if self.pcd_type not in dsc_pcd_types:
            raise ValueError(f"{pcdtype} is not a proper PCD type")
        if not self.pcd_type.endswith("HII") and self.default_store is not None:
            raise ValueError(f"{pcdtype} does not allow for a store to be specified")
        self.sku = sku.upper()

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash((self.arch, self.pcd_type))

    def __repr__(self) -> str:
        """A string representation of the object."""
        store = "" if self.default_store is None else f".{self.default_store}"
        return f"Pcds{self.pcd_type}.{self.arch}.{self.sku}{store}"

    def __eq__(self, other: 'dsc_pcd_section_type') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not dsc_pcd_section_type:
            return False
        return self.pcd_type == other.pcd_type and self.arch == other.arch


class dsc_pcd_component_type(dsc_pcd_section_type):
    """This class is uses to define the PCD type inside a component."""

    def __init__(self, pcdtype: str) -> 'dsc_pcd_component_type':
        """Inits the dsc_pcd_component object."""
        super().__init__(pcdtype)

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"Pcds{self.pcd_type}"

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.pcd_type)

    def __eq__(self, other: 'dsc_pcd_component_type') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not dsc_pcd_component_type:
            return False
        return self.pcd_type == other.pcd_type


class sku_id:
    """Contains the data for a sku.

    Args:
        id: sku id number
        name: name of the sku
        parent: parent
        source_info: source info
    """

    def __init__(
        self,
        id: int=0,
        name: str="DEFAULT",
        parent: str="DEFAULT",
        source_info: Optional['source_info']=None
    ) -> 'sku_id':
        """Inits the sku_id object."""
        self.id = id
        self.name = name
        self.parent = parent  # the default parent is default
        self.source_info = source_info

    def __eq__(self, other: 'sku_id') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not sku_id:
            return False
        return self.id == other.id or self.name == other.name

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        # we return zero because we want all the skus to hash to the same bucket
        # this won't be performant for large numbers of skus, which hopefully won't happen
        # we instead rely on __eq__ since we want to collide on two different attributes
        # since we want to make sure names and id's are unique
        return 0

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.id}|{self.name}|{self.parent}"


class component:
    """Contains the data for a component for the EDK build system to build."""

    def __init__(self, inf: str, source_info: Optional['source_info']=None) -> 'component':
        """Inits the component object."""
        self.library_classes = set()  # a list of libraries that this component uses
        self.pcds = {}  # a dictionary of PCD's that are keyed by dsc_pcd_component_type, they are sets
        self.defines = set()  # a set of defines
        self.build_options = set()  # a set of build options for this component
        self.inf = inf  # the EDK2 relative path to the source INF
        self.source_info = source_info

    def __eq__(self, other: 'component') -> bool:
        """Enables equality comparisons (a == b)."""
        if (type(other) is not component):
            return False
        return self.inf == other.inf  # NEXTVER: should this be case insensitive?

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.inf)

    def __repr__(self) -> str:
        """A string representation of the object."""
        source = str(self.source_info) if source_info is not None else ""
        return f"{self.inf} @ {source}"


class definition:
    """Contains the information on a definition.

    Args:
        name: definition name
        value: definition value
        local: if the value is local or not
        source_info: source info
    """

    def __init__(
        self,
        name: str,
        value: str,
        local: bool=False,
        source_info: Optional['source_info']=None
    ) -> 'definition':
        """Inits the definition object.

        NOTE: Local means DEFINE is in front and is localized to that particular section
        """
        self.name = name
        self.value = value
        self.local = local
        self.source_info = source_info

    def __repr__(self) -> str:
        """A string representation of the object."""
        string = ""
        if self.local:
            string = "DEFINE "
        string += f"{self.name} = {self.value} @ {self.source_info}"
        return string

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.name)

    def __eq__(self, other: 'definition') -> bool:
        """Enables equality comparisons (a == b)."""
        if (type(other) is not definition):
            return False
        return other.name == self.name


class library:
    """Contains the data for a specific EDK library.

    Attributes:
        inf (str): inf file
        source_info (:obj:`obj`, optional): source info
    """

    def __init__(self, inf: str, source_info: Optional['source_info']=None) -> 'library':
        """Inits the Library object."""
        self.inf = inf
        self.source_info = source_info

    def __eq__(self, other: 'library') -> bool:
        """Enables equality comparisons (a == b)."""
        if type(other) is not library:
            return False
        return self.inf == other.inf

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.inf)  # NEXTVER how to figure out if they hash to the same spot?

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.inf} @ {self.source_info}"


class library_class:
    """Contains the data for a specific EDK2 library class.

    Attributes:
        libraryclass: the EDK2 library class
        inf): the inf
        source_info: source info
    """

    def __init__(self, libraryclass: str, inf: str, source_info: Optional['source_info']=None) -> 'library_class':
        """Inits the Library class object.

        Args:
            libraryclass: the EDK2 library class
            inf: the inf
            source_info: source info
        """
        self.libraryclass = libraryclass
        self.inf = inf
        self.source_info = source_info

    def __eq__(self, other: 'library_class') -> bool:
        """Enables equality comparisons (a == b)."""
        if (type(other) is not library_class):
            return False
        # if they're both null
        if self.libraryclass.lower() == "null" and other.libraryclass.lower() == "null":
            return self.inf == other.inf
        return self.libraryclass.lower() == other.libraryclass.lower()

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        # if we're a null lib, we want the hash to be based on the inf path
        if (self.libraryclass.lower() == "null"):
            return hash(self.inf)
        else:
            return hash(self.libraryclass)

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.libraryclass}|{self.inf} @ {self.source_info}"


class pcd:
    """A PCD object.

    Attributes:
        namespace: namespace
        name: pcd name
        value: pcd value
        source_info: source info

    EXAMPLE: PcdTokenSpaceGuidCName.PcdCName|Value
    """

    def __init__(self, namespace: str, name: str, value: str, source_info: Optional['source_info']=None) -> 'pcd':
        """Inits a PCD object.

        Args:
            namespace: namespace
            name: pcd name
            value: pcd value
            source_info: source info
        """
        self.namespace = namespace
        self.name = name
        self.value = value
        self.source_info = source_info

    def __eq__(self, other: 'pcd') -> bool:
        """Enables equality comparisons (a == b)."""
        if not issubclass(other.__class__, pcd):
            return False
        return self.namespace == other.namespace and self.name == other.name

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(f"{self.namespace}.{self.name}")

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.namespace}.{self.name} = {self.value} @ {self.source_info}"


class pcd_typed(pcd):
    """A Typed PCD object.

    Attributes:
        datum_type: Data Type
        max_size: max size of the data type

    EXAMPLE: PcdTokenSpaceGuidCName.PcdCName|Value[|DatumType[|MaximumDatumSize]]
    """

    def __init__(
        self,
        namespace: str,
        name: str,
        value: str,
        datum_type: str,
        max_size: int=0,
        source_info: Optional['source_info']=None
    ) -> 'pcd_typed':
        """Inits the Typed PCD Object."""
        super().__init__(namespace, name, value, source_info)
        self.datum_type = datum_type
        self.max_size = int(max_size)

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.namespace}.{self.name} = {self.value} |{self.datum_type}|{self.max_size} @ {self.source_info}"


pcd_variable_attributes = ["NV", "BS", "RT", "RO"]


class pcd_variable(pcd):
    """A Variable PCD object.

    Attributes:
        var_name: VariableName
        var_guid: VariableGuid
        var_offset: VariableOffset
        default: default value
        attribute: Optional attributes
        source_info: source info

    EXAMPLE: PcdTokenSpaceGuidCName.PcdCName|VariableName|VariableGuid|VariableOffset[|HiiDefaultValue[|HiiAttribute]]
    """

    def __init__(
        self,
        namespace: str,
        name: str,
        var_name: str,
        var_guid: str,
        var_offset: str,
        default: Optional[str]=None,
        attributes: Optional[str]=None,
        source_info: Optional['source_info']=None
    ) -> 'pcd_variable':
        """Inits a pcd_variable object."""
        super().__init__(namespace, name, "", source_info)
        if attributes is None:
            attributes = []
        self.var_name = var_name
        self.var_guid = var_guid
        self.var_offset = var_offset
        self.default = default

        if isinstance(attributes, str):
            attributes = attributes.split(",")
        attributes = [str(x).upper().strip() for x in attributes]
        if any([x not in pcd_variable_attributes for x in attributes]):
            raise ValueError(f"Invalid PcdHiiAttribute values: {attributes}")
        self.attributes = attributes

    def __repr__(self) -> str:
        """A string representation of the object."""
        pcd_data = f"{self.var_guid}|{self.var_offset}|{self.default}|{self.attributes}"
        return f"{self.namespace}.{self.name} = {self.var_name} |{pcd_data} @ {self.source_info}"


class build_option:
    """Build option object.

    Attributes:
        tool_code: One of the defined tool codes in the Conf/tools_def.txt file.
        attribute: for example flags, d_path, path
        data: the actual flags or path you want to set
        target: DEBUG, RELEASE, or other
        tagname: the tool chain tag
        arch: ARM, AARCH64, IA32, X64, etc
        family: Conf/tools_def.txt defines FAMILY as one of MSFT, INTEL or GCC.
        replace: whether or not this replaces the default from tools_def, if this is false, we append
        source_info: source_info object.

    NOTE: Contains the data for a build option
        EX: MSFT:*_*_*_CC_FLAGS = /D MDEPKG_NDEBUG
    """
    # {FAMILY}:{TARGET}_{TAGNAME}_{ARCH}_{TOOLCODE}_{ATTRIBUTE}
    def __init__(
        self,
        tool_code: str,
        attribute: str,
        data: str,
        target: str="*",
        tagname: str="*",
        arch: str="*",
        family: Optional[str]=None,
        replace: bool=False,
        source_info: 'source_info'=None
    ) -> 'build_option':
        """Inits a build_option object.

        Args:
            tool_code: One of the defined tool codes in the Conf/tools_def.txt file.
            attribute: for example flags, d_path, path
            data: the actual flags or path you want to set
            target: DEBUG, RELEASE, or other
            tagname: the tool chain tag
            arch: ARM, AARCH64, IA32, X64, etc
            family: Conf/tools_def.txt defines FAMILY as one of MSFT, INTEL or GCC.
            replace: whether or not this replaces the default from tools_def, if this is false, we append
            source_info: source_info object.

        NOTE: attribute Attribute:
            The flags defined in this section are appended to flags defined in the tools_def.txt file
            for individual tools.

        NOTE: fam9ily Attribute:
            Typically, this field is used to help the build tools determine whether the line
            is used for Microsoft style Makefiles or the GNU style Makefile
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

    def __eq__(self, other: 'build_option') -> bool:
        """Enables equality comparisons (a == b)."""
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

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.__repr__(False))

    def __repr__(self, include_data: bool=True) -> str:
        """A string representation of the object."""
        rep = "" if self.family is None else f"{self.family}:"
        rep += "_".join((self.target, self.tagname, self.arch, self.tool_code, self.attribute))
        if include_data:
            rep += f"= {self.data}"
        return rep


class default_store:
    """Object containing information on a default store.

    Attributes:
        index: index
        value: defaults to "Standard"
        source_info: defaults to None
    """
    ''' contains the information on a default store. '''
    ''' 0 | Standard        # UEFI Standard default '''

    def __init__(self, index: int=0, value: str="Standard", source_info: Optional[str]=None) -> 'default_store':
        """Inits a default store object.

        NOTE: Local means DEFINE is in front and is localized to that particular section
        """
        self.index = int(index)
        self.value = value
        self.source_info = source_info

    def __repr__(self) -> str:
        """A string representation of the object."""
        return f"{self.index} | {self.value}"

    def __hash__(self) -> int:
        """Returns the hash of an object for hashtables."""
        return hash(self.index)

    def __eq__(self, other: 'default_store') -> bool:
        """Enables equality comparisons (a == b)."""
        if (type(other) is not default_store):
            return False
        return other.index == self.index


class source_info:
    """Object representing source file information.

    Attributes:
        file (str): filename
        lineno (:obj:`int`, optional): line number
    """
    def __init__(self, file: str, lineno: int = None) -> 'source_info':
        """Inits a source_info object."""
        self.file = file
        self.lineno = lineno

    def __repr__(self) -> str:
        """Returns a string representation of object."""
        if self.lineno is None:
            return self.file
        return f"{self.file}:{self.lineno}"
