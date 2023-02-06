##
# Utility Functions to support re-use in python scripts.
# Includes functions for running external commands, etc
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module containing utility functions to support re-use in python scripts."""
import re
import os
import stat
import logging
import datetime
import time
import shutil
import threading
import subprocess
import sys
import inspect
import platform
import importlib
from collections import namedtuple
import locale

from warnings import warn


# https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
# TODO make this a private class.
class PropagatingThread(threading.Thread):  # noqa
    """Class to support running commands from the shell in a python environment.

    Don't use directly.

    PropagatingThread copied from sample here:
    """

    def run(self):  # noqa
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):  # noqa
        super(PropagatingThread, self).join()
        if self.exc:
            raise self.exc
        return self.ret


# http://stackoverflow.com/questions/19423008/logged-subprocess-communicate
# TODO make this a private function
def reader(filepath, outstream, stream, logging_level=logging.INFO, encodingErrors='strict'):  # noqa
    """Helper functions for running commands from the shell in python environment.

    Don't use directly

    process output stream and write to log.
    part of the threading pattern.
    """
    f = None
    # open file if caller provided path
    if (filepath):
        f = open(filepath, "w")

    (_, encoding) = locale.getdefaultlocale()
    while True:
        s = stream.readline().decode(encoding, errors=encodingErrors)
        if not s:
            break
        if (f is not None):
            # write to file if caller provided file
            f.write(s)
        if (outstream is not None):
            # write to stream object if caller provided object
            outstream.write(s)
        logging.log(logging_level, s.rstrip())
    stream.close()
    if (f is not None):
        f.close()


def GetHostInfo():
    """Returns a namedtuple containing information about host machine.

    Returns:
        (namedTuple[Host(os, arch, bit)]): Host(os=OS Type, arch=System Architecture, bit=Highest Order Bit)
    """
    Host = namedtuple('Host', 'os arch bit')
    host_info = platform.uname()
    os = host_info.system
    processor_info = host_info.machine

    arch = None
    bit = None

    if ("x86" in processor_info.lower()) or ("AMD" in processor_info.upper()) or ("INTEL" in processor_info.upper()):
        arch = "x86"
    elif ("ARM" in processor_info.upper()) or ("AARCH" in processor_info.upper()):
        arch = "ARM"

    if "32" in processor_info:
        bit = "32"
    elif "64" in processor_info:
        bit = "64"

    if (arch is None) or (bit is None):
        raise EnvironmentError("Host info could not be parsed: {0}".format(str(host_info)))

    return Host(os=os, arch=arch, bit=bit)


def timing(f):
    """This is a mixing to do timing on a function.

    Example:
        ```
            @timing
            def function_i_want_to_time():
        ```
    """
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        logging.debug('{:s} function took {:.3f} ms'.format(f.__name__, (time2 - time1) * 1000.0))
        return ret
    return wrap


def RunCmd(cmd, parameters, capture=True, workingdir=None, outfile=None, outstream=None, environ=None,
           logging_level=logging.INFO, raise_exception_on_nonzero=False, encodingErrors='strict',
           close_fds=True):
    """Run a shell command and print the output to the log file.

    This is the public function that should be used to run commands from the shell in python environment

    Attributes:
        cmd (str): command being run, either quoted or not quoted
        parameters (str): parameters string taken as is
        capture (obj): boolean to determine if caller wants the output captured
            in any format.
        workingdir (str): path to set to the working directory before running
            the command.
        outfile (obj): capture output to file of given path.
        outstream (obj): capture output to a stream.
        environ (obj): shell environment variables dictionary that replaces the
            one inherited from the current process.
        logging_level (obj): log level to log output at.  Default is INFO
        raise_exception_on_nonzero (bool): Setting to true causes exception to
            be raised if the cmd return code is not zero.
        encodingErrors (str): may be given to set the desired error handling
            for encoding errors decoding cmd output. Default is 'strict'.
        close_fds (bool): If True, file descriptors are closed before the
            command is run. Default is True.

    Returns:
        (int): returncode of called cmd
    """
    cmd = cmd.strip('"\'')
    if " " in cmd:
        cmd = '"' + cmd + '"'
    if parameters is not None:
        parameters = parameters.strip()
        cmd += " " + parameters
    starttime = datetime.datetime.now()
    logging.log(logging_level, "Cmd to run is: " + cmd)
    logging.log(logging_level, "------------------------------------------------")
    logging.log(logging_level, "--------------Cmd Output Starting---------------")
    logging.log(logging_level, "------------------------------------------------")
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         cwd=workingdir, shell=True, env=environ, close_fds=close_fds)
    if (capture):
        thread = PropagatingThread(target=reader, args=(outfile, outstream, c.stdout, logging_level, encodingErrors))
        thread.start()
        c.wait()
        thread.join()
    else:
        c.wait()

    endtime = datetime.datetime.now()
    delta = endtime - starttime
    endtime_str = "{0[0]:02}:{0[1]:02}".format(divmod(delta.seconds, 60))
    returncode_str = "{0:#010x}".format(c.returncode)
    logging.log(logging_level, "------------------------------------------------")
    logging.log(logging_level, "--------------Cmd Output Finished---------------")
    logging.log(logging_level, "--------- Running Time (mm:ss): " + endtime_str + " ----------")
    logging.log(logging_level, "----------- Return Code: " + returncode_str + " ------------")
    logging.log(logging_level, "------------------------------------------------")

    if raise_exception_on_nonzero and c.returncode != 0:
        raise Exception("{0} failed with Return Code: {1}".format(cmd, returncode_str))
    return c.returncode


def RunPythonScript(pythonfile, params, capture=True, workingdir=None, outfile=None, outstream=None,
                    environ=None, logging_level=logging.INFO, raise_exception_on_nonzero=False):
    """Run a python script and print the output to the log file.

    This is the public function that should be used to execute python scripts from the shell in python environment.
    The python script will be located using the path as if it was an executable.

    Attributes:
        cmd: cmd string to run including parameters
        capture: boolean to determine if caller wants the output captured in any format.
        workingdir: path to set to the working directory before running the command.
        outfile: capture output to file of given path.
        outstream: capture output to a stream.
        environ: shell environment variables dictionary that replaces the one inherited from the current process.

    Returns:
        (int): returncode of called cmd
    """
    # locate python file on path
    pythonfile.strip('"\'')
    if " " in pythonfile:
        pythonfile = '"' + pythonfile + '"'
    params.strip()
    logging.debug("RunPythonScript: {0} {1}".format(pythonfile, params))
    if (os.path.isabs(pythonfile)):
        logging.debug("Python Script was given as absolute path: %s" % pythonfile)
    elif (os.path.isfile(os.path.join(os.getcwd(), pythonfile))):
        pythonfile = os.path.join(os.getcwd(), pythonfile)
        logging.debug("Python Script was given as relative path: %s" % pythonfile)
    else:
        # loop thru path environment variable
        for a in os.getenv("PATH").split(os.pathsep):
            a = os.path.normpath(a)
            if os.path.isfile(os.path.join(a, pythonfile)):
                pythonfile = os.path.join(a, pythonfile)
                logging.debug("Python Script was found on the path: %s" % pythonfile)
                break
    params = pythonfile + " " + params
    return RunCmd(sys.executable, params, capture=capture, workingdir=workingdir, outfile=outfile,
                  outstream=outstream, environ=environ, logging_level=logging_level,
                  raise_exception_on_nonzero=raise_exception_on_nonzero)


def DetachedSignWithSignTool(SignToolPath, ToSignFilePath, SignatureOutputFile, PfxFilePath,
                             PfxPass=None, Oid="1.2.840.113549.1.7.2", Eku=None):
    """Locally Sign input file using Windows SDK signtool.

    This will use a local Pfx file.
    WARNING: This should not be used for production signing as that process should follow stronger
        security practices (HSM / smart cards / etc)

    Signing is in format specified by UEFI authentacted variables
    """
    # check signtool path
    if not os.path.exists(SignToolPath):
        logging.error("Path to signtool invalid.  %s" % SignToolPath)
        return -1

    # Adjust for spaces in the path (when calling the command).
    if " " in SignToolPath:
        SignToolPath = '"' + SignToolPath + '"'

    OutputDir = os.path.dirname(SignatureOutputFile)
    # Signtool docs https://docs.microsoft.com/en-us/dotnet/framework/tools/signtool-exe
    # Signtool parameters from
    #   https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/secure-boot-key-generation-and-signing-using-hsm--example  # noqa: E501
    # Search for "Secure Boot Key Generation and Signing Using HSM"
    params = 'sign /fd sha256 /p7ce DetachedSignedData /p7co ' + Oid + ' /p7 "' + \
             OutputDir + '" /f "' + PfxFilePath + '"'
    if Eku is not None:
        params += ' /u ' + Eku
    if PfxPass is not None:
        # add password if set
        params = params + ' /p ' + PfxPass
    params = params + ' /debug /v "' + ToSignFilePath + '" '
    ret = RunCmd(SignToolPath, params)
    if (ret != 0):
        logging.error("Signtool failed %d" % ret)
        return ret
    signedfile = os.path.join(OutputDir, os.path.basename(ToSignFilePath) + ".p7")
    if (not os.path.isfile(signedfile)):
        raise Exception("Output file doesn't exist %s" % signedfile)

    shutil.move(signedfile, SignatureOutputFile)
    return ret


def CatalogSignWithSignTool(SignToolPath, ToSignFilePath, PfxFilePath, PfxPass=None):
    """Locally sign input file using Windows SDK signtool.

    This will use a local Pfx file.

    WARNING: This should not be used for production signing as that process should follow
        stronger security practices (HSM / smart cards / etc)

    Signing is catalog format which is an attached signature
    """
    # check signtool path
    if not os.path.exists(SignToolPath):
        logging.error("Path to signtool invalid.  %s" % SignToolPath)
        return -1

    # Adjust for spaces in the path (when calling the command).
    if " " in SignToolPath:
        SignToolPath = '"' + SignToolPath + '"'

    OutputDir = os.path.dirname(ToSignFilePath)
    # Signtool docs https://docs.microsoft.com/en-us/dotnet/framework/tools/signtool-exe
    # todo: link to catalog signing documentation
    params = "sign /a /fd SHA256 /f " + PfxFilePath
    if PfxPass is not None:
        # add password if set
        params = params + ' /p ' + PfxPass
    params = params + ' /debug /v "' + ToSignFilePath + '" '
    ret = RunCmd(SignToolPath, params, workingdir=OutputDir)
    if (ret != 0):
        logging.error("Signtool failed %d" % ret)
    return ret


# Simplified Comparison Function borrowed from StackOverflow...
# https://stackoverflow.com/questions/1714027/version-number-comparison
# With Python 3.0 help from:
# https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons
def version_compare(version1, version2):
    """Compare two versions."""
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    (a, b) = (normalize(version1), normalize(version2))
    return (a > b) - (a < b)


def import_module_by_file_name(module_file_path):
    """Standard method of importing a Python file. Expecting absolute path."""
    module_name = os.path.basename(module_file_path)
    spec = importlib.util.spec_from_file_location(module_name, module_file_path)

    if spec is None:
        raise RuntimeError(f"Expected module file named {module_file_path}")

    ImportedModule = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ImportedModule)

    return ImportedModule


def locate_class_in_module(Module, DesiredClass):
    """Given a module and a class, this function will return the subclass of DesiredClass found in Module.

    It gives preference to classes that are defined in the module itself.
    This means that if you have an import that subclasses DesiredClass, it will be picked unless
    there is a class defined in the module that subclasses DesiredClass.

    In this hypothetical class hierarchy, GrandChildClass would be picked
    --------------      ------------      -----------------
    |DesiredClass|  ->  |ChildClass|  ->  |GrandChildClass|
    --------------      ------------      -----------------
    """
    DesiredClassInstance = None
    # Pull out the contents of the module that was provided
    module_contents = dir(Module)
    # Filter through the Module, we're only looking for classes.
    classList = [getattr(Module, obj) for obj in module_contents
                 if inspect.isclass(getattr(Module, obj))]

    for _class in classList:
        # Classes that the module import show up in this list too so we need
        # to make sure it's an INSTANCE of DesiredClass, not DesiredClass itself!
        # if multiple instances are found in the same class hierarchy, pick the
        # most specific one. If multiple instances are found belonging to different
        # class hierarchies, raise an error.
        if _class is not DesiredClass and issubclass(_class, DesiredClass):
            if (DesiredClassInstance is None) or issubclass(_class, DesiredClassInstance):
                DesiredClassInstance = _class
            elif not issubclass(DesiredClassInstance, _class):
                raise RuntimeError(f"Multiple instances were found:\n\t{DesiredClassInstance}\n\t{_class}")
    return DesiredClassInstance


def RemoveTree(dir_path: str, ignore_errors: bool = False) -> None:
    """Helper for removing a directory.

    On error try to change file attributes.  Also adds retry logic.

    Args:
        dir_path (str): Path to directory to remove.
        ignore_errors (bool): ignore errors during removal
    """
    # TODO actually make this private with _
    def remove_readonly(func, path, _):
        """Private function to attempt to change permissions on file/folder being deleted."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for _ in range(3):  # retry up to 3 times
        try:
            shutil.rmtree(dir_path, ignore_errors=ignore_errors, onerror=remove_readonly)
        except OSError as err:
            logging.warning(f"Failed to fully remove {dir_path}: {err}")
        else:
            break
    else:
        raise RuntimeError(f"Failed to remove {dir_path}")


