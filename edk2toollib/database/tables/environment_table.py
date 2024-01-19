# @file environment_table.py
# A module to run a table generator that creates or appends to a table with environment information."
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to run a table generator that creates or appends to a table with environment information."""
import datetime
from typing import Any

import git

from edk2toollib.database import Environment, Session, Value
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class EnvironmentTable(TableGenerator):
    """A Workspace parser that records import environment information for a given parsing execution."""  # noqa: E501
    def __init__(self, *args: Any, **kwargs: Any) -> 'EnvironmentTable':
        """Initialize the query with the specific settings."""

    def parse(self, session: Session, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Parses the environment and adds the data to the table."""
        dtime = datetime.datetime.now()

        try:
            version = git.Repo(pathobj.WorkspacePath).head.commit.hexsha
        except git.InvalidGitRepositoryError:
            version = "UNKNOWN"

        entry = Environment(
            id=id,
            date=dtime,
            version=version,values = [Value(env_id = env, key=key, value=value) for key, value in env.items()])

        session.add(entry)
