##
# unittest for the LicenseQuery query
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
"""Unittest for the LicenseQuery query."""
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.queries import LicenseQuery
from edk2toollib.database.tables import SourceTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_simple_license(empty_tree: Tree):
    """Tests that missing licenses are detected."""
    f1 = empty_tree.library_folder / "File.c"
    f1.touch()

    with open(f1, 'a+') as f:
        f.writelines([
            '/**'
            '  Nothing to see here!'
            '**/'
        ])

    f2 = empty_tree.library_folder / "File2.c"
    f2.touch()

    with open(f2, 'a+') as f:
        f.writelines([
            '/**'
            '  SPDX-License-Identifier: Fake-License'
            '**/'
        ])

    f3 = empty_tree.component_folder / "File3.c"
    f3.touch()

    with open(f3, 'a+') as f:
        f.writelines([
            '/**'
            '  SPDX-License-Identifier: BSD-2-Clause-Patent'
            '**/'
        ])

    f4 = empty_tree.component_folder / "File4.c"
    f4.touch()

    with open(f4, 'a+') as f:
        f.writelines([
            '/**'
            '  Nothing to see here!'
            '**/'
        ])

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    db.register(SourceTable())
    db.parse()

    # Test with no filters
    result = db.search(LicenseQuery())
    assert len(result) == 2

    # Test with include filter
    result = db.search(LicenseQuery(include = "Library"))
    assert len(result) == 1
    assert "Library" in result[0]["PATH"]

    # Test with exclude filter
    result = db.search(LicenseQuery(exclude = "Library"))
    assert len(result) == 1
    assert "Driver" in result[0]["PATH"]