def PrintByteList(ByteList, IncludeAscii=True, IncludeOffset=True, IncludeHexSep=True, OffsetStart=0, **kwargs):
    """Print a byte array as hex and optionally output ascii as well as offset within the buffer."""
    out_fs = kwargs.get("out_fs", sys.stdout)
    kwargs["include_ascii"] = IncludeAscii
    kwargs["include_hex_sep"] = IncludeHexSep
    kwargs["include_offset"] = IncludeOffset

    warn(
        "This function is being replaced by hexdump, if you rely on this behavior switch to hexdump",
        DeprecationWarning
    )
    hexdump(ByteList, offset_start=OffsetStart, out_fs=out_fs, **kwargs)


def hexdump(byte_list, offset_start=0, out_fs=sys.stdout, **kwargs) -> None:
    """Print a byte array as hex and optionally output ascii as well as offset within the buffer.

    Args:
        byte_list (bytearray): byte array to print
        offset_start (int): offset to print to the side of the hexdump
        out_fs (io.BytesIO): output file stream to print to

    Keyword Arguments:
        include_ascii (bool): Option (Default: True) to include ascii
        include_offset (bool): Option (Default: True) to include the offset
        include_hex_sep (bool): Option (Default: True) to include the hex seperator

    Returns:
        None
    """
    include_ascii = kwargs.get('include_ascii', True)
    include_offset = kwargs.get('include_offset', True)
    include_hex_sep = kwargs.get('include_hex_sep', True)

    ascii_string = ""
    index = 0

    for index, byte in enumerate(byte_list):
        # Start of New Line
        if index % 16 == 0 and include_offset:
            out_fs.write(f"{(index + offset_start):#04x} -")

        # Midpoint of a Line
        if index % 16 == 8 and include_hex_sep:
            out_fs.write(" -")

        # Print As Hex Byte
        out_fs.write(f" {byte:#04x}")

        # Prepare to Print As Ascii
        if byte < 0x20 or byte > 0x7E:
            ascii_string += "."
        else:
            ascii_string += f"{chr(byte)}"

        # End of Line
        if index % 16 == 15:
            if include_ascii:
                out_fs.write(f" {ascii_string} ")
            ascii_string = ""
            out_fs.write("\n")

    # Done - Lets check if we have partial
    if index % 16 != 15:
        # Lets print any partial line of ascii
        if include_ascii and ascii_string != "":
            # Pad out to the correct spot

            while index % 16 != 15:
                out_fs.write("     ")
                if index % 16 == 7:  # account for the - symbol in the hex dump
                    if include_offset:
                        out_fs.write("  ")
                index += 1
            # print the ascii partial line
            out_fs.write(f" {ascii_string} ")
            # print a single newline so that next print will be on new line
        out_fs.write("\n")


