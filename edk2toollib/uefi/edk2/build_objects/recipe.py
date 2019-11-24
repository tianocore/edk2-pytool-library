# @file recipe.py
# Data model for the build recipe (DSC + FDF + Environment)
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

class recipe:
  ''' the recipe that is handed to the build system- this is the sum of the DSC + FDF '''
  components = set()  # a list of component
  skus = set()  # a list of skus to build
  output_dir = ""  # an EDK2 relative path to the output directory
  flash_map = None  # the map of the flash layout

class component:
  ''' Contains the data for a component for the EDK build system to build '''
  def __init__(self, inf, phases:list = [], source_info = None):
    
    self.libraries = set()  # a list of libraries that this component uses
    self.phases = set(phases) # a set of phases that this component is in (PEIM, DXE_RUNTIME, ...)
    self.pcds = set()  # a set of PCD's that
    self.inf = inf  # the EDK2 relative path to the source INF
    self.source_info = source_info
    build_options = {}  # map of build option to flags
    target = "NOOPT"  # the target to build this module in
    tags = []  # a list of tags defined by the various parts of the build system
    _transform_history = []

  def __eq__(self, other):
    return self.inf == other.inf

class library:
  ''' Contains the data for a specific library '''
  def __init__(self, libraryclass:str, inf:str, source_info = None):
    self.libraryclass = libraryclass
    self.inf = inf
    self.source_info = source_info

  def __eq__(self, other):
    if (self.libraryclass.lower() == "null")
      return self.inf == other.inf
    return self.libraryclass.lower() == other.libraryclass.lower()

class pcd:
  ''' Contains the data for a specific pcd '''
  def __init__(self, namespace, name, value):
    self.namespace = ""
    self.name = ""
    self.value = None

  def __eq__(self, other):
    return self.namespace == other.namespace and self.name == other.name

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
  
  def __str__(self):
    if lineno is None:
      return self.file
    return f"{self.file}@{self.lineno}"