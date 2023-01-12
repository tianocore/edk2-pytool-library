# @file path_utilities.py
# Code to help convert Edk2, absolute, and relative file paths
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help convert Edk2, absolute, and relative file paths."""
import os
import logging
import fnmatch
import errno
from typing import Iterable
from pathlib import Path


class Edk2Path(object):
    """Represents edk2 file paths.

    Class that helps perform path operations within an EDK workspace.
    """

    def __init__(self, ws: os.PathLike, package_path_list: Iterable[os.PathLike],
                 error_on_invalid_pp: bool = True):
        """Constructor.

        Args:
            ws (os.PathLike): absolute path or cwd relative path of the workspace.
            package_path_list (Iterable[os.PathLike]): list of packages path.
                Entries can be Absolute path, workspace relative path, or CWD relative.
            error_on_invalid_pp (bool): default value is True. If packages path
                                        value is invalid raise exception.

        Raises:
            (NotADirectoryError): Invalid workspace or package path directory.
        """
        self.WorkspacePath = ws
        self.logger = logging.getLogger("Edk2Path")

        # Other code is dependent the following types, so keep it that way:
        #   - self.PackagePathList: List[str]
        #   - self.WorkspacePath: str

        self.PackagePathList = []
        self.WorkspacePath = ""

        workspace_candidate_path = Path(ws)

        if not workspace_candidate_path.is_absolute():
            workspace_candidate_path = Path(os.getcwd(), ws)

        if not workspace_candidate_path.is_dir():
            raise NotADirectoryError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                workspace_candidate_path.resolve())

        self.WorkspacePath = str(workspace_candidate_path)

        candidate_package_path_list = []
        for a in package_path_list:
            if os.path.isabs(a):
                candidate_package_path_list.append(Path(a))
            else:
                wsr = Path(self.WorkspacePath, a)
                if wsr.is_dir():
                    candidate_package_path_list.append(wsr)
                else:
                    # assume current working dir relative.  Will catch invalid dir when checking whole list
                    candidate_package_path_list.append(Path(os.getcwd(), a))

        error = False
        for a in candidate_package_path_list[:]:
            if not a.is_dir():
                self.logger.log(logging.ERROR if error_on_invalid_pp else
                                logging.WARNING,
                                f"Invalid package path entry {a.resolve()}")
                candidate_package_path_list.remove(a)
                error = True

        self.PackagePathList = [str(p) for p in candidate_package_path_list]

        if error and error_on_invalid_pp:
            raise NotADirectoryError(errno.ENOENT, os.strerror(errno.ENOENT),
                                     a.resolve())

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
        for package_path in candidate_package_path_list:
            package_path_packages[package_path] = \
                [Path(p).parent for p in package_path.glob('**/*.dec')]

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

    def GetEdk2RelativePathFromAbsolutePath(self, abspath):
        """Given an absolute path return a edk2 path relative to workspace or packagespath.

        Note: absolute path must be in the OS specific path form
        Note: the relative path will be in POSIX-like path form

        Args:
            abspath (os.PathLike): absolute path to a file or directory. Path must contain OS specific separator.

        Returns:
            (os.PathLike): POSIX-like relative path to workspace or packagespath
            (None): abspath is none
            (None): path is not valid
        """
        if abspath is None:
            return None

        relpath = None
        found = False

        # Check if the Absolute path starts with any of the package paths. If a match is found, build the relative
        # path based off that package.
        #
        # Sort the package paths from from longest to shortest. This handles the case where a package and a package
        # path are in the same directory. See the following path_utilities_test for a detailed explanation of the
        # scenario: test_get_relative_path_when_folder_is_next_to_package
        for packagepath in sorted((os.path.normcase(p) for p in self.PackagePathList), reverse=True):

            # If a match is found, use the original string to avoid change in case
            if os.path.normcase(abspath).startswith(packagepath):
                self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using PackagePath")
                relpath = abspath[len(packagepath):]
                found = True
                break

        # If a match was not found, check if absolute path is based on the workspace root.
        if not found and os.path.normcase(abspath).startswith(os.path.normcase(self.WorkspacePath)):
            self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using WorkspacePath")
            relpath = abspath[len(self.WorkspacePath):]
            found = True

        if found:
            relpath = relpath.replace(os.sep, "/").strip("/")
            self.logger.debug(f'[{abspath}] -> [{relpath}]')
            return relpath

        # Absolute path was not in reference to a package path or the workspace root.
        self.logger.error("Failed to convert AbsPath to Edk2Relative Path")
        self.logger.error(f'AbsolutePath: {abspath}')
        return None

    def GetAbsolutePathOnThisSystemFromEdk2RelativePath(self, relpath, log_errors=True):
        """Given a edk2 relative path return an absolute path to the file in this workspace.

        Args:
            relpath (os.PathLike): POSIX-like path
            log_errors (:obj:`bool`, optional): whether to log errors

        Returns:
            (os.PathLike): absolute path in the OS specific form
            (None): invalid relpath
            (None): Unable to get the absolute path
        """
        if relpath is None:
            return None
        relpath = relpath.replace("/", os.sep)
        abspath = os.path.join(self.WorkspacePath, relpath)
        if os.path.exists(abspath):
            return abspath

        for a in self.PackagePathList:
            abspath = os.path.join(a, relpath)
            if (os.path.exists(abspath)):
                return abspath
        if log_errors:
            self.logger.error("Failed to convert Edk2Relative Path to an Absolute Path on this system.")
            self.logger.error("Relative Path: %s" % relpath)

        return None

    def GetContainingPackage(self, InputPath: str) -> str:
        """Find the package that contains the given path.

        This isn't perfect but at least identifies the directory consistently.

        Note: The inputPath must be in the OS specific path form.

        Args:
            InputPath (str): absolute path to a file, directory, or module.
                             supports both windows and linux like paths.

        Returns:
            (str): name of the package that the module is in.
        """
        self.logger.debug("GetContainingPackage: %s" % InputPath)
        # Make a list that has the path case normalized for comparison.
        # Note: This only does anything on Windows
        package_paths = [os.path.normcase(x) for x in self.PackagePathList]
        workspace_path = os.path.normcase(self.WorkspacePath)

        # 1. Handle the case that InputPath is not in the workspace tree
        path_root = None
        if workspace_path not in os.path.normcase(InputPath):
            for p in package_paths:
                if p in os.path.normcase(InputPath):
                    path_root = p
                    break
            if not path_root:
                return None

        # 2. Determine if the path is under a package in the workspace

        # Start the search within the first available directory. If provided InputPath is a directory, start there,
        # else (if InputPath is a file) move to it's parent directory and start there.
        if os.path.isdir(InputPath):
            dirpath = str(InputPath)
        else:
            dirpath = os.path.dirname(InputPath)

        if not path_root:
            path_root = workspace_path

        while path_root != os.path.normcase(dirpath):
            if os.path.exists(dirpath):
                for f in os.listdir(dirpath):
                    if fnmatch.fnmatch(f.lower(), '*.dec'):
                        a = os.path.basename(dirpath)
                        return a

            dirpath = os.path.dirname(dirpath)

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
            input_path (str): Absolute path to a file, directory, or module.
                              Supports both Windows and Linux like paths.

        Returns:
            (list[str]): Absolute paths of .inf files that could be the
                         containing module.
        """
        input_path = Path(input_path)
        if not input_path.is_absolute():
            # Todo: Return a more specific exception type when
            # https://github.com/tianocore/edk2-pytool-library/issues/184 is
            # implemented.
            raise Exception("Module path must be absolute.")

        package_paths = [Path(os.path.normcase(x)) for x in self.PackagePathList]
        workspace_path = Path(os.path.normcase(self.WorkspacePath))
        all_root_paths = package_paths + [workspace_path]

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
        if input_path.suffix == '.inf':
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
