# @file path_utilities_test.py
# Contains unit test routines for the path_utilities class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path, PurePath

from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class PathUtilitiesTest(unittest.TestCase):

    def _make_file_helper(self, parentpath: str, filename: str) -> None:
        '''Simple internal helper to make a file and write basic content.'''
        with open(os.path.join(parentpath, filename), "w") as f:
            f.write("Unit test content")

    def _make_edk2_module_helper(self, parentpath: str, modname: str, extension_case_lower: bool = True) -> str:
        '''Simple internal helper to make a folder and inf like edk2
        return the path to the module folder.
        '''
        modfolder = os.path.join(parentpath, modname)
        os.makedirs(modfolder, exist_ok=True)
        fn = modname + (".inf" if extension_case_lower else ".INF")
        self._make_file_helper(modfolder, fn)
        return modfolder

    def _make_edk2_package_helper(self, path: str, packagename: str, extension_case_lower: bool = True) -> str:
        '''Simple internal helper to make an ed2 package as follows:

        path/
          packagename/
            packagename.dec
            module1/
              module1.inf
            module2/
              module2.inf
              X64/
                TestFile.c

        return the path to the new package
        '''
        pkgfolder = os.path.join(path, packagename)
        os.makedirs(pkgfolder, exist_ok=True)
        pn = packagename + (".dec" if extension_case_lower else ".DEC")
        self._make_file_helper(pkgfolder, pn)
        self._make_edk2_module_helper(pkgfolder, "module1", extension_case_lower=extension_case_lower)
        p2 = self._make_edk2_module_helper(pkgfolder, "module2", extension_case_lower=extension_case_lower)
        p3 = os.path.join(p2, "X64")
        os.makedirs(p3)
        self._make_file_helper(p3, "TestFile.c")
        return pkgfolder

    def setUp(self):
        '''Unittest fixture run before each test.
        Create a tmpdir and set the current working dir there.
        '''
        self.tmp = tempfile.mkdtemp()
        self.precwd = os.getcwd()
        os.chdir(self.tmp)  # move to tempfile root

    def tearDown(self):
        '''Unittest fixture run after each test.
        Delete the tempdir and set the current working dir back.
        '''
        os.chdir(self.precwd)
        if os.path.isdir(self.tmp):
            shutil.rmtree(self.tmp)

    # TESTS

    def test_basic_init_ws_abs(self):
        '''Test edk2path with valid absolute path to workspace.'''
        pathobj = Edk2Path(self.tmp, [])
        self.assertEqual(pathobj.WorkspacePath, self.tmp)

    def test_basic_init_ws_cwd(self):
        '''Test edk2path with a relative path to workspace.'''
        relpath = "testrootfolder"
        fullpath = os.path.join(self.tmp, relpath)
        os.mkdir(fullpath)
        pathobj = Edk2Path(relpath, [])
        self.assertEqual(pathobj.WorkspacePath, fullpath)

    def test_nonexistant_ws(self):
        '''Test edk2path with invalid workspace.'''
        invalid_ws = os.path.join(self.tmp, "invalidpath")
        with self.assertRaises(Exception):
            Edk2Path(invalid_ws, [])

    def test_nonexistant_abs(self):
        '''Test edk2path with valid ws but invalid pp.'''
        pp = "doesnot_exist"
        pp_full_1 = os.path.join(self.tmp, pp)
        # absolute path
        with self.assertRaises(Exception):
            Edk2Path(self.tmp, [pp_full_1])
        # relative path
        with self.assertRaises(Exception):
            Edk2Path(self.tmp, [pp])
        # confirm optional parameter to remove invalid pp values
        pathobj = Edk2Path(self.tmp, [pp], error_on_invalid_pp=False)
        self.assertEqual(len(pathobj.PackagePathList), 0)

    def test_pp_inside_workspace(self):
        '''Test with packagespath pointing to folder nested inside workspace
        root/                   <-- current working directory
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    pp packages here
                ws packages here.
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)

        # pp absolute
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folder_pp1_abs)

        # pp relative to workspace
        pathobj = Edk2Path(ws_abs, [folder_pp_rel])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folder_pp1_abs)

        # pp relative to cwd
        pathobj = Edk2Path(ws_abs, [os.path.join(ws_rel, folder_pp_rel)])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folder_pp1_abs)

    def test_pp_outside_workspace(self):
        '''Test with packagespath pointing to folder outside of workspace
        root/                   <-- current working directory
            folder_ws/           <-- workspace root
                ws packages here
            folder_pp/       <-- packages path
                pp packages here.

        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(self.tmp, folder_pp_rel)
        os.mkdir(folder_pp1_abs)

        # pp absolute
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folder_pp1_abs)

        # pp relative to cwd
        pathobj = Edk2Path(ws_abs, [folder_pp_rel])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folder_pp1_abs)

    def test_invalid_pp(self):
        """Tests that the exception message contains all invalid paths and no valid paths."""
        ws = Path(self.tmp, "folder_ws")
        ws.mkdir()
        (ws / "good_path").mkdir()

        with self.assertRaises(NotADirectoryError) as context:
            Edk2Path(str(ws), ["bad_pp_path", "bad_pp_path2", "good_path"], error_on_invalid_pp=True)
        self.assertTrue('bad_pp_path' in str(context.exception))
        self.assertTrue('bad_pp_path2' in str(context.exception))
        self.assertTrue('good_path' not in str(context.exception))

        # Make sure we don't throw an exception unless we mean to
        Edk2Path(str(ws), ["bad_pp_path", "bad_pp_path2", "good_path"], error_on_invalid_pp=False)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_basic_init_ws_abs_different_case(self):
        inputPath = self.tmp.capitalize()
        if self.tmp[0].isupper():
            inputPath = self.tmp[0].lower() + self.tmp[1:]

        pathobj = Edk2Path(inputPath, [])
        self.assertNotEqual(pathobj.WorkspacePath, self.tmp)

    def test_get_containing_package_inside_workspace(self):
        '''Test basic usage of GetContainingPackage with packages path nested
        inside the workspace.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # directory in WSTestPkg
        p = os.path.join(ws_pkg_abs, "X64")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # WSTestPkg directory itself
        self.assertEqual(pathobj.GetContainingPackage(ws_pkg_abs), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return None
        p = os.path.join(ws_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return None
        p = os.path.join(folder_pp1_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

    def test_get_containing_package_outside_workspace(self):
        '''Test basic usage of GetContainingPackage with packages path
        outside the workspace.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
            folder_pp/       <-- packages path
                PPTestPkg/   <-- A edk2 package
                    PPTestPkg.DEC
                    module1/
                        module1.INF
                    module2/
                        module2.INF
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(self.tmp, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return None
        p = os.path.join(ws_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return None
        p = os.path.join(folder_pp1_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_get_containing_package_ws_abs_different_case(self):
        '''Test basic usage of GetContainingPackage when the workspace path has different case for
        the drive letter then the incoming paths. This can happen on Windows
        if os.path.realpath is used.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        wsi_abs = os.path.join(self.tmp, ws_rel.capitalize())  # invert the case of the first char of the ws folder name
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(wsi_abs, [folder_pp1_abs])

        # confirm inverted
        self.assertNotEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(os.path.normcase(pathobj.WorkspacePath), os.path.normcase(ws_abs))

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return None
        p = os.path.join(ws_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p), ws_rel)

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return None
        p = os.path.join(folder_pp1_abs, "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p), folder_pp_rel)

    def test_get_containing_package_with_nonexistent_path(self):
        '''Test basic usage of GetContainingPackage when the file path does not exist.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        wsi_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(wsi_abs, [folder_pp1_abs])

        p = os.path.join(pp_pkg_abs, "subfolder", "testfile2.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        p = os.path.join(ws_pkg_abs, "subfolder", "testfile2.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

    def test_get_containing_modules_with_relative_path(self):
        """Test that a relative path raises an exception.

        Note: GetContainingModules() only accepts absolute paths.

        File layout:
            root/                   <-- Current working directory (self.tmp)
                folder_ws           <-- Workspace directory
                    pp1             <-- Package Path 1
                        PPTestPkg   <-- An edk2 package
                            PPTestPkg.DEC
                            module1
                                module1.INF
                            module2
                                module2.INF
                                X64
                                    TestFile.c
                    WSTestPkg       <-- An edk2 package
                        WSTestPkg.dec
                        module1
                            module1.inf
                        module2
                            module2.inf
                            X64
                                TestFile.c
        """
        # Make the workspace directory: folder_ws/
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        # Make Package Path 1 directory: folder_ws/pp1
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)

        # Make WSTestPkg: folder_ws/WSTestPkg
        ws_p_name = "WSTestPkg"
        self._make_edk2_package_helper(ws_abs, ws_p_name)

        # Make PPTestPkg in Package Path 1: folder_ws/pp1/PPTestPkg
        pp_p_name = "PPTestPkg"
        self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)

        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # Change the current working directory to the workspace
        os.chdir(ws_abs)

        # Pass a valid relative path to GetContainingModules()
        #   folder_ws/WSTestPkg/module2/module2.inf
        p = os.path.join("WSTestPkg", "module2", "module2.inf")
        self.assertRaises(Exception, pathobj.GetContainingModules, p)

        # Pass an invalid relative path to GetContainingModules()
        #   folder_ws/WSTestPkg/module2/module3.inf
        p = os.path.join("WSTestPkg", "module2", "module3.inf")
        self.assertRaises(Exception, pathobj.GetContainingModules, p)

        # Pass a valid non .inf relative path to GetContainingModules()
        #   folder_ws/WSTestPkg/module2/X64/TestFile.c
        p = os.path.join("WSTestPkg", "module2", "X64", "TestFile.c")
        self.assertRaises(Exception, pathobj.GetContainingModules, p)

    def test_get_containing_module_with_infs_in_other_temp_dirs(self):
        '''Test that GetContainingModule does not look outside the workspace
        root for modules. To do so, a temporary .inf file is placed in the
        user's temporary directory. Such a file could already exist and
        similarly impact test results. To ensure consistent test results, this
        test explicitly creates such a file.

        File layout:

        root/                         <-- User temporary directory
           SomeModule.inf             <-- .inf file in user temporary directory
           <temp_working_dir>/        <-- Current working directory (self.tmp)
               folder_ws              <-- Workspace root
                   WSTestPkg          <-- An edk2 package
                       WSTestPkg.dec
                       module1
                           module1.inf
                       module2
                           module2.inf
                           X64
                               TestFile.c
        '''
        # Make the workspace directory: <self.tmp>/folder_ws/
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)

        # Make WSTestPkg: <self.tmp>/folder_ws/WSTestPkg/
        ws_p_name = "WSTestPkg"
        self._make_edk2_package_helper(ws_abs, ws_p_name)

        # Place a .inf file in the temporary directory
        # <Temporary Directory>/SomeModule.inf
        other_inf = os.path.join(os.path.dirname(self.tmp), "SomeModule.inf")
        with open(other_inf, 'w'):
            pass

        try:
            pathobj = Edk2Path(ws_abs, [])

            # File outside of the workspace - invalid and should return None
            p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
            relist = pathobj.GetContainingModules(p)
            self.assertEqual(len(relist), 0)
        finally:
            if os.path.isfile(other_inf):
                os.remove(other_inf)

    def test_get_containing_modules_path_format(self):
        """Test that get containing modules returns the exact expected path.

        Note: GetContainingModules() only accepts absolute paths.

        File layout:
            root/                   <-- Current working directory (self.tmp)
                folder_ws           <-- Workspace directory
                    pp1             <-- Package Path 1
                        PPTestPkg   <-- An edk2 package
                            PPTestPkg.DEC
                            module1
                                module1.INF
                            module2
                                module2.INF
                                X64
                                    TestFile.c
                    WSTestPkg       <-- An edk2 package
                        WSTestPkg.dec
                        module1
                            module1.inf
                        module2
                            module2.inf
                            X64
                                TestFile.c
        """
        # /folder_ws/
        ws_rel = "folder_ws"
        # /folder_ws/pp1/
        folder_pp_rel = "pp1"
        # /folder_ws/WSTestPkg/
        ws_p_name = "WSTestPkg"
        # /folder_ws/pp1/PPTestPkg
        pp_p_name = "PPTestPkg"

        # Create <temp_dir>/folder_ws/
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        # Create <temp_dir>/folder_ws/pp1/
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)

        # Create <temp_dir>/folder_ws/WSTestPkg/
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)

        # Create <temp_dir>/folder_ws/pp1/PPTestPkg
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # Check the case and location of the absolute path
        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        expected_module_inf = p
        actual_module_inf_list = pathobj.GetContainingModules(p)
        self.assertEqual(len(actual_module_inf_list), 1)
        self.assertEqual(expected_module_inf, actual_module_inf_list[0])

        # Check the case and location of the absolute path
        p = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile.c")
        expected_module_inf = os.path.join(ws_pkg_abs, "module2", "module2.inf")
        actual_module_inf_list = pathobj.GetContainingModules(p)
        self.assertEqual(len(actual_module_inf_list), 1)
        self.assertEqual(expected_module_inf, actual_module_inf_list[0])

    def test_get_containing_module(self):
        '''Test basic usage of GetContainingModule with packages path nested
        inside the workspace.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # file in WSTestPkg root.  Module list is empty
        p = os.path.join(ws_pkg_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file in module in WSTestPkg/module1/module1.inf
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(ws_pkg_abs, "module1", "module1.inf")),
            Path(relist[0]))

        # file in workspace root - no package- should return ws root
        p = os.path.join(ws_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file in module2 x64
        p = os.path.join(ws_pkg_abs, "module2", "X64", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(ws_pkg_abs, "module2", "module2.inf")),
            Path(relist[0]))

        # inf file in module2 x64
        p = os.path.join(ws_pkg_abs, "module2", "module2.inf")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(ws_pkg_abs, "module2", "module2.inf")),
            Path(relist[0]))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file in module in PPTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(pp_pkg_abs, "module1", "module1.INF")),
            Path(relist[0]))

        # inf file in module in PPTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(pp_pkg_abs, "module1", "module1.INF")),
            Path(relist[0]))

        # file in packages path root - no module
        p = os.path.join(folder_pp1_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file doesn't exist and parent folder doesn't exist
        p = os.path.join(ws_pkg_abs, "ThisParentDirDoesNotExist", "ThisFileDoesNotExist.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file doesn't exist and parent folder doesn't exist and parent parent folder doesn't exist
        p = os.path.join(ws_pkg_abs, "DirDirDoesNotExist", "DirDoesNotExist", "FileDoesNotExist.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file doesn't exist and parent folder doesn't exist but parent parent is valid module
        # file in module in WSTestPkg/module1/module1.inf
        p = os.path.join(ws_pkg_abs, "module1", "ThisParentDirDoesNotExist", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertEqual(
            Path(os.path.join(ws_pkg_abs, "module1", "module1.inf")),
            Path(relist[0]))

    def test_get_edk2_relative_path_from_absolute_path_posix(self):
        """Test that relative path returned is a POSIX path.

        File layout:
            root/                   <-- Current working directory (self.tmp)
                folder_ws           <-- Workspace directory
                    pp1             <-- Package Path 1
                        PPTestPkg   <-- An edk2 package
                            PPTestPkg.DEC
                            module1
                                module1.INF
                            module2
                                module2.INF
                                X64
                                    TestFile.c
                    WSTestPkg       <-- An edk2 package
                        WSTestPkg.dec
                        module1
                            module1.inf
                        module2
                            module2.inf
                            X64
                                TestFile.c
        """
        # /folder_ws/
        ws_rel = "folder_ws"
        # /folder_ws/pp1/
        folder_pp_rel = "pp1"
        # /folder_ws/WSTestPkg/
        ws_p_name = "WSTestPkg"
        # /folder_ws/pp1/PPTestPkg
        pp_p_name = "PPTestPkg"

        # Create <temp_dir>/folder_ws/
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        # Create <temp_dir>/folder_ws/pp1/
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)

        # Create <temp_dir>/folder_ws/WSTestPkg/
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)

        # Create <temp_dir>/folder_ws/pp1/PPTestPkg
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        expected_rel_from_abs_path = PurePath(os.path.join(pp_p_name, "module1", "module1.INF")).as_posix()
        actual_rel_from_abs_path = pathobj.GetEdk2RelativePathFromAbsolutePath(p)
        self.assertEqual(expected_rel_from_abs_path, actual_rel_from_abs_path)

        actual_rel_from_abs_path = pathobj.GetEdk2RelativePathFromAbsolutePath(pp_pkg_abs, "module1", "module1.INF")
        self.assertEqual(expected_rel_from_abs_path, actual_rel_from_abs_path)

        p = os.path.join(ws_pkg_abs, "module_2", "X64", "TestFile.inf")
        expected_rel_from_abs_path = PurePath(os.path.join(ws_p_name, "module_2", "X64", "TestFile.inf")).as_posix()
        actual_rel_from_abs_path = pathobj.GetEdk2RelativePathFromAbsolutePath(p)
        self.assertEqual(expected_rel_from_abs_path, actual_rel_from_abs_path)

        actual_rel_from_abs_path = pathobj.GetEdk2RelativePathFromAbsolutePath(ws_pkg_abs, "module_2", "X64", "TestFile.inf")
        self.assertEqual(expected_rel_from_abs_path, actual_rel_from_abs_path)

    def test_get_edk2_relative_path_from_absolute_path(self):
        '''Test basic usage of GetEdk2RelativePathFromAbsolutePath with packages path nested
        inside the workspace.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # file in packages path
        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{pp_p_name}/module1/module1.INF")

        # file in workspace
        p = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64/TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(ws_pkg_abs, "module2", "X64", "TestFile.c"), f"{ws_p_name}/module2/X64/TestFile.c")

        # Folder in packages path
        p = os.path.join(pp_pkg_abs, "module2", "X64")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{pp_p_name}/module2/X64")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp_pkg_abs, "module2", "X64"), f"{pp_p_name}/module2/X64")

        # Folder in workspace
        p = os.path.join(ws_pkg_abs, "module2", "X64")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(ws_pkg_abs, "module2", "X64"), f"{ws_p_name}/module2/X64")

        # file not in workspace
        p = os.path.join(self.tmp, "module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(self.tmp, "module2", "X64", "TestFile.c"))

        # pass in bad parameter
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(None))

        # file is outside of code tree and not absolute path
        p = os.path.join("module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        self.assertIsNone(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath("module2", "X64", "TestFile.c"))

        # file is cwd relative but not absolute path
        p = os.path.join(ws_rel, ws_p_name, "module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(ws_rel, ws_p_name, "module2", "X64", "TestFile.c"))

        # ensure converted path keeps original capitalization
        p = os.path.join(ws_pkg_abs, "Module2", "x64", "TESTFILE.C")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/Module2/x64/TESTFILE.C")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(ws_pkg_abs, "Module2", "x64", "TESTFILE.C"), f"{ws_p_name}/Module2/x64/TESTFILE.C")

    def test_get_relative_path_when_packages_path_list_contains_substrings(self):
        '''Test usage of GetEdk2RelativePathFromAbsolutePath when members of PackagePathList contain
        substrings of themselves, for example "MU" and "MU_TIANO"
        File layout:
         root/                    <-- current working directory (self.tmp)
            folder_ws/            <-- workspace root
                folder_pp/        <-- packages path
                    PPTestPkg1/   <-- A edk2 package
                        PPTestPkg1.DEC
                        module1/
                            module1.INF
                            X64/
                                TestFile1.c
                folder_pp_suffix/ <-- packages path
                    PPTestPkg2/   <-- A edk2 package
                        PPTestPkg2.DEC
                        module2/
                            module2.INF
                            X64/
                                TestFile2.c.
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp1_rel = "folder_pp"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp1_rel)
        os.mkdir(folder_pp1_abs)
        folder_pp2_rel = "folder_pp_suffix"
        folder_pp2_abs = os.path.join(ws_abs, folder_pp2_rel)
        os.mkdir(folder_pp2_abs)
        ws_p_name = "PPTestPkg2"
        ws_pkg_abs = self._make_edk2_package_helper(folder_pp2_abs, ws_p_name)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs, folder_pp2_abs])

        # file in workspace
        p = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile2.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64/TestFile2.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(ws_pkg_abs, "module2", "X64", "TestFile2.c"), f"{ws_p_name}/module2/X64/TestFile2.c")

    def test_get_relative_path_when_package_path_inside_package(self):
        '''Test a package_path directory inside the subfolders of a package.
            Should not raise an exception.

        File layout:
        root/                            <-- Current working directory
            folder_ws/                   <-- Workspace root
                folder_pp1/              <-- Package Path 1
                    PPTestPkg1/          <-- A valid edk2 package
                        PPTestPkg1.dec
                        folder_pp2/      <-- Package Path 2
                        module1/
                            module1.inf
                        module2/
                            module2.inf
                            X64/
                                TestFile.c
        '''
        folder_ws_rel = "folder_ws"
        folder_ws_abs = os.path.join(self.tmp, folder_ws_rel)
        os.mkdir(folder_ws_abs)

        folder_pp1_rel = "folder_pp1"
        folder_pp1_abs = os.path.join(folder_ws_abs, folder_pp1_rel)
        os.mkdir(folder_pp1_abs)

        pp1_name = "PPTestPkg1"
        pp1_abs = self._make_edk2_package_helper(folder_pp1_abs, pp1_name)

        folder_pp2_rel = "folder_pp2"
        folder_pp2_abs = os.path.join(pp1_abs, folder_pp2_rel)
        os.mkdir(folder_pp2_abs)

        pathobj = Edk2Path(folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])
        p = os.path.join(pp1_abs, "module2", "X64", "TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{pp1_name}/module2/X64/TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp1_abs, "module2", "X64", "TestFile.c"), f"{pp1_name}/module2/X64/TestFile.c")

    def test_get_relative_path_with_nested_packages(self):
        '''Test a two package paths that contain nested packages.
            Should raise an exception due to nested packages.

        File layout:
        root/                                   <-- Current working directory
            folder_ws/                          <-- Workspace root
                folder_pp1/                     <-- Package Path 1
                    PPTestPkg1/                 <-- A valid edk2 package
                        PPTestPkg1.dec
                        folder_pp2/             <-- Package Path 2
                            PPTestPkg2/         <-- A valid edk2 package
                                PPTestPkg2.dec
                                module1/
                                    module1.inf
                                module2/
                                    module2.inf
                                    X64/
                                        TestFile.c
                        module1/
                            module1.inf
                        module2/
                            module2.inf
                            X64/
                                TestFile.c
        '''
        folder_ws_rel = "folder_ws"
        folder_ws_abs = os.path.join(self.tmp, folder_ws_rel)
        os.mkdir(folder_ws_abs)

        folder_pp1_rel = "folder_pp1"
        folder_pp1_abs = os.path.join(folder_ws_abs, folder_pp1_rel)
        os.mkdir(folder_pp1_abs)

        pp1_name = "PPTestPkg1"
        pp1_abs = self._make_edk2_package_helper(folder_pp1_abs, pp1_name)

        folder_pp2_rel = "folder_pp2"
        folder_pp2_abs = os.path.join(pp1_abs, folder_pp2_rel)
        os.mkdir(folder_pp2_abs)

        pp2_name = "PPTestPkg2"
        self._make_edk2_package_helper(folder_pp2_abs, pp2_name)

        # Nested packages should raise an exception by default
        self.assertRaises(Exception, Edk2Path, folder_ws_abs, [folder_pp1_abs])
        self.assertRaises(Exception, Edk2Path, folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])

        # Nested packages should no longer raise an exception
        # Note: These tests can be removed when support for
        #       PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES is removed.
        os.environ["PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES"] = "true"
        Edk2Path(folder_ws_abs, [folder_pp1_abs])
        Edk2Path(folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])

        # Remove the environment variable now that the test above is complete
        os.environ.pop("PYTOOL_TEMPORARILY_IGNORE_NESTED_EDK_PACKAGES")

        # Nested packages should no longer raise an exception if explicitly
        # marked as known-bad.
        os.environ["PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES"] = "SomeOtherPkg,PPTestPkg1"
        Edk2Path(folder_ws_abs, [folder_pp1_abs])
        Edk2Path(folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])

        os.environ["PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES"] = "SomeOtherPkg,PPTestPkg2"
        Edk2Path(folder_ws_abs, [folder_pp1_abs])
        Edk2Path(folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])

        os.environ["PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES"] = "SomeOtherPkg,SomeOtherPkg2"
        self.assertRaises(Exception, Edk2Path, folder_ws_abs, [folder_pp1_abs])
        self.assertRaises(Exception, Edk2Path, folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])

        # Remove the environment variable now that the test above is complete
        os.environ.pop("PYTOOL_IGNORE_KNOWN_BAD_NESTED_PACKAGES")

    def test_get_relative_path_when_folder_is_next_to_package(self):
        '''Test usage of GetEdk2RelativePathFromAbsolutePath when a folder containing a package is in the same
        directory as a different package. This test ensures the correct value is returned regardless the order of
        the package paths.
        file layout:
        root/                      <-- Current working directory
            folder_ws/             <-- Workspace Root
                folder_pp1/        <-- A Package Path
                    PPTestPkg1     <-- A Package
                    folder_pp2/    <-- A Package Path
                        PPTestPkg2 <-- A Package.
        '''
        folder_ws_rel = "folder_ws"
        folder_ws_abs = os.path.join(self.tmp, folder_ws_rel)
        os.mkdir(folder_ws_abs)

        folder_pp1_rel = "folder_pp1"
        folder_pp1_abs = os.path.join(folder_ws_abs, folder_pp1_rel)
        os.mkdir(folder_pp1_abs)

        pp1_name = "PPTestPkg1"
        pp1_abs = self._make_edk2_package_helper(folder_pp1_abs, pp1_name)
        p1 = os.path.join(pp1_abs, "module2", "X64", "TestFile2.c")

        folder_pp2_rel = "folder_pp2"
        folder_pp2_abs = os.path.join(folder_pp1_abs, folder_pp2_rel)
        os.mkdir(folder_pp2_abs)

        pp2_name = "PPTestPkg2"
        pp2_abs = self._make_edk2_package_helper(folder_pp2_abs, pp2_name)
        p2 = os.path.join(pp2_abs, "module2", "X64", "TestFile2.c")

        pathobj = Edk2Path(folder_ws_abs, [folder_pp1_abs, folder_pp2_abs])
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p1), f'{pp1_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p2), f'{pp2_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp1_abs, "module2", "X64", "TestFile2.c"),
                         f'{pp1_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp2_abs, "module2", "X64", "TestFile2.c"),
                         f'{pp2_name}/module2/X64/TestFile2.c')

        pathobj = Edk2Path(folder_ws_abs, [folder_pp2_abs, folder_pp1_abs])
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p1), f'{pp1_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p2), f'{pp2_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp1_abs, "module2", "X64", "TestFile2.c"),
                         f'{pp1_name}/module2/X64/TestFile2.c')
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(pp2_abs, "module2", "X64", "TestFile2.c"),
                         f'{pp2_name}/module2/X64/TestFile2.c')

    def test_get_relative_path_when_path_does_not_exist(self):
        '''Test basic usage of GetEdk2RelativePathFromAbsolutePath with packages path nested
        inside the workspace, but the absolute path is not a real path.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # not existant file in packages path
        p = os.path.join(pp_pkg_abs, "module1", "FAKE.INF")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{pp_p_name}/module1/FAKE.INF")
        p = (pp_pkg_abs, "module1", "FAKE.INF")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(*p), f"{pp_p_name}/module1/FAKE.INF")

        # non existant file in non existant directory in packages path
        p = os.path.join(ws_pkg_abs, "module2", "X64", "FAKE", "FAKE.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64/FAKE/FAKE.c")
        p = (ws_pkg_abs, "module2", "X64", "FAKE", "FAKE.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(*p), f"{ws_p_name}/module2/X64/FAKE/FAKE.c")

        # not existant file in workspace
        p = os.path.join(ws_pkg_abs, "module2", "X64", "FAKE.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64/FAKE.c")
        p = (ws_pkg_abs, "module2", "X64", "FAKE.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(*p), f"{ws_p_name}/module2/X64/FAKE.c")

        # not existant file not in workspace
        p = os.path.join(self.tmp, "module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        p = (self.tmp, "module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(*p))

        # not existant file is outside of code tree and not absolute path
        p = os.path.join("module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        p = ("module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(*p))

        # not existant file is cwd relative but not absolute path
        p = os.path.join(ws_rel, ws_p_name, "module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))
        p = (ws_rel, ws_p_name, "module2", "X64", "FAKE.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(*p))

    def test_get_relative_path_when_package_is_not_directly_inside_packages_path(self):
        '''Test basic usage of GetEdk2RelativePathFromAbsolutePath when the
        package is not a direct subfolder of a packagespath, but atleast one
        folder away.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    folder_extra/
                        PPTestPkg/   <-- A edk2 package
                            PPTestPkg.DEC
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        folder_pp_rel = "folder_pp"
        folder_pp_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp_abs)

        folder_extra_rel = "folder_extra"
        folder_extra_abs = os.path.join(folder_pp_abs, folder_extra_rel)
        os.mkdir(folder_extra_abs)

        ws_p_name = "PPTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(folder_extra_abs, ws_p_name)
        pathobj = Edk2Path(ws_abs, [folder_pp_abs])

        p = os.path.join(ws_pkg_abs, "PPTestPkg.dec")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p),
                         f"{folder_extra_rel}/{ws_p_name}/{ws_p_name}.dec")
        p = (ws_pkg_abs, "PPTestPkg.dec")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(*p),
                         f"{folder_extra_rel}/{ws_p_name}/{ws_p_name}.dec")

    def test_get_edk2_relative_path_with_windows_path_on_linux(self):
        '''Test basic usage of GetEdk2RelativePathFromAbsolutePath when the
        provided path is a Windows path, but the code is running on linux.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    folder_extra/
                        PPTestPkg/   <-- A edk2 package
                            PPTestPkg.DEC
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        folder_pp_rel = "folder_pp"
        folder_pp_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp_abs)

        folder_extra_rel = "folder_extra"
        folder_extra_abs = os.path.join(folder_pp_abs, folder_extra_rel)
        os.mkdir(folder_extra_abs)

        ws_p_name = "PPTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(folder_extra_abs, ws_p_name)
        pathobj = Edk2Path(ws_abs, [folder_pp_abs])

        p = f"{ws_pkg_abs}\\module2\\X64\\TestFile.c"
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p),
                         f"{folder_extra_rel}/PPTestPkg/module2/X64/TestFile.c")
        p = (ws_pkg_abs, "module2", "X64", "TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(*p),
                         f"{folder_extra_rel}/PPTestPkg/module2/X64/TestFile.c")

    def test_get_absolute_path_on_this_system_from_edk2_relative_path(self):
        '''Test basic usage of GetAbsolutePathOnThisSystemFromEdk2RelativePath with packages path nested
        inside the workspace.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folder_ws/           <-- workspace root
                folder_pp/       <-- packages path
                    PPTestPkg/   <-- A edk2 package
                        PPTestPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            X64/
                                TestFile.c
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
        '''
        ws_rel = "folder_ws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folder_pp_rel = "pp1"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp_rel)
        os.mkdir(folder_pp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self._make_edk2_package_helper(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # file in packages path
        ep = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        self.assertEqual(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(pp_p_name, "module1", "module1.INF"), ep)
        rp = f"{pp_p_name}/module1/module1.INF"
        self.assertEqual(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(rp), ep)

        # file in workspace
        ep = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile.c")
        self.assertEqual(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(ws_p_name, "module2", "X64", "TestFile.c"), ep)
        rp = f"{ws_p_name}/module2/X64/TestFile.c"
        self.assertEqual(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(rp), ep)

        # file not in workspace
        rp = "DoesNotExistPkg/module2/X64/TestFile.c"
        self.assertIsNone(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(rp))

        # pass in bad parameter
        self.assertIsNone(pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(None))

    def test_get_absolute_path_then_relative_path_when_path_contains_repeated_packagepath_name(self):
        '''Test the back and forth between GetAbsolutePath and GetRelativeFromAbsolute when the
        path structure has multiple instances of a package path
        File layout:
         root/                  <-- current working directory (self.tmp)
            PlatformClientPkg/           <-- workspace root
                CLIENT_PKG/       <-- packages path
                    ClientPkg/   <-- A edk2 package
                        ClientPkg.DEC
                        module1/
                            module1.INF
                        module2/
                            module2.INF
                            x64/
                               TestFile.c.
        '''
        ws_rel = "PlatformClientPkg"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)

        folder_pp1_rel = "CLIENT_PKG"
        folder_pp1_abs = os.path.join(ws_abs, folder_pp1_rel)
        os.mkdir(folder_pp1_abs)

        ws_pkg_name = "ClientPkg"
        ws_pkg_abs = self._make_edk2_package_helper(folder_pp1_abs, ws_pkg_name)

        pathobj = Edk2Path(ws_abs, [folder_pp1_abs])

        # Check getting absolute path from relative path
        abspath = pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(
            ws_pkg_name, ws_pkg_name + ".dec")
        self.assertEqual(abspath, os.path.join(ws_pkg_abs, "ClientPkg.dec"))

        abspath = pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(
            os.path.join(ws_pkg_name, ws_pkg_name + ".dec"))
        self.assertEqual(abspath, os.path.join(ws_pkg_abs, "ClientPkg.dec"))

        # check get relative path from abs path
        expectedpath = f"{ws_pkg_name}/ClientPkg.dec"

        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(abspath), expectedpath)
