##
# unittests for the InstancedFv table generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Unittest for the InstancedFv table generator."""
import logging
from pathlib import Path

import pytest
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import InstancedFvTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

GET_INF_LIST_QUERY = """
SELECT i.path
FROM inf AS i
JOIN junction AS j ON ? = j.key1 and j.table2 = "inf"
"""

def test_valid_fdf(empty_tree: Tree):  # noqa: F811
    """Tests that a typical fdf can be properly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedFvTable())

    comp1 = empty_tree.create_component("TestDriver1", "DXE_DRIVER")
    comp2 = empty_tree.create_component("TestDriver2", "DXE_DRIVER")
    comp3 = empty_tree.create_component("TestDriver3", "DXE_DRIVER")
    Path(empty_tree.package / "Extra Drivers").mkdir()
    Path(empty_tree.package / "Extra Drivers" / "TestDriver4.inf").touch()
    comp5 = empty_tree.create_component("TestDriver5", "DXE_DRIVER")

    dsc = empty_tree.create_dsc()

    # Write the FDF; includes a "infformat" FV used to test
    # All the different ways an INF can be defined in the FDF
    fdf = empty_tree.create_fdf(
        fv_testfv = [
            f"INF  {comp1}", # PP relative
            f'INF  {str(empty_tree.ws / comp2)}', # Absolute
            f'INF  RuleOverride=RESET_VECTOR {comp3}', # RuleOverride
            'INF  TestPkg/Extra Drivers/TestDriver4.inf', # Space in path
            f'INF  ruleoverride = RESET_VECTOR {comp5}', # RuleOverride lowercase & spaces'
        ]
    )
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    rows = db.connection.execute("SELECT key2 FROM junction where key1 == 'testfv'").fetchall()

    assert len(rows) == 5
    assert sorted(rows) == sorted([
        (Path(comp1).as_posix(),),
        (Path(comp2).as_posix(),),
        (Path(comp3).as_posix(),),
        ('TestPkg/Extra Drivers/TestDriver4.inf',),
        (Path(comp5).as_posix(),),
    ])

def test_missing_dsc_and_fdf(empty_tree: Tree, caplog):
    """Tests that the table generator is skipped if missing the necessary information."""
    with caplog.at_level(logging.DEBUG):
        edk2path = Edk2Path(str(empty_tree.ws), [])
        db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
        db.register(InstancedFvTable())

        # raise exception if the Table generator is missing required information to Generate the table.
        with pytest.raises(KeyError):
            db.parse({})

        db.parse({"TARGET_ARCH": "", "TARGET": "DEBUG"})
        db.parse({"TARGET_ARCH": "", "TARGET": "DEBUG", "ACTIVE_PLATFORM": "Pkg.dsc"})

        # check that we skipped (instead of asserting) twice, once for missing ACTIVE_PLATFORM and once for the
        # missing FLASH_DEFINITION
        count = 0
        for _, _, record in caplog.record_tuples:
            if record.startswith("DSC or FDF not found"):
                count += 1
        assert count == 2

def test_non_closest_inf_path(empty_tree: Tree):
    dsc = empty_tree.create_dsc()
    fdf = empty_tree.create_fdf(
        fv_testfv = [
            "INF Common/Subfolder/Drivers/TestDriver1.inf",
        ]
    )

    # Create the Common folder, which will be a package path
    common_folder = empty_tree.ws / "Common"
    common_folder.mkdir()

    # Create a subfolder of common folder, which is also a package path
    sub_folder = common_folder / "SubFolder"
    sub_folder.mkdir()
    edk2path = Edk2Path(str(empty_tree.ws), ["Common", str(sub_folder)])

    # Make the INF we want to make sure we get the closest match of
    (sub_folder / "Drivers").mkdir()
    (sub_folder / "Drivers" / "TestDriver1.inf").touch()

    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedFvTable())
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    rows = db.connection.execute("SELECT key2 FROM junction where key1 == 'testfv'").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "Drivers/TestDriver1.inf"
