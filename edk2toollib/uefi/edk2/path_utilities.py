# @file path_utilities.py
# Code to help convert Edk2, absolute, and relative file paths
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import os
import logging
import fnmatch
import glob
from typing import Iterable
from pathlib import Path

#
# Class to help convert from absolute path to EDK2 build path
# using workspace and packagepath variables
#


class Edk2Path(object):

    def __init__(self, ws: os.PathLike, packagepathlist: Iterable[os.PathLike], error_on_invalid_pp: bool = True):
        """ An Edk2Path object is an object that can be used to resolve edk2 relative paths

        Args:
            ws: absolute path or cwd relative path of the workspace.
            packagespathlist: list of packages path.
                Entries can be Absolute path, workspace relative path, or CWD relative.
            error_on_invalid_pp: default value is True. If packages path value is invalid raise exception
        """

        self.WorkspacePath = ws
        self.logger = logging.getLogger("Edk2Path")
        if (not os.path.isabs(ws)):
            self.WorkspacePath = os.path.abspath(os.path.join(os.getcwd(), ws))

        if (not os.path.isdir(self.WorkspacePath)):
            self.logger.error("Workspace path invalid.  {0}".format(ws))
            raise Exception("Workspace path invalid.  {0}".format(ws))

        # Set PackagePath
        self.PackagePathList = list()
        for a in packagepathlist:
            if (os.path.isabs(a)):
                self.PackagePathList.append(a)
            else:
                # see if workspace relative
                wsr = os.path.join(ws, a)
                if (os.path.isdir(wsr)):
                    self.PackagePathList.append(wsr)
                else:
                    # assume current working dir relative.  Will catch invalid dir when checking whole list
                    self.PackagePathList.append(os.path.abspath(os.path.join(os.getcwd(), a)))

        error = False
        for a in self.PackagePathList[:]:
            if (not os.path.isdir(a)):
                self.logger.log(logging.ERROR if error_on_invalid_pp else logging.WARNING,
                                "Invalid package path entry {0}".format(a))
                self.PackagePathList.remove(a)  # remove invalid path
                error = True

        # report error
        if (error and error_on_invalid_pp):
            raise Exception("Invalid package path directory(s)")

        # for each package path, trace from packagepath to the
        # either the workspace root or filesystem root and verify
        # no *.DEC file exists. This would signify a nested package.
        for package_path in self.PackagePathList:
            p = Path(package_path)
            ws = self.WorkspacePath
            while p != p.parent:
                if str(p).lower() == str(ws).lower():
                    break
                if len(glob.glob(f'{p}/*dec')) != 0:
                    raise Exception(f'Nested packages not allowed. Pkg path [{package_path}] nested in Package [{p}]')
                p = p.parent

    def GetEdk2RelativePathFromAbsolutePath(self, abspath):
        ''' Given an absolute path return a edk2 path relative to workspace or packagespath.

        Note: absolute path must be in the OS specific path form
        Note: the relative path will be in POSIX-like path form

        @param abspath: absolute path to a file or directory. Path must contain OS specific separator.

        @ret POSIX-like relative path to workspace or packagespath
        @ret None if path is not valid
        '''
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
            relpath = relpath.replace(os.sep, "/")
            self.logger.debug(f'[{abspath}] -> [{relpath.strip("/")}]')
            return relpath.strip("/")

        # Absolute path was not in reference to a package path or the workspace root.
        self.logger.error("Failed to convert AbsPath to Edk2Relative Path")
        self.logger.error(f'AbsolutePath: {abspath}')
        return None

    def GetAbsolutePathOnThisSystemFromEdk2RelativePath(self, relpath, log_errors=True):
        ''' Given a edk2 relative path return an absolute path to the file or
        directory in this workspace.

        Note: The relative path must be in POSIX-like path form
        Note: The absolute path will return the OS specific path form
        Note: For case insensitive operating systems the case of the input
        relpath will be used for the return value even if it doesn't match
        the case in the filesystem.

        If not valid or doesn't exist return None'''

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

    def GetContainingPackage(self, InputPath):
        ''' Find the package this path belongs to using some Heuristic.  This isn't
        perfect but at least identifies the directory consistently.

        Note: The inputPath must be in the OS specific path form

        @param InputPath:  absolute path to a file, directory, or module. Supports both Windows and Linux like paths

        @ret Name of Package that the module is in.
        '''
        self.logger.debug("GetContainingPackage: %s" % InputPath)
        # Make a list that has the path case normalized for comparison.
        # This only does anything on Windows
        NormCasePackagesPathList = [os.path.normcase(x) for x in self.PackagePathList]

        # check InputPath to make sure it is at least in the folder structure of the code tree
        if os.path.normcase(self.WorkspacePath) not in os.path.normcase(InputPath):
            # not in workspace - check all the packages paths
            found_in_pp = False
            for p in NormCasePackagesPathList:
                if p in os.path.normcase(InputPath):
                    found_in_pp = True
                    break
            if (not found_in_pp):
                self.logger.error(f"{InputPath} not in code tree")
                self.logger.info("PackagePath is: %s" % os.pathsep.join(self.PackagePathList))
                self.logger.info("Workspace path is : %s" % self.WorkspacePath)
                return None

        # Start the search within the first available directory. If provided InputPath is a directory, start there,
        # else (if InputPath is a file) move to it's parent directory and start there.
        if os.path.isdir(InputPath):
            dirpathprevious = str(InputPath)
            dirpath = str(InputPath)
        else:
            dirpathprevious = os.path.dirname(InputPath)
            dirpath = os.path.dirname(InputPath)

        # InputPath is in workspace or PackagesPath for worst case scenario.
        for _ in range(100):  # 100 is just a counter to avoid infinite loops.  Path nodes are unlikely to exceed 100
            #
            # Check for a DEC file in this folder
            # if here then return the directory name as the "package"
            #
            for f in os.listdir(dirpath):
                if fnmatch.fnmatch(f.lower(), '*.dec'):
                    a = os.path.basename(dirpath)
                    self.logger.debug("Found DEC file at %s.  Pkg is: %s", dirpath, a)
                    return a

            #
            # if at the root of the workspace return the previous dir.
            # this catches cases where a package has no DEC
            #
            if os.path.normcase(dirpath) == os.path.normcase(self.WorkspacePath):
                a = os.path.basename(dirpathprevious)
                self.logger.debug("Reached Workspace Path.  Using previous directory: %s" % a)
                return a

            #
            # if at the root of a packagepath return the previous dir.
            # this catches cases where a package has no DEC
            #
            if os.path.normcase(dirpath) in NormCasePackagesPathList:
                a = os.path.basename(dirpathprevious)
                self.logger.debug("Reached Package Path.  Using previous directory: %s" % a)
                return a

            dirpathprevious = dirpath
            dirpath = os.path.dirname(dirpath)

        self.logger.error("Failed to find containing package for %s" % InputPath)
        self.logger.info("PackagePath is: %s" % os.pathsep.join(self.PackagePathList))
        self.logger.info("Workspace path is : %s" % self.WorkspacePath)
        return None

    def GetContainingModules(self, InputPath: str) -> list:
        '''Find the list of modules (infs) that file path is in
        for now just assume any inf in the same dir or if none
        then check parent dir.  If InputPath is not in the filesystem
        this function will try to return the likely containing module
        but if the entire module has been deleted this isn't possible.

        Note: The inputPath must be in the OS specific path form

        @param InputPath:  absolute path to file

        @ret list of abs path file paths for module infs
        '''

        self.logger.debug("GetContainingModules: %s" % InputPath)

        # if INF return self
        if fnmatch.fnmatch(InputPath.lower(), '*.inf'):
            return [InputPath]

        # Before checking the local filesystem for an INF
        # make sure filesystem has file or at least folder
        if not os.path.isfile(InputPath):
            logging.debug("InputPath doesn't exist in filesystem")

        modules = []
        # Check current dir
        dirpath = os.path.dirname(InputPath)
        if os.path.isdir(dirpath):
            for f in os.listdir(dirpath):
                if fnmatch.fnmatch(f.lower(), '*.inf'):
                    self.logger.debug("Found INF file in %s.  INf is: %s", dirpath, f)
                    modules.append(os.path.join(dirpath, f))

        # if didn't find any in current dir go to parent dir.
        # this handles cases like:
        # ModuleDir/
        #   Module.inf
        #   x64/
        #     file.c
        #
        if (len(modules) == 0):
            dirpath = os.path.dirname(dirpath)
            if os.path.isdir(dirpath):
                for f in os.listdir(dirpath):
                    if fnmatch.fnmatch(f.lower(), '*.inf'):
                        self.logger.debug("Found INF file in %s.  INf is: %s", dirpath, f)
                        modules.append(os.path.join(dirpath, f))

        return modules
