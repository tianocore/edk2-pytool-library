# @file dsc_recipe_translator
## Translates a DSC into a recipe or a recipe into a DSC
# It will also print that DSC to a file
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
import os
from edk2toollib.uefi.edk2.build_objects.dsc import *
from edk2toollib.uefi.edk2.build_objects.recipe import recipe

class DscRecipeTranslator():
    @classmethod
    def dsc_to_recipe(cls, dsc_obj):
        ''' converts a DSC obj to a recipe obj '''
        return None

    @classmethod
    def recipe_to_dsc(cls, rec):
        ''' converts a recipe object to a DSC obj '''
        return None

    @classmethod
    def dsc_to_file(cls, dsc_obj, filepath):
        file_path = os.path.abspath(filepath)
        f = open(file_path, "w")
        lines = cls._GetDscLinesFromDscObj(dsc_obj)
        for l in lines:
            f.write(l + "\n")
        f.close()
    
    @classmethod
    def _GetDscLinesFromDscObj(cls, obj) -> list:
        ''' gets the DSC strings for an data model objects '''
        lines = []
        if type(obj) is list or type(obj) is set:
            for item in obj:
                lines += cls._GetDscLinesFromDscObj(item)
        elif type(obj) is dsc:
            lines.append("[Defines]")
            lines += cls._GetDscLinesFromDscObj(obj.defines)
            
            # Second do the Skus
            lines.append("[SkuIds]")
            for x in obj.skus:
                lines += cls._GetDscLinesFromDscObj(x)

            # Third, library classes
            for header, x in obj.library_classes.items():
                lines.append(f"[LibraryClasses{header}]")
                lines += cls._GetDscLinesFromDscObj(x)

            # Next do the components
            for header, x in obj.components.items():
                lines.append(f"[Components{header}]")
                lines += cls._GetDscLinesFromDscObj(x)

            # Then PCD's
            for header, x in obj.pcds.items():
                lines.append(f"[{header}]")
                lines += cls._GetDscLinesFromDscObj(x)

            # Then Build Options
            for header, x in obj.build_options.items():
                lines.append(f"[BuildOptions{header}]")
                lines += cls._GetDscLinesFromDscObj(x)
               

        elif type(obj) is sku_id:
            lines.append(f"{obj.id}|{obj.name}|{obj.parent}")
        elif type(obj) is library_class:
            lines.append(f"{obj.libraryclass}|{obj.inf}")
        elif type(obj) is definition:
            def_str = f"{obj.name} =\t{obj.value}"
            if obj.local:
                def_str = "DEFINE " + def_str
            lines.append(def_str)
        elif type(obj) is component:
            lines.append(f"{obj.inf}")
            #TODO: write out module override sections
        elif type(obj) is pcd:
            lines.append(f"{obj.namespace}.{obj.name}|{obj.value}")
        elif type(obj) is pcd_typed:
            if obj.max_size == 0:
                lines.append(f"{obj.namespace}.{obj.name}|{obj.value}|{obj.datum_type}")
            else:
                lines.append(f"{obj.namespace}.{obj.name}|{obj.value}|{obj.datum_type}|{obj.max_size}")
        elif type(obj) is pcd_variable:
            if obj.default is None:
                lines.append(f"{obj.namespace}.{obj.name}|{obj.var_name}|{obj.var_guid}|{obj.var_offset}")
            elif len(obj.attributes) == 0:
                lines.append(f"{obj.namespace}.{obj.name}|{obj.var_name}|{obj.var_guid}|{obj.var_offset}|{obj.default}")
            else:
                attr = ", ".join(obj.attributes)
                lines.append(f"{obj.namespace}.{obj.name}|{obj.var_name}|{obj.var_guid}|{obj.var_offset}|{obj.default}|{attr}")

        elif type(obj) is build_option:
            rep = "" if obj.family is None else f"{obj.family}:"
            rep += "_".join((obj.target, obj.tagname, obj.arch, obj.tool_code, obj.attribute))
            rep += f"= {obj.data}"
            lines.append(rep)
        return lines
        
