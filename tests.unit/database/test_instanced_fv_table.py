##
# unittests for the InstancedFv table generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Unittest for the InstancedFv table generator."""
from pathlib import Path

import pytest
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import InstancedFvTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_valid_fdf(empty_tree: Tree):  # noqa: F811
    """Tests that a typical fdf can be properly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    # raise exception if the Table generator is missing required information to
    # Generate the table.
    with pytest.raises(KeyError):
        fv_table = InstancedFvTable(env = {})

    comp1 = empty_tree.create_component("TestDriver1", "DXE_DRIVER")
    comp2 = empty_tree.create_component("TestDriver2", "DXE_DRIVER")
    comp3 = empty_tree.create_component("TestDriver3", "DXE_DRIVER")
    comp4 = str(Path('TestPkg','Extra Drivers','TestDriver4.inf'))
    comp5 = empty_tree.create_component("TestDriver5", "DXE_DRIVER")

    dsc = empty_tree.create_dsc()

    # Write the FDF; includes a "infformat" FV used to test
    # All the different ways an INF can be defined in the FDF
    fdf = empty_tree.create_fdf(
        fv_infformat = [
            f"INF  {comp1}", # PP relative
            f'INF  {str(empty_tree.ws / comp2)}', # Absolute
            f'INF  RuleOverride=RESET_VECTOR {comp3}', # RuleOverride
            f'INF  {comp4}', # Space in path
            f'INF  ruleoverride = RESET_VECTOR {comp5}', # RuleOverride lowercase & spaces
        ]
    )

    fv_table = InstancedFvTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })
    # Parse the FDF
    fv_table.parse(db)

    # Ensure tests pass for expected output
    for fv in db.table("instanced_fv").all():

        # Test INF's were parsed correctly. Paths should be posix as
        # That is the EDK2 standard
        if fv['FV_NAME'] == "infformat":
            assert sorted(fv['INF_LIST']) == sorted([
                Path(comp1).as_posix(),
                Path(comp2).as_posix(),
                Path(comp3).as_posix(),
                Path(comp5).as_posix(),
                Path(comp4).as_posix(),
                ])
