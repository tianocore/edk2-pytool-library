##
# unittest for the ComponentQuery query
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Unittest for the ComponentQuery query."""
from common import Tree, correlate_env, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.queries import ComponentQuery
from edk2toollib.database.tables import EnvironmentTable, InstancedInfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_simple_component(empty_tree: Tree):
    """Tests that components are detected."""
    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")
    lib3 = empty_tree.create_library("TestLib3", "TestNullCls")

    comp1 = empty_tree.create_component(
        "TestDriver1", "DXE_DRIVER",
        libraryclasses = ["TestCls"]
    )
    comp2 = empty_tree.create_component(
        "TestDriver2", "DXE_DRIVER",
        libraryclasses = ["TestCls"]
    )

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls|{lib1}'
        ],
        components = [
            f'{comp2}',
            f'{comp1} {{',
            '<LibraryClasses>',
            '!if $(TARGET) == "DEBUG"',
            f'TestCls|{lib2}',
            f'NULL|{lib3}',
            '!endif',
            '}',
        ]
    )

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj = edk2path)
    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }
    db.register(InstancedInfTable(env = env), EnvironmentTable(env = env))
    db.parse()
    correlate_env(db)

    # Ensure that a component query with an invalid env id returns nothing and does not crash
    result = db.search(ComponentQuery(env_id = 1))
    assert len(result) == 0

    # ensure that a component query with a valid env id returns the correct result
    result = db.search(ComponentQuery(env_id = 0))
    assert len(result) == 2

    # ensure that a component query without an env id returns the correct result
    result = db.search(ComponentQuery())
    assert len(result) == 2

    result = db.search(ComponentQuery(component = "TestDriver1"))
    assert len(result) == 1

    assert sorted(result[0]['LIBRARIES_USED']) == sorted([('TestCls','TestPkg/Library/TestLib2.inf'), ('NULL','TestPkg/Library/TestLib3.inf')])

    result = db.search(ComponentQuery(component = "NonExistantDriver"))
    assert len(result) == 0
