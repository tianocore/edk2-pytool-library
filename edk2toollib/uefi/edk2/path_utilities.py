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

#
# Class to help convert from absolute path to EDK2 build path
# using workspace and packagepath variables
#


class Edk2Path(object):

    #
    # ws - absolute path or cwd relative to workspace
    # packagepathlist - list of packages path.  Absolute path list or workspace relative path
    #
    def __init__(self, ws, packagepathlist):
        self.WorkspacePath = ws
        self.logger = logging.getLogger("Edk2Path")
        if(not os.path.isabs(ws)):
            self.WorkspacePath = os.path.abspath(os.path.join(os.getcwd(), ws))

        if(not os.path.isdir(self.WorkspacePath)):
            self.logger.error("Workspace path invalid.  {0}".format(ws))
            raise Exception("Workspace path invalid.  {0}".format(ws))

        # Set PackagePath
        self.PackagePathList = list()
        for a in packagepathlist:
            if(os.path.isabs(a)):
                self.PackagePathList.append(a)
            else:
                # see if workspace relative
                wsr = os.path.join(ws, a)
                if(os.path.isdir(wsr)):
                    self.PackagePathList.append(wsr)
                else:
                    # assume current working dir relative.  Will catch invalid dir when checking whole list
                    self.PackagePathList.append(os.path.abspath(os.path.join(os.getcwd(), a)))

        error = False
        for a in self.PackagePathList:
            if(not os.path.isdir(a)):
                self.logger.error("Invalid package path entry {0}".format(a))
                error = True

        # report error
        if(error):
            raise Exception("Invalid package path directory(s)")

    def GetEdk2RelativePathFromAbsolutePath(self, abspath):
        ''' Given an absolute path return a edk2 path relative
        to workspace or packagespath.

        If not valid return None
        '''

        relpath = None
        found = False
        if abspath is None:
            return None
        for a in (os.path.normcase(p) for p in self.PackagePathList):
            if os.path.normcase(abspath).startswith(a):
                # found our path...now use original strings to avoid
                # change in case
                relpath = abspath[len(a):]
                found = True
                self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using PackagePath")
                self.logger.debug("AbsolutePath: %s found in PackagePath: %s" % (abspath, a))
                break

        if(not found):
            # Does path start with workspace
            if os.path.normcase(abspath).startswith(os.path.normcase(self.WorkspacePath)):
                # found our path...now use original strings to avoid
                # change in case
                relpath = abspath[len(self.WorkspacePath):]
                found = True
                self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using WorkspacePath")
                self.logger.debug("AbsolutePath: %s found in Workspace: %s" % (abspath, self.WorkspacePath))

        if(found):
            relpath = relpath.replace(os.sep, "/")
            return relpath.lstrip("/")

        # didn't find the path for conversion.
        self.logger.error("Failed to convert AbsPath to Edk2Relative Path")
        self.logger.error("AbsolutePath: %s" % abspath)
        return None

    def GetAbsolutePathOnThisSytemFromEdk2RelativePath(self, relpath):
        ''' Given a edk2 relative path return an absolute path to the file
        in this workspace.

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
            if(os.path.exists(abspath)):
                return abspath
        self.logger.error("Failed to convert Edk2Relative Path to an Absolute Path on this system.")
        self.logger.error("Relative Path: %s" % relpath)

        return None

    # Find the package this path belongs to using
    # some Heuristic.  This isn't perfect but at least
    # identifies the directory consistently
    #
    # @param InputPath:  absolute path to module
    #
    # @ret Name of Package that the module is in.
    def GetContainingPackage(self, InputPath):
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
            if(not found_in_pp):
                self.logger.error(f"{InputPath} not in code tree")
                self.logger.info("PackagePath is: %s" % os.pathsep.join(self.PackagePathList))
                self.logger.info("Workspace path is : %s" % self.WorkspacePath)
                return None

        # InputPath is in workspace or PackagesPath for worst case scenario.

        dirpathprevious = os.path.dirname(InputPath)
        dirpath = os.path.dirname(InputPath)
        while(True):
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

    # Find the list of modules (infs) that file path is in
    #
    # for now just assume any inf in the same dir or if none
    # then check parent dir.
    #
    # @param InputPath:  absolute path to file
    #
    # @ret list of abs path file paths for module infs
    def GetContainingModules(self, InputPath: str) -> list:
        self.logger.debug("GetContainingModules: %s" % InputPath)

        # if INF return self
        if fnmatch.fnmatch(InputPath.lower(), '*.inf'):
            return [InputPath]

        modules = []
        # Check current dir
        dirpath = os.path.dirname(InputPath)
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
        if(len(modules) == 0):
            dirpath = os.path.dirname(dirpath)
            for f in os.listdir(dirpath):
                if fnmatch.fnmatch(f.lower(), '*.inf'):
                    self.logger.debug("Found INF file in %s.  INf is: %s", dirpath, f)
                    modules.append(os.path.join(dirpath, f))

        return modules
