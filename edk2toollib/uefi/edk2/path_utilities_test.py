# @file path_utilities_test.py
# Contains unit test routines for the path_utilities class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os
import sys
import tempfile
import shutil
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class PathUtilitiesTest(unittest.TestCase):

    def MakeFile(self, parentpath, filename):
        with open(os.path.join(parentpath, filename), "w") as f:
            f.write("Unit test content")

    def MakeEdk2Module(self, parentpath, modname, extension_case_lower=True):
        modfolder = os.path.join(parentpath, modname)
        os.makedirs(modfolder, exist_ok=True)
        fn = modname + (".inf" if extension_case_lower else ".INF")
        self.MakeFile(modfolder, fn)
        return modfolder

    def MakeEdk2Package(self, path, packagename, extension_case_lower=True):
        ''' Make an ed2 package as follows:

        path/
          packagename/
            packagename.dec
            module1/
              module1.inf
            module2/
              module2.inf
              X64/
                TestFile.c
        '''
        pkgfolder = os.path.join(path, packagename)
        os.makedirs(pkgfolder, exist_ok=True)
        pn = packagename + (".dec" if extension_case_lower else ".DEC")
        self.MakeFile(pkgfolder, pn)
        self.MakeEdk2Module(pkgfolder, "module1", extension_case_lower=extension_case_lower)
        p2 = self.MakeEdk2Module(pkgfolder, "module2", extension_case_lower=extension_case_lower)
        p3 = os.path.join(p2, "X64")
        os.makedirs(p3)
        self.MakeFile(p3, "TestFile.c")
        return pkgfolder

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.precwd = os.getcwd()
        os.chdir(self.tmp)  # move to tempfile root

    def tearDown(self):
        os.chdir(self.precwd)
        if os.path.isdir(self.tmp):
            shutil.rmtree(self.tmp)

    # TESTS

    def test_basic_init_ws_abs(self):
        ''' test edk2path with valid absolute path to workspace'''
        pathobj = Edk2Path(self.tmp, [])
        self.assertEqual(pathobj.WorkspacePath, self.tmp)

    def test_basic_init_ws_cwd(self):
        ''' test edk2path with a relative path to workspace'''
        relpath = "testrootfolder"
        fullpath = os.path.join(self.tmp, relpath)
        os.mkdir(fullpath)
        pathobj = Edk2Path(relpath, [])
        self.assertEqual(pathobj.WorkspacePath, fullpath)

    def test_nonexistant_ws(self):
        ''' test edk2path with invalid workspace'''

        invalidws = os.path.join(self.tmp, "invalidpath")
        with self.assertRaises(Exception):
            Edk2Path(invalidws, [])

    def test_nonexistant_abs(self):
        ''' test edk2path with valid ws but invalid pp'''
        pp = "doesnot_exist"
        pp_full_1 = os.path.join(self.tmp, pp)
        # absolute path
        with self.assertRaises(Exception):
            Edk2Path(self.tmp, [pp_full_1])
        # relative path
        with self.assertRaises(Exception):
            Edk2Path(self.tmp, [pp])

    def test_pp_inside_workspace(self):
        ''' test with packagespath pointing to folder nested inside workspace
        root/                   <-- current working directory
            folderws/           <-- workspace root
                folderpp/       <-- packages path
                    pp packages here
                ws packages here
        '''
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)

        # pp absolute
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folderpp1_abs)

        # pp relative to workspace
        pathobj = Edk2Path(ws_abs, [folderpp_rel])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folderpp1_abs)

        # pp relative to cwd
        pathobj = Edk2Path(ws_abs, [os.path.join(ws_rel, folderpp_rel)])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folderpp1_abs)

    def test_pp_outside_workspace(self):
        ''' test with packagespath pointing to folder outside of workspace
        root/                   <-- current working directory
            folderws/           <-- workspace root
                ws packages here
            folderpp/       <-- packages path
                pp packages here

        '''
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(self.tmp, folderpp_rel)
        os.mkdir(folderpp1_abs)

        # pp absolute
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folderpp1_abs)

        # pp relative to cwd
        pathobj = Edk2Path(ws_abs, [folderpp_rel])
        self.assertEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(pathobj.PackagePathList[0], folderpp1_abs)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_basic_init_ws_abs_different_case(self):
        inputPath = self.tmp.capitalize()
        if self.tmp[0].isupper():
            inputPath = self.tmp[0].lower() + self.tmp[1:]

        pathobj = Edk2Path(inputPath, [])
        self.assertNotEqual(pathobj.WorkspacePath, self.tmp)

    def test_get_containing_package_inside_workspace(self):
        ''' test basic usage of GetContainingPackage with packages path nested
        inside the workspace

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                folderpp/       <-- packages path
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
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return ws root
        p = os.path.join(ws_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_rel)

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return packages path dir
        p = os.path.join(folderpp1_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), folderpp_rel)

    def test_get_containing_package_outside_workspace(self):
        ''' test basic usage of GetContainingPackage with packages path
        outside the workspace

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                WSTestPkg/   <-- A edk2 package
                    WSTestPkg.dec
                    module1/
                        module1.inf
                    module2/
                        module2.inf
                        X64/
                            TestFile.c
            folderpp/       <-- packages path
                PPTestPkg/   <-- A edk2 package
                    PPTestPkg.DEC
                    module1/
                        module1.INF
                    module2/
                        module2.INF
                        X64/
                            TestFile.c
        '''
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(self.tmp, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return ws root
        p = os.path.join(ws_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_rel)

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return packages path dir
        p = os.path.join(folderpp1_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), folderpp_rel)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_get_containing_package_ws_abs_different_case(self):
        ''' test basic usage of GetContainingPackage when the workspace path has different case for
        the drive letter then the incoming paths. This can happen on Windows
        if os.path.realpath is used.

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                folderpp/       <-- packages path
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
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        wsi_abs = os.path.join(self.tmp, ws_rel.capitalize())  # invert the case of the first char of the ws folder name
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(wsi_abs, [folderpp1_abs])

        # confirm inverted
        self.assertNotEqual(pathobj.WorkspacePath, ws_abs)
        self.assertEqual(os.path.normcase(pathobj.WorkspacePath), os.path.normcase(ws_abs))

        # file in WSTestPkg root
        p = os.path.join(ws_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in module in WSTestPkg
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_p_name)

        # file in workspace root - no package- should return ws root
        p = os.path.join(ws_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), ws_rel)

        # file outside of the workspace - invalid and should return None
        p = os.path.join(os.path.dirname(ws_abs), "testfile.c")
        self.assertIsNone(pathobj.GetContainingPackage(p))

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in module in WSTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), pp_p_name)

        # file in packages path root - no package- should return packages path dir
        p = os.path.join(folderpp1_abs, "testfile.c")
        self.assertEqual(pathobj.GetContainingPackage(p), folderpp_rel)

    def test_get_containing_module(self):
        ''' test basic usage of GetContainingModule with packages path nested
        inside the workspace

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                folderpp/       <-- packages path
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
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])

        # file in WSTestPkg root.  Module list is empty
        p = os.path.join(ws_pkg_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file in module in WSTestPkg/module1/module1.inf
        p = os.path.join(ws_pkg_abs, "module1", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertIn(os.path.join(ws_pkg_abs, "module1", "module1.inf"), relist)

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
        self.assertIn(os.path.join(ws_pkg_abs, "module2", "module2.inf"), relist)

        # inf file in module2 x64
        p = os.path.join(ws_pkg_abs, "module2", "module2.inf")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertIn(os.path.join(ws_pkg_abs, "module2", "module2.inf"), relist)

        # file in PPTestPkg root
        p = os.path.join(pp_pkg_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

        # file in module in PPTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertIn(os.path.join(pp_pkg_abs, "module1", "module1.INF"), relist)

        # inf file in module in PPTestPkg
        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 1)
        self.assertIn(os.path.join(pp_pkg_abs, "module1", "module1.INF"), relist)

        # file in packages path root - no package- should return packages path dir
        p = os.path.join(folderpp1_abs, "testfile.c")
        relist = pathobj.GetContainingModules(p)
        self.assertEqual(len(relist), 0)

    def test_get_edk2_relative_path_from_absolute_path(self):
        ''' test basic usage of GetEdk2RelativePathFromAbsolutePath with packages path nested
        inside the workspace

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                folderpp/       <-- packages path
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
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])

        # file in packages path
        p = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{pp_p_name}/module1/module1.INF")

        # file in workspace
        p = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile.c")
        self.assertEqual(pathobj.GetEdk2RelativePathFromAbsolutePath(p), f"{ws_p_name}/module2/X64/TestFile.c")

        # file not in workspace
        p = os.path.join(self.tmp, "module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))

        # pass in bad parameter
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(None))

        # file is outside of code tree and not absolute path
        p = os.path.join("module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))

        # file is cwd relative but not absolute path
        p = os.path.join(ws_rel, ws_p_name, "module2", "X64", "TestFile.c")
        self.assertIsNone(pathobj.GetEdk2RelativePathFromAbsolutePath(p))

    def test_get_absolute_path_on_this_sytem_from_edk2_relative_path(self):
        ''' test basic usage of GetAbsolutePathOnThisSytemFromEdk2RelativePath with packages path nested
        inside the workspace

        File layout:

         root/                  <-- current working directory (self.tmp)
            folderws/           <-- workspace root
                folderpp/       <-- packages path
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
        ws_rel = "folderws"
        ws_abs = os.path.join(self.tmp, ws_rel)
        os.mkdir(ws_abs)
        folderpp_rel = "pp1"
        folderpp1_abs = os.path.join(ws_abs, folderpp_rel)
        os.mkdir(folderpp1_abs)
        ws_p_name = "WSTestPkg"
        ws_pkg_abs = self.MakeEdk2Package(ws_abs, ws_p_name)
        pp_p_name = "PPTestPkg"
        pp_pkg_abs = self.MakeEdk2Package(folderpp1_abs, pp_p_name, extension_case_lower=False)
        pathobj = Edk2Path(ws_abs, [folderpp1_abs])

        # file in packages path
        ep = os.path.join(pp_pkg_abs, "module1", "module1.INF")
        rp = f"{pp_p_name}/module1/module1.INF"
        self.assertEqual(pathobj.GetAbsolutePathOnThisSytemFromEdk2RelativePath(rp), ep)

        # file in workspace
        ep = os.path.join(ws_pkg_abs, "module2", "X64", "TestFile.c")
        rp = f"{ws_p_name}/module2/X64/TestFile.c"
        self.assertEqual(pathobj.GetAbsolutePathOnThisSytemFromEdk2RelativePath(rp), ep)

        # file not in workspace
        rp = f"DoesNotExistPkg/module2/X64/TestFile.c"
        self.assertIsNone(pathobj.GetAbsolutePathOnThisSytemFromEdk2RelativePath(rp))

        # pass in bad parameter
        self.assertIsNone(pathobj.GetAbsolutePathOnThisSytemFromEdk2RelativePath(None))
