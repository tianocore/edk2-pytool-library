## @file
# Quick script to check that the wheel/package created is aligned on a git tag.
# Official releases should not be made from non-tagged code.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import glob
import os
import sys

p = os.path.join(os.getcwd(), "dist")
whl_files = glob.glob(os.path.join(p, "*.whl"))
if len(whl_files) != 1:
    for filename in whl_files:
        print(filename)
    raise Exception("Too many wheel files")
rfn = os.path.relpath(whl_files[0], os.getcwd())
v = rfn.split("-")[1]
if v.count(".") != 2:
    raise Exception("Version %s not in format major.minor.patch" % v)
if "dev" in v:
    raise Exception("No Dev versions allowed to be published.")
print("version: " + str(v))
sys.exit(0)
