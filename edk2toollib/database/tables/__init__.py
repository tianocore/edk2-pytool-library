##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A collection of table generators that run against the workspace."""
from .environment_table import EnvironmentTable  # noqa: F401
from .inf_table import InfTable  # noqa: F401
from .instanced_fv_table import InstancedFvTable  # noqa: F401
from .instanced_inf_table import InstancedInfTable  # noqa: F401
from .package_table import PackageTable  # noqa: F401
from .source_table import SourceTable  # noqa: F401
