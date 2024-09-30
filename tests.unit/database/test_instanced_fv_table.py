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
from edk2toollib.database import Edk2DB, Fv
from edk2toollib.database.tables import InstancedFvTable, InstancedInfTable
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
    db.register(*[InstancedInfTable(), InstancedFvTable()])
    other_folder = empty_tree.ws / "TestPkg" / "Extra Drivers"
    other_folder.mkdir(parents=True)

    comp1 = empty_tree.create_component("TestDriver1", "DXE_DRIVER")
    comp2 = empty_tree.create_component("TestDriver2", "DXE_DRIVER")
    comp3 = empty_tree.create_component("TestDriver3", "DXE_DRIVER")
    comp4 = empty_tree.create_component("TestDriver4", "DXE_DRIVER")
    comp4 = Path(empty_tree.ws, comp4).rename(other_folder / "TestDriver4.inf")
    comp5 = empty_tree.create_component("TestDriver5", "DXE_DRIVER")
    comp6 = empty_tree.create_component("TestDriver6", "DXE_DRIVER")
    comp7 = empty_tree.create_component("TestDriver7", "DXE_DRIVER")
    comp8 = empty_tree.create_component("TestDriver8", "DXE_DRIVER")
    comp9 = empty_tree.create_component("TestDriver9", "DXE_DRIVER")

    dsc = empty_tree.create_dsc(
        libraryclasses=[],
        components=[comp1, comp2, comp3, comp4, comp5, comp6, comp7, comp8, comp9],
    )

    # Write the FDF; includes a "infformat" FV used to test
    # All the different ways an INF can be defined in the FDF
    fdf = empty_tree.create_fdf(
        fv_testfv=[
            f"INF  {comp1}",  # PP relative
            f"INF  {str(empty_tree.ws / comp2)}",  # Absolute
            f"INF  RuleOverride=RESET_VECTOR {comp3}",  # RuleOverride
            "INF  TestPkg/Extra Drivers/TestDriver4.inf",  # Space in path
            f"INF  ruleoverride = RESET_VECTOR {comp5}",  # RuleOverride lowercase & spaces'
            f"INF USE = IA32 {comp6}",
            f'INF VERSION = "1.1.1" {comp7}',
            f'INF UI = "HELLO" {comp8}',
            f"INF FILE_GUID = 12345678-1234-1234-1234-123456789012 {comp9}",
        ]
    )
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        infs = session.query(Fv).filter_by(name="testfv").one().infs

        assert len(infs) == 9
        assert sorted([inf.path for inf in infs]) == sorted(
            [
                Path(comp1).as_posix(),
                Path(comp2).as_posix(),
                Path(comp3).as_posix(),
                "TestPkg/Extra Drivers/TestDriver4.inf",
                Path(comp5).as_posix(),
                Path(comp6).as_posix(),
                Path(comp7).as_posix(),
                Path(comp8).as_posix(),
                Path(comp9).as_posix(),
            ]
        )


def test_missing_dsc_and_fdf(empty_tree: Tree, caplog):  # noqa: F811
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


def test_non_closest_inf_path(empty_tree: Tree):  # noqa: F811
    # Create the Common folder, which will be a package path
    common_folder = empty_tree.ws / "Common"
    common_folder.mkdir()

    # Create a subfolder of common folder, which is also a package path
    sub_folder = common_folder / "SubFolder"
    sub_folder.mkdir()
    edk2path = Edk2Path(str(empty_tree.ws), ["Common", str(sub_folder)])

    # Make the INF we want to make sure we get the closest match of
    (sub_folder / "Drivers").mkdir()
    driver = empty_tree.create_component("TestDriver1", "DXE_DRIVER")
    driver = Path(empty_tree.ws, driver).rename(sub_folder / "Drivers" / "TestDriver1.inf")

    dsc = empty_tree.create_dsc(libraryclasses=[], components=[driver])
    fdf = empty_tree.create_fdf(
        fv_testfv=[
            "INF Common/SubFolder/Drivers/TestDriver1.inf",
        ]
    )

    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable(), InstancedFvTable())
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        libs = session.query(Fv).filter_by(name="testfv").one().infs
        assert len(libs) == 1

        assert libs[0].path == "Drivers/TestDriver1.inf"
