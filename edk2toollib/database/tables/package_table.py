# @file package_table.py
# A module to associate the packages in a workspace with the repositories they come from.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to generate a table containing information about a package."""
from pathlib import Path
from typing import Any

import git

from edk2toollib.database import Package, Repository, Session
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

GIT_EXTENSION = ".git"
DEC_EXTENSION = "*.dec"
class PackageTable(TableGenerator):
    """A Table Generator that associates packages with their repositories."""
    def __init__(self, *args: Any, **kwargs: Any) -> 'PackageTable':
        """Initializes the Repository Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): None

        """

    def get_repo_name(repo: git.Repo) -> str:
        """Get the name of the repository."""
        if "origin" in repo.remotes:
            return repo.remotes.origin.url.split("/")[-1].split(GIT_EXTENSION)[0].upper()
        elif len(repo.remotes) > 0:
            return repo.remotes[0].url.split("/")[-1].split(GIT_EXTENSION)[0].upper()
        return "BASE"

    def parse(self, session: Session, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Glob for packages and insert them into the table."""
        try:
            repo = git.Repo(pathobj.WorkspacePath)
        except git.InvalidGitRepositoryError:
            return

        all_packages = {(pkg.name, pkg.path): pkg for pkg in session.query(Package).all()}
        all_repos = {(repo.name, repo.path): repo for repo in session.query(Repository).all()}

        packages_to_add = []
        for file in Path(pathobj.WorkspacePath).rglob(DEC_EXTENSION):
            pkg_name = file.parent.name
            containing_repo = PackageTable.get_repo_name(repo)
            repo_path = None

            for submodule in repo.submodules:
                if submodule.abspath in str(file):
                    containing_repo = submodule.name
                    repo_path = submodule.path
                    break

            repository = all_repos.setdefault(
                (containing_repo, repo_path),
                Repository(name=containing_repo, path=repo_path)
            )

            pkg_path = file.parent.relative_to(pathobj.WorkspacePath).as_posix()
            if (pkg_name, pkg_path) not in all_packages:
                package = all_packages.setdefault(
                    (pkg_name, pkg_path),
                    Package(name=pkg_name, path=pkg_path, repository=repository)
                )
                packages_to_add.append(package)
        session.add_all(packages_to_add)
