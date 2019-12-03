# @file recipe.py
# Data model for the build recipe (DSC + FDF + Environment)
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


class recipe:
    ''' the recipe that is handed to the build system- this is the sum of the DSC + FDF '''
    def __init__(self):
        self.components = set()  # a list of component
        self.skus = set()  # a list of skus to build
        self.output_dir = ""  # an EDK2 relative path to the output directory
        self.flash_map = None  # the map of the flash layout


class sku_id:
    ''' contains the data for a sku '''

    def __init__(self, id=0, name="DEFAULT", parent="DEFAULT"):
        self.id = id
        self.name = name
        self.parent = parent # the default parent is default

    def __eq__(self, other):
        if type(other) is not sku_id:
            return False
        print(self, other)
        return self.id == other.id or self.name == other.name

    def __hash__(self):
        # we return zero because we want all the skus to hash to the same bucket
        # this won't be performant for large numbers of skus, which hopefully won't happen
        # we instead rely on __eq__ since we want to collide on two different attributes
        return 0  

    def __repr__(self):
        return f"{self.id}|{self.name}|{self.parent}"


class component:
    ''' Contains the data for a component for the EDK build system to build '''

    def __init__(self, inf, phases: list = [], source_info=None):

        self.libraries = set()  # a list of libraries that this component uses
        # TODO: should there only be one phase allowed for a component
        self.phases = set(phases)  # a set of phases that this component is in (PEIM, DXE_RUNTIME, ...)
        self.pcds = set()  # a set of PCD's that
        self.inf = inf  # the EDK2 relative path to the source INF
        self.source_info = source_info
        build_options = {}  # map of build option to flags
        target = "NOOPT"  # the target to build this module in
        tags = []  # a list of tags defined by the various parts of the build system
        _transform_history = []

    def __eq__(self, other):
        if (type(other) is not component):
            return False
        if len(self.phases) > 0 and len(other.phases) > 0:
            if len(self.phases.intersection(other.phases)) == 0:
                return False  # if we don't overlap in phases?
        return self.inf == other.inf  # TODO: should this be case insensitive?

    def __hash__(self):
        hashes = [hash(x) for x in self.phases]
        phase_hash = sum(hashes)
        return hash(self.inf) ^ phase_hash

    def __repr__(self):
        source = str(self.source_info) if source_info is not None else ""
        phases = str(self.phases) if len(self.phases) > 0 else ""
        return f"{self.inf} {phases} {source}"


class library:
    ''' Contains the data for a specific library '''

    def __init__(self, libraryclass: str, inf: str, source_info=None):
        self.libraryclass = libraryclass
        self.inf = inf
        self.source_info = source_info

    def __eq__(self, other):
        if (type(other) is not library):
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
        return f"{self.libraryclass}|{self.inf}"


class pcd:
    ''' Contains the data for a specific pcd '''

    def __init__(self, namespace, name, value=None):
        self.namespace = namespace
        self.name = name
        self.value = value

    def __eq__(self, other):
        if (type(other) is not pcd):
            return False
        return self.namespace == other.namespace and self.name == other.name

    def __hash__(self):
        return hash(f"{self.namespace}.{self.name}")

    def __repr__(self):
        return f"{self.namespace}.{self.name} = {self.value}"


class map_object:
    ''' contains the information for a the memory layout of a flash map '''

    def __init__(self):
        self.guid = ""
        # TODO: flesh this section out once FDF is clear

    def __eq__(self, other):
        return self.guid == other.guid


class source_info:
    def __init__(self, file: str, lineno: int = None):
        self.file = file
        self.lineno = lineno

    def __repr__(self):
        if self.lineno is None:
            return self.file
        return f"{self.file}@{self.lineno}"
