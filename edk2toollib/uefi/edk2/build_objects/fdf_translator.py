# @file fdf_recipe_translator
# Translates a Fdf into a recipe or a recipe into a Fdf
# It will also print that Fdf to a file
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
import os
import logging
from edk2toollib.uefi.edk2.build_objects.fdf import *
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
            if len(obj.defines) > 0:
                lines.append(f"{depth_pad}[Defines]")
                lines += cls._GetFdfLinesFromFdfObj(obj.defines, depth)
            for header, x in obj.fds.items():
                lines.append(f"{depth_pad}[Fd{header}]")
                lines += cls._GetFdfLinesFromFdfObj(x, depth)
            pass
            # raise RuntimeError(obj)
        else:
            logging.warning(f"UNKNOWN OBJECT {obj}")
        return lines

