# @file locate_tools.py
# This module provides python services that locate common development tools using vswhere.exe,
# vsvars.bat, and other Windows based tools.  This works best on systems running Windows
# and with dev tools installed but will attempt to use known paths for WinSDK if the dev
# tools are not available.  This is only a best effort to locate the SDK tools in well
# known/default install locations.
#
# Suggested Dev Tools:
#   Current Windows SDKs
#   Visual Studio 2017 Build Tools or newer
#
# Note: When this module is used in local develop mode it will download vswhere.exe from the github.
#       It will confirm the hash is a known good value.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import pkg_resources
import os
import logging
import glob
import subprocess
from edk2toollib.utility_functions import RunCmd
from edk2toollib.utility_functions import GetHostInfo
import re
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import urllib.error
import urllib.request

# Update this when you want a new version of VsWhere
__VERSION = "2.8.4"
__URL = "https://github.com/microsoft/vswhere/releases/download/{}/vswhere.exe".format(__VERSION)
__SHA256 = "e50a14767c27477f634a4c19709d35c27a72f541fb2ba5c3a446c80998a86419"

#
# Supported Versions that can be queried with vswhere
# Use lower case for key as all comparisons will be lower case
#
supported_vs_versions = {"vs2017": "15.0,16.0", "vs2019": "16.0,17.0"}


# Downloads VSWhere
def _DownloadVsWhere(unpack_folder: os.PathLike = None):
    if unpack_folder is None:
        unpack_folder = os.path.dirname(__VsWherePath())

    out_file_name = os.path.join(unpack_folder, "vswhere.exe")
    logging.info("Attempting to download vswhere to: {}. This may take a second.".format(unpack_folder))
    # check if we have the vswhere file already downloaded
    if not os.path.isfile(out_file_name):
        try:
            # Download the file and save it locally under `temp_file_name`
            with urllib.request.urlopen(__URL) as response, open(out_file_name, 'wb') as out_file:
                out_file.write(response.read())
        except urllib.error.HTTPError as e:
            logging.error("We ran into an issue when getting VsWhere")
            raise e

    # do the hash to make sure the file is good
    with open(out_file_name, "rb") as file:
        import hashlib
        temp_file_sha256 = hashlib.sha256(file.read()).hexdigest()
    if temp_file_sha256 != __SHA256:
        # delete the file since it's not what we're expecting
        os.remove(out_file_name)
        raise RuntimeError(f"VsWhere - sha256 does not match\n\tdownloaded:\t{temp_file_sha256}\n\t")


def __VsWherePath():
    file = "vswhere.exe"
    requirement = pkg_resources.Requirement.parse("edk2-pytool-library")
    file_path = os.path.join("edk2toollib", "bin", file)
    vswhere_path = pkg_resources.resource_filename(requirement, file_path)
    return vswhere_path


####
#
# https://docs.microsoft.com/en-us/vswhere/install-vswhere-client-tools
#
# @return string "/PATH/TO/vswhere.exe" or None
####
def GetVsWherePath(fail_on_not_found: bool = True):
    vswhere_path = __VsWherePath()
    # check if we can't find it, look for vswhere in the path
    if not os.path.isfile(vswhere_path):
        for env_var in os.getenv("PATH").split(os.pathsep):
            env_var = os.path.join(os.path.normpath(env_var), "vswhere.exe")
            if os.path.isfile(env_var):
                vswhere_path = env_var
                break

    # if we still can't find it, download it
    if not os.path.isfile(vswhere_path):
        vswhere_dir = os.path.dirname(vswhere_path)
        try:  # try to download
            _DownloadVsWhere(vswhere_dir)
        except Exception:
            logging.warning("Tried to download VsWhere and failed")
            pass

    # if we're still hosed
    if not os.path.isfile(vswhere_path) and fail_on_not_found:
        logging.error("We weren't able to find vswhere!")
        return None

    return vswhere_path


####
# Finds a product with VS Where
#
# product: is defined by vswhere tool
# vs_version: helper to find version of supported VS version (example vs2019).
####
def FindWithVsWhere(products: str = "*", vs_version: str = None):
    cmd = "-latest -nologo -all -property installationPath"
    vs_where_path = GetVsWherePath()
    if vs_where_path is None:
        logging.warning("We weren't able to find VSWhere")
        return (1, None)
    if(products is not None):
        cmd += " -products " + products
    if(vs_version is not None):
        vs_version = vs_version.lower()
        if vs_version in supported_vs_versions.keys():
            cmd += " -version " + supported_vs_versions[vs_version]
        else:
            logging.warning("Invalid or unsupported vs_version " + vs_version)
            return (2, None)
    a = StringIO()
    ret = RunCmd(vs_where_path, cmd, outstream=a)
    if(ret != 0):
        a.close()
        return (ret, None)
    p1 = a.getvalue().strip()
    a.close()
    if(len(p1.strip()) > 0):
        return (0, p1)
    return (ret, None)


