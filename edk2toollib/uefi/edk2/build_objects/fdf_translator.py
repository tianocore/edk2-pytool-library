# @file fdf_recipe_translator
# Translates a Fdf into a recipe or a recipe into a Fdf
# It will also print that Fdf to a file
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
import os
import logging
from edk2toollib.uefi.edk2.build_objects.fdf import *
from edk2toollib.uefi.edk2.build_objects.dsc import definition
from edk2toollib.uefi.edk2.build_objects.recipe import recipe


class FdfTranslator():
    @classmethod
    def fdf_to_file(cls, fdf_obj, filepath):
        file_path = os.path.abspath(filepath)
        f = open(file_path, "w")
        lines = cls._GetFdfLinesFromFdfObj(fdf_obj)
        for l in lines:
            f.write(l + "\n")
        f.close()

    @classmethod
    def _GetFdfLinesFromFdfObj(cls, obj, depth=0) -> list:
        ''' gets the Fdf strings for an data model objects '''
        lines = []
        depth_pad = ''.ljust(depth)
        org_depth = depth
        depth += 2

        if type(obj) is list or type(obj) is set:
            for item in obj:
                lines += cls._GetFdfLinesFromFdfObj(item, org_depth)
        elif type(obj) is fdf:
            # DEFINES
            if len(obj.defines) > 0:
                lines.append(f"{depth_pad}[Defines]")
                lines += cls._GetFdfLinesFromFdfObj(obj.defines, depth)
            # FD
            for header, x in obj.fds.items():
                lines.append(f"{depth_pad}[Fd{header}]")
                lines += cls._GetFdfLinesFromFdfObj(x, depth)
            # FV
            for header, x in obj.fvs.items():
                lines.append(f"{depth_pad}[Fv{header}]")

        elif type(obj) is fdf_fd:
            lines += cls._GetFdfLinesFromFdfObj(obj.tokens, depth)
            lines += cls._GetFdfLinesFromFdfObj(obj.defines, depth)
            lines += cls._GetFdfLinesFromFdfObj(obj.regions, depth)

        elif type(obj) is fdf_fd_token:
            tok_str = f"{depth_pad}{obj.name} =\t{obj.value}"
            if len(obj.pcd_name) > 0:
                tok_str += f"|{obj.pcd_name}"
            lines.append(tok_str)

        elif type(obj) is fdf_fd_region:
            lines.append(f"{depth_pad}{hex(obj.offset)}|{hex(obj.size)}")
            lines += cls._GetFdfLinesFromFdfObj(obj.pcds, depth+2)
            if obj.data is not None:
                lines += cls._GetFdfLinesFromFdfObj(obj.data, depth+2)

        elif type(obj) is fdf_fd_region_pcd:
            lines.append(f"{depth_pad}SET {obj.token_space}.{obj.name} = {obj.value}")

        elif type(obj) is fdf_fd_region_data:
            lines.append(f"{depth_pad}{obj.type} = {obj.data}")

        elif type(obj) is definition:
            def_str = f"{obj.name} =\t{obj.value}"
            if obj.local:
                def_str = "DEFINE " + def_str
            lines.append(depth_pad + def_str)

        else:
            logging.warning(f"UNKNOWN OBJECT {obj}")

        return lines