def export_c_type_array(buffer_fs, variable_name, out_fs, **kwargs) -> None:
    """Converts a given binary file to a UEFI typed C style array.

    Args:
        buffer_fs (io.BytesIO): buffer file stream to turn into a C style array
        variable_name (str): variable name to use for the C style array
        out_fs (io.StringIO): output filestream to write to

    Keyword Arguments:
        data_type (str): The datatype of the array (Default: UINT8)
        length_data_type (str): The datatype of the length field (Default: UINTN)
        is_array (bool): if true includes '[]' (Default: True)
        bytes_per_row (int): number of bytes to include per row (Default: 16)
        indent (str): the characters to use for indention (Default: '  ' (2 spaces))
        length_variable_name (str): name to use for the length variable
        include_ascii (bool): includes a ascii comment to side of hex
        include_length (bool): includes length in the decleration of array
            (ex. "UINT8 TestVariable[13] = {")
    Return:
         None

    Raises:
        ValueError: Binary file length was 0
    """
    data_type = kwargs.get("data_type", "UINT8")
    length_data_type = kwargs.get("length_data_type", "UINTN")
    bytes_per_row = kwargs.get("bytes_per_row", 16)
    indent = kwargs.get("indent", "    ")
    include_ascii = kwargs.get("include_ascii", True)
    include_length = kwargs.get("include_length", True)
    length_variable_name = kwargs.get("length_variable_name", None)

    start = buffer_fs.tell()
    buffer_fs.seek(0, 2)
    end = buffer_fs.tell()
    buffer_fs.seek(start)
    length = end - start

    # for some reason os.linesep causes twice the amount of desired newlines
    newline = '\n'

    if length == 0:
        raise ValueError("Binary file length was 0")

    length_value = ""
    if include_length:
        length_value = str(length)

    out_fs.write(f"{data_type} {variable_name}[{length_value}] = {{")

    ascii_string = ""
    i = 0
    byte = ''

    for i, byte in enumerate(buffer_fs.read()):
        if i % bytes_per_row == 0:
            if i != 0 and include_ascii:
                # An ending space is required because the '\' character will cause a line cont.
                out_fs.write(f" // {ascii_string} ")
                ascii_string = ""
            out_fs.write(f"{newline}{indent}")

        out_fs.write(f"{byte:#04x}")

        if byte < 0x20 or byte > 0x7E:
            ascii_string += "."
        else:
            ascii_string += f"{chr(byte)}"

        if i != length - 1:
            out_fs.write(", ")

    # pad out the remaining space
    if include_ascii:
        # bytes_per_row - 1 because indexes at 0
        # subtract the number of bytes we printed
        # now we know how many bytes we could have printed
        potential_bytes = (bytes_per_row - 1) - (i % bytes_per_row)

        # pad out the number of bytes by our byte length
        # use whatever was left over in byte
        byte_length = len(f" {byte:#04x},")

        # pad out the the line
        out_fs.write(" " * potential_bytes * byte_length)

        # make up for the trailing ',' and print a comment
        # An ending space is required because the '\' character will cause a line cont.
        out_fs.write(f"   // {ascii_string} ")

    out_fs.write(f"{newline}}};{newline*2}")

    if length_variable_name:
        out_fs.write(
            f"{length_data_type} {length_variable_name} = sizeof {variable_name};{newline*2}")
