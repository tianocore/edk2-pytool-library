##
# unittest for the PackageTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Tests for building a package table."""
import git
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import PackageTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_basic_parse(tmp_path):
    """Tests basic PackageTable functionality."""
    # Clone the repo and init a single submodule.
    repo_path = tmp_path / "mu_tiano_platforms"
    repo = git.Repo.clone_from("https://github.com/microsoft/mu_tiano_platforms", repo_path)
    if repo is None:
        raise Exception("Failed to clone mu_tiano_platforms")
    repo.git.submodule("update", "--init", "Features/CONFIG")

    edk2path = Edk2Path(str(repo_path), ["Platforms", "Features/CONFIG"])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(PackageTable())
    db.parse({})

    results = db.connection.cursor().execute("SELECT * FROM package").fetchall()

    to_pass = {
        ("QemuPkg", "BASE"): False,
        ("QemuSbsaPkg", "BASE"): False,
        ("QemuQ35Pkg", "BASE"): False,
        ("SetupDataPkg", "Features/CONFIG"): False,
    }
    for result in results:
        to_pass[result] = True

    # Assert that all expected items in to_pass were found and set to True
    assert all(to_pass.values())
