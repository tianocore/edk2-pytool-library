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
  def __init__(self, source:str, phases:list = []):
    
    self.libraries = set()  # a list of libraries that this component uses
    self.phases = set(phases) # a set of phases that this component is in (PEIM, DXE_RUNTIME, ...)
    self.pcds = set()  # a set of PCD's that
    self.source_inf = source  # the EDK2 relative path to the source INF
    build_options = {}  # map of build option to flags
    target = "NOOPT"  # the target to build this module in
    tags = []  # a list of tags defined by the various parts of the build system
    _transform_history = []

  def __eq__(self, other):
    return self.source_inf == other.source_inf

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