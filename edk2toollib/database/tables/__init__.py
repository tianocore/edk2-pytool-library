##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A collection of table generators that run against the workspace."""

from edk2toollib.database.edk2_db import TableGenerator  # noqa: F401
from edk2toollib.database.tables.environment_table import EnvironmentTable  # noqa: F401
from edk2toollib.database.tables.inf_table import InfTable  # noqa: F401
from edk2toollib.database.tables.instanced_fv_table import InstancedFvTable  # noqa: F401
from edk2toollib.database.tables.instanced_inf_table import InstancedInfTable  # noqa: F401
from edk2toollib.database.tables.package_table import PackageTable  # noqa: F401
from edk2toollib.database.tables.source_table import SourceTable  # noqa: F401
