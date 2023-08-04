# @file path_utilities.py
# Code to help convert Edk2, absolute, and relative file paths
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
r"""A module for managing Edk2 file paths agnostic to OS path separators ("/" vs "\").

This module converts all windows style paths to Posix file paths internally, but will return
the OS specific path with the exception of of any function that returns an Edk2 style path,
which will always return Posix form.
"""
import errno
import logging
import os
from pathlib import Path
from typing import Iterable, Optional


class Edk2Path(object):
    """Represents edk2 file paths.

    Class that helps perform path operations within an EDK workspace.

    Attributes:
        WorkspacePath (str): Absolute path to the workspace root.
        PackagePathList (List[str]): List of absolute paths to a package.

    Attributes are initialized by the constructor and are read-only.

    !!! warning
        Edk2Path performs expensive packages path and package validation when
        instantiated. If using the same Workspace root and packages path, it is
        suggested that only a single Edk2Path instance is instantiated and
        passed to any consumers.

    There are two OS environment variables that modify the behavior of this class with
    respect to nested package checking:
        PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES - converts errors about nested
            packages to warnings.
        PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES - contains a comma-delimited list of
            known bad packages. If a package matching a known bad package from the
            list is encountered, an info-level message will be printed and the nested
            package check will be skipped.

    """

    def __init__(self, ws: str, package_path_list: Iterable[str],
                 error_on_invalid_pp: bool = True):
        """Constructor.

        Args:
            ws: absolute path or cwd relative path of the workspace.
            package_path_list: list of packages path. Entries can be Absolute path, workspace relative path, or CWD
                relative.
            error_on_invalid_pp: default value is True. If packages path value is invalid raise exception.

        Raises:
            (NotADirectoryError): Invalid workspace or package path directory.
        """
        self.logger = logging.getLogger("Edk2Path")

        # Other code is dependent the following types, so keep it that way:
        #   - self.PackagePathList: List[str]
        #   - self.WorkspacePath: str
        ws = ws.replace("\\", "/")
        workspace_candidate_path = Path(ws)

        if not workspace_candidate_path.is_absolute():
            workspace_candidate_path = Path.cwd() / ws

        if not workspace_candidate_path.is_dir():
            raise NotADirectoryError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                workspace_candidate_path.resolve())

        self._workspace_path = workspace_candidate_path

        candidate_package_path_list = []
        for a in [Path(path.replace("\\", "/")) for path in package_path_list]:
            if a.is_absolute():
                candidate_package_path_list.append(a)
            else:
                wsr = self._workspace_path / a
                if wsr.is_dir():
                    candidate_package_path_list.append(wsr)
                else:
                    # assume current working dir relative.  Will catch invalid dir when checking whole list
                    candidate_package_path_list.append(Path.cwd() / a)

        invalid_pp = []
        for a in candidate_package_path_list[:]:
            if not a.is_dir():
                self.logger.log(logging.ERROR if error_on_invalid_pp else
                                logging.WARNING,
                                f"Invalid package path entry {a.resolve()}")
                candidate_package_path_list.remove(a)
                invalid_pp.append(str(a.resolve()))

        self._package_path_list = candidate_package_path_list

        if invalid_pp and error_on_invalid_pp:
            raise NotADirectoryError(errno.ENOENT, os.strerror(errno.ENOENT), invalid_pp)

        #
        # Nested package check - ensure packages do not exist in a linear
        # path hierarchy.
        #
        # 1. Build a dictionary for each package path.
        #      - Key = Package path
        #      - Value = List of packages discovered in package path
        # 2. Enumerate all keys in dictionary checking if any package
        #    is relative (nested) to each other.
        # 3. Raise an Exception if two packages are found to be nested.
        #
        package_path_packages = {}
        for package_path in self._package_path_list:
            package_path_packages[package_path] = \
                [p.parent for p in package_path.glob('**/*.dec')]

        # Note: The ability to ignore this function raising an exception on
        #       nested packages is temporary. Do not plan on this variable
        #       being available long-term and try to resolve the nested
        #       packages problem right away.
        #
        # Removal is tracked in the following GitHub issue:
        # https://github.com/tianocore/edk2-pytool-library/issues/200
        ignore_nested_packages = False
        if "PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES" in os.environ and \
            os.environ["PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES"].strip().lower() == \
                "true":
            ignore_nested_packages = True

        if "PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES" in os.environ:
            pkgs_to_ignore = os.environ["PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES"].split(",")
        else:
            pkgs_to_ignore = []

        for package_path, packages in package_path_packages.items():
            packages_to_check = []
            for package in packages:
                if any(x in str(package) for x in pkgs_to_ignore):
                    self.logger.log(
                        logging.INFO,
                        f"Ignoring nested package check for known-bad package "
                        f"[{str(package)}].")
                else:
                    packages_to_check.append(package)
            for i, package in enumerate(packages_to_check):
                for j in range(i + 1, len(packages_to_check)):
                    comp_package = packages_to_check[j]
                    if (package.is_relative_to(comp_package)
                            or comp_package.is_relative_to(package)):
                        if ignore_nested_packages:
                            self.logger.log(
                                logging.WARNING,
                                f"Nested packages not allowed. The packages "
                                f"[{str(package)}] and [{str(comp_package)}] are "
                                f"nested.")
                            self.logger.log(
                                logging.WARNING,
                                "Note 1: Nested packages are being ignored right now because the "
                                "\"PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES\" environment variable "
                                "is set. Do not depend on this variable long-term.")
                            self.logger.log(
                                logging.WARNING,
                                "Note 2: Some pytool features may not work as expected with nested packages.")
                        else:
                            raise Exception(
                                f"Nested packages not allowed. The packages "
                                f"[{str(package)}] and [{str(comp_package)}] are "
                                f"nested. Set the \"PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES\" "
                                f"environment variable to \"true\" as a temporary workaround "
                                f"until you fix the packages so they are no longer nested.")

    @property
    def WorkspacePath(self):
        """Workspace Path as a string."""
        return str(self._workspace_path)

    @property
    def PackagePathList(self):
        """List of package paths as strings."""
        return [str(p) for p in self._package_path_list]

    def GetEdk2RelativePathFromAbsolutePath(self, *abspath: str) -> str:
        """Transforms an absolute path to an edk2 path relative to the workspace or a packages path.

        Args:
            *abspath: absolute path to a file or directory. Can be the entire path or parts of the path provided
                separately. Supports both Windows and Posix style paths

        Returns:
            (str): POSIX-like path relative to the workspace or packages path
            (None): abspath is None
            (None): path is not valid

        Example:
            ```python
                rel_path = edk2path.GetEdk2RelativePathFromAbsolutePath("C:/Workspace/edk2/MdePkg/Include")
                rel_path = edk2path.GetEdk2RelativePathFromAbsolutePath("C:/Workspace", "edk2", "MdePkg", "Include")
            ```
        """
        if abspath == (None,):
            return None

        abspath = Path(*[part.replace("\\", "/") for part in abspath])

        relpath = None
        found = False

        # Check if the Absolute path starts with any of the package paths. If a match is found, build the relative
        # path based off that package.
        #
        # Sort the package paths from from longest to shortest. This handles the case where a package and a package
        # path are in the same directory. See the following path_utilities_test for a detailed explanation of the
        # scenario: test_get_relative_path_when_folder_is_next_to_package
        for packagepath in sorted(self._package_path_list, reverse=True):

            # If a match is found, use the original string to avoid change in case
            if abspath.is_relative_to(packagepath):
                self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using PackagePath")
                relpath = abspath.relative_to(packagepath)
                found = True
                break

        # If a match was not found, check if absolute path is based on the workspace root.
        if not found and abspath.is_relative_to(self._workspace_path):
            self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using WorkspacePath")
            relpath = abspath.relative_to(self._workspace_path)
            found = True

        if found:
            relpath = relpath.as_posix()
            self.logger.debug(f'[{abspath}] -> [{relpath}]')
            return relpath

        # Absolute path was not in reference to a package path or the workspace root.
        self.logger.error("Failed to convert AbsPath to Edk2Relative Path")
        self.logger.error(f'AbsolutePath: {abspath}')
        return None

    def GetAbsolutePathOnThisSystemFromEdk2RelativePath(self, *relpath: str, log_errors: Optional[bool]=True) -> str:
        """Given a relative path return an absolute path to the file in this workspace.

        Args:
            *relpath: Relative path to convert. Can be the entire path or parts of the path provided separately
            log_errors: whether to log errors

        Returns:
            (str): absolute path in the OS specific form
            (None): invalid relpath
            (None): Unable to get the absolute path

        Example:
            ```python
                abs_path = edk2path.GetAbsolutePathOnThisSystemFromEdk2RelativePath("MdePkg/Include")
                abs_path = edk2path.GetAbsolutePathOnThisSystemFromEdk2RelativePath("MdePkg", "Include")
            ```
        """
        if relpath == (None,):
            return None

        relpath = Path(*[part.replace("\\", "/") for part in relpath])
        abspath = self._workspace_path / relpath
        if abspath.exists():
            return str(abspath)

        for a in self._package_path_list:
            abspath = a / relpath
            if abspath.exists():
                return str(abspath)
        if log_errors:
            self.logger.error("Failed to convert Edk2Relative Path to an Absolute Path on this system.")
            self.logger.error("Relative Path: %s" % relpath)

        return None

    def GetContainingPackage(self, InputPath: str) -> str:
        """Finds the package that contains the given path.

        This isn't perfect, but at least identifies the direcotry consistently.


        Args:
            InputPath: absolute path to a file, directory, or module. Supports both windows and posix paths.

        Returns:
            (str): name of the package that the path is in.
        """
        self.logger.debug("GetContainingPackage: %s" % InputPath)
        InputPath = Path(InputPath.replace("\\", "/"))
        # Make a list that has the path case normalized for comparison.
        # Note: This only does anything on Windows

        # 1. Handle the case that InputPath is not in the workspace tree
        path_root = None
        if not InputPath.is_relative_to(self._workspace_path):
            for p in self._package_path_list:
                if InputPath.is_relative_to(p):
                    path_root = p
                    break
            if not path_root:
                return None
        else:
            path_root = self._workspace_path

        # 2. Determine if the path is under a package in the workspace

        # Start the search within the first available directory. If provided InputPath is a directory, start there,
        # else (if InputPath is a file) move to it's parent directory and start there.
        if InputPath.is_dir():
            dirpath = InputPath
        else:
            dirpath = InputPath.parent

        while not path_root.samefile(dirpath):
            if dirpath.exists():
                for f in dirpath.iterdir():
                    if f.suffix.lower() =='.dec':
                        return dirpath.name

            dirpath = dirpath.parent

        return None

    def GetContainingModules(self, input_path: str) -> list[str]:
        """Find the list of modules (inf files) for a file path.

        Note: This function only accepts absolute paths. An exception will
              be raised if a non-absolute path is given.

        Note: If input_path does not exist in the filesystem, this function
              will try to return the likely containing module(s) but if the
              entire module has been deleted, this isn't possible.

        - If a .inf file is given, that file is returned.
        - Otherwise, the nearest set of .inf files (in the closest parent)
          will be returned in a list of file path strings.

        Args:
            input_path: Absolute path to a file, directory, or module.
                Supports both Windows and Posix like paths.

        Returns:
            (list[str]): Absolute paths of .inf files that could be the
                         containing module.
        """
        input_path = Path(input_path.replace("\\", "/"))
        if not input_path.is_absolute():
            # Todo: Return a more specific exception type when
            # https://github.com/tianocore/edk2-pytool-library/issues/184 is
            # implemented.
            raise Exception("Module path must be absolute.")

        all_root_paths = self._package_path_list + [self._workspace_path]

        # For each root path, find the maximum allowed root in its hierarchy.
        maximum_root_paths = all_root_paths
        for root_path in maximum_root_paths:
            for other_root_path in maximum_root_paths[:]:
                if root_path == other_root_path:
                    continue
                if root_path.is_relative_to(other_root_path):
                    if len(root_path.parts) > len(other_root_path.parts):
                        maximum_root_paths.remove(root_path)
                    else:
                        maximum_root_paths.remove(other_root_path)

        # Verify the file path is within a valid workspace or package path
        # directory.
        for path in maximum_root_paths:
            if input_path.is_relative_to(path):
                break
        else:
            return []

        modules = []
        if input_path.suffix.lower() == '.inf':
            # Return the file path given since it is a module .inf file
            modules = [str(input_path)]

        if not modules:
            # Continue to ascend directories up to a maximum root path.
            #
            # This handles cases like:
            #   ModuleDir/      |   ModuleDir/      | ...similarly nested files
            #     Module.inf    |     Module.inf    |
            #     x64/          |     Common/       |
            #       file.c      |       X64/        |
            #                   |         file.c    |
            #
            # The terminating condition of the loop is when a maximum root
            # path has been reached.
            #
            # A maximum root path represents the maximum allowed ascension
            # point in the input_path directory hierarchy as sub-roots like
            # a package path pointing under a workspace path are already
            # accounted for during maximum root path filtering.
            #
            # Given a root path is either the workspace or a package path,
            # neither of which are a module directory, once that point is
            # reached, all possible module candidates are exhausted.
            current_dir = input_path.parent
            while current_dir not in maximum_root_paths:
                if current_dir.is_dir():
                    current_dir_inf_files = \
                        [str(f) for f in current_dir.iterdir() if
                         f.is_file() and f.suffix.lower() == '.inf']
                    if current_dir_inf_files:
                        # A .inf file(s) exist in this directory.
                        #
                        # Since this is the closest parent that can be considered
                        # a module, return the .inf files as module candidates.
                        modules.extend(current_dir_inf_files)
                        break

                current_dir = current_dir.parent

        return modules