# Run visual studio batch file and collect the
# interesting environment values
#
#  Inspiration taken from cpython for this method of env collection
#
# keys: enumerable list with names of env variables to collect after bat run
# arch: arch to run.  amd64, x86, ??
# product: value defined by vswhere.exe
# vs_version: helper to find version of supported VS version (example vs2019).
# returns a dictionary of the interesting environment variables
def QueryVcVariables(keys: list, arch: str = None, product: str = None, vs_version: str = None):
    """Launch vcvarsall.bat and read the settings from its environment.  This is a windows only function
    and Windows is case insensitive for the keys"""

    if product is None:
        product = "*"
    if arch is None:
        # TODO: look up host architecture?
        arch = "amd64"
    interesting = set(x.upper() for x in keys)
    result = {}
    ret, vs_path = FindWithVsWhere(product, vs_version)
    if ret != 0 or vs_path is None:
        logging.warning("We didn't find VS path or otherwise failed to invoke vsWhere")
        raise ValueError("Bad VC")
    vcvarsall_path = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvarsall.bat")
    logging.debug("Calling '%s %s'", vcvarsall_path, arch)
    popen = subprocess.Popen('"%s" %s & set' % (vcvarsall_path, arch), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = popen.communicate()
        if popen.wait() != 0:
            raise Exception(stderr.decode("mbcs"))
        stdout = stdout.decode("mbcs")
        for line in stdout.split("\n"):
            if '=' not in line:
                continue
            line = line.strip()
            key, value = line.split('=', 1)
            if key.upper() in interesting:
                if value.endswith(os.pathsep):
                    value = value[:-1]
                result[key] = value
    finally:
        popen.stdout.close()
        popen.stderr.close()

    if len(result) != len(interesting):
        logging.debug("Input: " + str(sorted(interesting)))
        logging.debug("Result: " + str(sorted(list(result.keys()))))
        result_set = set(list(result.keys()))
        difference = list(interesting.difference(result_set))

        logging.error("We were not able to find on the keys requested from vcvarsall.")
        logging.error("We didn't find: %s" % str(difference))
        raise ValueError("Missing keys when querying vcvarsall: " + str(difference))
    return result


# return 1 if a > b
# return 0 if b == a
# return -1 if a < b
def _CompareWindowVersions(a, b):
    a_periods = str(a).count(".")
    b_periods = str(b).count(".")
    if a_periods == 3 and b_periods != 3:
        return 1
    if b_periods == 3 and a_periods != 3:
        return -1
    if a_periods != 3 and b_periods != 3:
        return 0
    a_parts = str(a).split(".")
    b_parts = str(b).split(".")
    for i in range(3):
        a_p = int(a_parts[i])
        b_p = int(b_parts[i])
        if a_p > b_p:
            return 1
        if a_p < b_p:
            return -1
    return 0


def _CheckArchOfMatch(match):
    '''
    Returns if this binary matches our host
    returns true or false
    if no arch is in the match, then we return true
    '''
    match = str(match).lower()
    isx86 = "x86" in match
    isx64 = "x64" in match or "amd64" in match
    isArm64 = "aarch" in match or "aarch64" in match or "arm64" in match
    isi386 = "i386" in match
    isArm = not isArm64 and ("arm" in match)
    count = 0
    count += 1 if isx64 else 0
    count += 1 if isx86 else 0
    count += 1 if isArm else 0
    count += 1 if isArm64 else 0
    count += 1 if isi386 else 0
    if count == 0:  # we don't know what arch this is?
        return True
    if count > 1:  # there are more than one arch for this binary
        logging.warning("We found more than one architecture for {}. Results maybe inconsistent".format(match))
        return True

    _, arch, bits = GetHostInfo()
    bits = int(bits)
    if isx86 and (bits < 32 or arch != "x86"):
        return False
    if isx64 and (bits < 64 or arch != "x86"):
        return False
    if isi386:
        # TODO add i386 to GetHostInfo
        return False
    if isArm64 and (bits < 64 or arch != "ARM"):
        return False
    if isArm and (bits < 32 or arch != "ARM"):
        return False
    return True


# does a glob in the folder that your sdk is
# uses the environmental variable WindowsSdkDir and tries to use WindowsSDKVersion
def FindToolInWinSdk(tool: str, product=None, arch=None):
    variables = ["WindowsSdkDir", "WindowsSDKVersion"]
    # get the value with QueryVcVariables
    try:
        results = QueryVcVariables(variables, product, arch)
        # Get the variables we care about
        sdk_dir = results["WindowsSdkDir"]
        sdk_ver = results["WindowsSDKVersion"]
    except ValueError:
        sdk_dir = os.path.join(os.getenv("ProgramFiles(x86)"), "Windows Kits", "10", "bin")
        sdk_ver = "0.0.0.0"
    sdk_dir = os.path.realpath(sdk_dir)
    search_pattern = os.path.join(sdk_dir, "**", tool)

    match_offset = len(sdk_dir)
    # look for something like 10.0.12323.0123
    windows_ver_regex = re.compile(r'\d+\.\d+\.\d+\.\d+')
    top_version_so_far = -1
    top_match = None
    # Look at in match in the tree
    for match in glob.iglob(search_pattern, recursive=True):
        match_file = match[match_offset:]  # strip off the root
        match_front, match_end = os.path.split(match_file)  # split off the filename
        versions = windows_ver_regex.findall(match_front)  # look for windows versions
        top_ver_match = 0
        if not _CheckArchOfMatch(match_front):  # make sure it's a good arch for us
            continue
        if len(versions) == 0:
            top_ver_match = "0.0.0.0"  # if we have a bad version, we should fall to a bad version
        for version in versions:  # find the highest version if there are multiple in this?
            is_current_sdk_version = _CompareWindowVersions(version, sdk_ver) == 0
            if _CompareWindowVersions(version, top_ver_match) > 0 or is_current_sdk_version:
                top_ver_match = version
        # if we have a highest version or one that matches our current from environment variables?
        is_current_sdk_version = _CompareWindowVersions(top_ver_match, sdk_ver) == 0
        if _CompareWindowVersions(top_ver_match, top_version_so_far) > 0 or is_current_sdk_version:
            top_version_so_far = top_ver_match
            top_match = match
    if top_match is None:
        logging.critical("We weren't able to find {}".format(tool))
    return top_match
