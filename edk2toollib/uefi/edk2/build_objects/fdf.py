class fdf():
    def __init__(self, file_path):
        self.file_path = file_path  # The EDK2 path to this particular DSC
        self.defines = set()
        self.fds = {} # should this be a set not a dictionary?
        self.fvs = {}

    def __eq__(self, other):
        if type(other) != fdf:
            return False
        if self.defines != other.defines:
            return False
        if self.fds != other.fds:
            return False
        if self.fvs != other.fvs:
            return False
        return True

class fdf_fd():
    def __init__(self):
        self.tokens = set()
        self.regions = set()
        self.defines = set()

    def __eq__(self, other):
        if type(other) != fdf_fd:
            return False
        if self.tokens != other.tokens:
            return False
        if self.regions != other.regions:
            return False
        return True

class fdf_fd_token():
    valid_token_names = ["BASEADDRESS", "SIZE", "ERASEPOLARITY", "BLOCKSIZE", "NUMBLOCKS"]
    def __init__(self, name, value, pcd_name="", source_info=None):
        self.name = name
        self.value = value
        self.pcd_name = pcd_name
        self.source_info = source_info

        if not fdf_fd_token.IsValidTokenName(self.name):
            raise ValueError(f"Invalid FD named token: {name} {source_info}")

    @classmethod
    def IsValidTokenName(cls, name):
        return name.upper() in cls.valid_token_names

    def __eq__(self, other):
        if type(other) is not fdf_fd_token:
            return False
        return other.name.upper() == self.name.upper()

    def __hash__(self):
        return hash(self.name.upper())

    def __repr__(self):
        return f"FDF_FD_TOKEN: {self.name} = {self.value} | {self.pcd_name}"

class fdf_fd_region():

    def __init__(self, offset, size, data=None, pcds=[], source_info=None):
        if type(offset) is str and offset.startswith("0X"):
            offset = int(offset[2:], 16)
        if type(size) is str and size.startswith("0X"):
            size = int(size[2:], 16)
        self.offset = offset
        self.source_info = source_info
        self.size = size
        self.data = data
        self.source_info = source_info
        self.pcds = set(pcds)

    def __eq__(self, other):
        if type(other) is not fdf_fd_region:
            return False
        return other.offset == self.offset

    def __hash__(self):
        return hash(self.offset)

class fdf_fd_region_pcd():
    ''' EX: SET gFlashDevicePkgTokenSpaceGuid.PcdEfiMemoryMapped = TRUE '''
    def __init__(self, token_space, name, value, source_info=None):
        self.source_info = source_info
        self.token_space = token_space
        self.name = name
        self.value = value

    def __eq__(self, other):
        if type(other) is not fdf_fd_region_pcd:
            return False
        # TODO: case insensitive compare?
        return other.token_space == self.token_space and self.name == other.name

    def __hash__(self):
        return hash(f"{self.token_space}.{self.name}".upper())

class fdf_fd_region_data():
    ''' Stores the data for a regions '''
    valid_region_types = ["DATA", "FV", "FILE", "INF", "CAPSULE"]

    def __init__(self, type, data, source_info=None):
        self.type = type.upper().strip()
        self.data = data
        if not fdf_fd_region_data.IsRegionType(self.type):
            raise ValueError(f"Invalid FD region type: {self.type} {source_info}")

    def __eq__(self, other):
        if type(other) != fdf_fd_region_data:
            return False
        return other.data == self.data and self.type == other.type

    @classmethod
    def IsRegionType(cls, name):
        return name.upper() in cls.valid_region_types

class fdf_fv():
    def __init__(self, source_info):
        self.source_info = source_info

class fdf_capsule():
    def __init__(self, source_info):
        self.source_info = source_info

class fdf_vtf():
    def __init__(self, source_info):
        self.source_info = source_info

class fdf_option_rom():
    def __init__(self, source_info):
        self.source_info = source_info


fdf_module_types = ["COMMON", "BASE", "SEC", "PEI_CORE", "PEIM", "DXE_CORE", "DXE_DRIVER",
                    "DXE_RUNTIME_DRIVER", "DXE_SAL_DRIVER", "DXE_SMM_DRIVER", "SMM_CORE", "UEFI_DRIVER", "UEFI_APPLICATION", "USER_DEFINED"]

class fdf_rule_section():
    ''' ARCH.MODULE_TYPE.TEMPLATE_NAME '''
    def __init__(self, arch="COMMON", module_type="COMMON", template_name=""):
        self.arch = str(arch).upper().strip()
        self.module_type = str(module_type).upper().strip()
        self.template_name = str(template_name).upper().strip()
        # Check if the module type is valid
        if self.module_type not in fdf_module_types:
            raise ValueError(f"Invalid module type {self.module_type} for rule section header")

class fdf_rule():
    def __init__(self, source_info):
        self.source_info = source_info
