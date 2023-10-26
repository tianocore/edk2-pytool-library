##
# unittest for the PackageTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Tests for building a package table."""

import sys

import git
import pytest
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import PackageTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux only")
def test_basic_parse(tmp_path):
    """Tests basic PackageTable functionality."""
    # Clone the repo and init a single submodule.
    repo_path = tmp_path / "mu_tiano_platforms"
    repo_path.mkdir()
    with git.Repo.clone_from("https://github.com/microsoft/mu_tiano_platforms", repo_path) as repo:
        if repo is None:
            raise Exception("Failed to clone mu_tiano_platforms")
        repo.git.submodule("update", "--init", "Features/CONFIG")

    edk2path = Edk2Path(str(repo_path), ["Platforms", "Features/CONFIG"])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(PackageTable())
    db.parse({})

    results = db.connection.cursor().execute("SELECT * FROM package").fetchall()

    to_pass = {
        ("QemuPkg", "MU_TIANO_PLATFORMS"): False,
        ("QemuSbsaPkg", "MU_TIANO_PLATFORMS"): False,
        ("QemuQ35Pkg", "MU_TIANO_PLATFORMS"): False,
        ("SetupDataPkg", "Features/CONFIG"): False,
    }
    for result in results:
        to_pass[result] = True

    # Assert that all expected items in to_pass were found and set to True
    assert all(to_pass.values())
