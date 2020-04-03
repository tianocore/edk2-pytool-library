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
        relpath = None
        found = False
        if abspath is None:
            return None
        for a in self.PackagePathList:
            stripped = abspath.lower().partition(a.lower())[2]
            if stripped:
                # found our path...now lets correct for case
                relpath = abspath[len(a):]
                found = True
                self.logger.debug("Successfully converted AbsPath to Edk2Relative Path using PackagePath")
                self.logger.debug("AbsolutePath: %s found in PackagePath: %s" % (abspath, a))
                break

        if(not found):
            # try to strip the workspace
            stripped = abspath.lower().partition(self.WorkspacePath.lower())[2]
            if stripped:
                # found our path...now lets correct for case
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

        dirpathprevious = os.path.dirname(InputPath)
        dirpath = os.path.dirname(InputPath)
        while(dirpath is not None):
            #
            # if at the root of a packagepath return the previous dir.
            # this catches cases where a package has no DEC
            #
            if(dirpath in self.PackagePathList):
                a = os.path.basename(dirpathprevious)
                self.logger.debug("Reached Package Path.  Using previous directory: %s" % a)
                return a
            #
            # if at the root of the workspace return the previous dir.
            # this catches cases where a package has no DEC
            #
            if(dirpath == self.WorkspacePath):
                a = os.path.basename(dirpathprevious)
                self.logger.debug("Reached Workspace Path.  Using previous directory: %s" % a)
                return a
            #
            # Check for a DEC file in this folder
            # if here then return the directory name as the "package"
            #
            for f in os.listdir(dirpath):
                if fnmatch.fnmatch(f, '*.dec'):
                    a = os.path.basename(dirpath)
                    self.logger.debug("Found DEC file at %s.  Pkg is: %s", dirpath, a)
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
        if InputPath.endswith(".inf"):
            return [InputPath]

        modules = []
        # Check current dir
        dirpath = os.path.dirname(InputPath)
        for f in os.listdir(dirpath):
            if fnmatch.fnmatch(f, '*.inf'):
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
                if fnmatch.fnmatch(f, '*.inf'):
                    self.logger.debug("Found INF file in %s.  INf is: %s", dirpath, f)
                    modules.append(os.path.join(dirpath, f))

        return modules
