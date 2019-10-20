##
# Handle basic logging with color via ANSI commands
# Will call into win32 commands as needed when needed
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import logging
import re
from edk2toollib.utility_functions import GetHostInfo
try:
    # try to import windows types from winDLL
    import ctypes
    from ctypes import LibraryLoader
    windll = LibraryLoader(ctypes.WinDLL)
    from ctypes import wintypes
except (AttributeError, ImportError):
    # if we run into an exception (ie on unix or linux)
    windll = None

    # create blank lambda
    def SetConsoleTextAttribute():
        None

    # create blank lambda
    def winapi_test():
        None

else:
    # if we don't raise an exception when we import windows types
    # then execute this but don't catch an exception if raised
    from ctypes import byref, Structure

    # inspired by https://github.com/tartley/colorama/
    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
        COORD = wintypes._COORD
        """struct in wincon.h."""
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]

        def __str__(self):
            return '(%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)' % (
                self.dwSize.Y, self.dwSize.X,
                self.dwCursorPosition.Y, self.dwCursorPosition.X,
                self.wAttributes,
                self.srWindow.Top, self.srWindow.Left,
                self.srWindow.Bottom, self.srWindow.Right,
                self.dwMaximumWindowSize.Y, self.dwMaximumWindowSize.X
            )

    # a simple wrapper around the few methods calls to windows
    class Win32Console(object):
        _GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
        _SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
        _SetConsoleTextAttribute.argtypes = [
            wintypes.HANDLE,
            wintypes.WORD,
        ]
        _SetConsoleTextAttribute.restype = wintypes.BOOL
        _GetStdHandle = windll.kernel32.GetStdHandle
        _GetStdHandle.argtypes = [
            wintypes.DWORD,
        ]
        _GetStdHandle.restype = wintypes.HANDLE

        # from winbase.h
        STDOUT = -11
        STDERR = -12

        @staticmethod
        def _winapi_test(handle):
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            success = Win32Console._GetConsoleScreenBufferInfo(
                handle, byref(csbi))
            return bool(success)

        @staticmethod
        def winapi_test():
            return any(Win32Console._winapi_test(h) for h in
                       (Win32Console._GetStdHandle(Win32Console.STDOUT),
                        Win32Console._GetStdHandle(Win32Console.STDERR)))

        @staticmethod
        def GetConsoleScreenBufferInfo(stream_id=STDOUT):
            handle = Win32Console._GetStdHandle(stream_id)
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            Win32Console._GetConsoleScreenBufferInfo(
                handle, byref(csbi))
            return csbi

        @staticmethod
        def SetConsoleTextAttribute(stream_id, attrs):
            handle = Win32Console._GetStdHandle(stream_id)
            return Win32Console._SetConsoleTextAttribute(handle, attrs)


# from wincon.h
class WinColor(object):
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    YELLOW = 6
    GREY = 7
    NORMAL = 0x00  # dim text, dim background
    BRIGHT = 0x08  # bright text, dim background
    BRIGHT_BACKGROUND = 0x80  # dim text, bright background


# defines the different codes for the ansi colors
class AnsiColor(object):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    RESET = 39
    LIGHTBLACK_EX = 90
    LIGHTRED_EX = 91
    LIGHTGREEN_EX = 92
    LIGHTYELLOW_EX = 93
    LIGHTBLUE_EX = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX = 96
    LIGHTWHITE_EX = 97
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_WHITE = 47
    BG_RESET = 49
    # These are fairly well supported, but not part of the standard.
    BG_LIGHTBLACK_EX = 100
    BG_LIGHTRED_EX = 101
    BG_LIGHTGREEN_EX = 102
    BG_LIGHTYELLOW_EX = 103
    BG_LIGHTBLUE_EX = 104
    BG_LIGHTMAGENTA_EX = 105
    BG_LIGHTCYAN_EX = 106
    BG_LIGHTWHITE_EX = 107

    @classmethod
    def __contains__(self, item):

        if type(item) is str and hasattr(self, item):
            return True
        # check if we contain the color number
        for attr_name in dir(self):
            if getattr(self, attr_name) is item:
                return True
        return False


# the formatter that outputs ANSI codes as needed
class ColoredFormatter(logging.Formatter):
    AZURE_COLORS = {
        'CRITICAL': "section",
        'ERROR': "error"
    }

    COLORS = {
        'WARNING': AnsiColor.YELLOW,
        'INFO': AnsiColor.CYAN,
        'DEBUG': AnsiColor.BLUE,
        'CRITICAL': AnsiColor.LIGHTWHITE_EX,
        'ERROR': AnsiColor.RED,
        "STATUS": AnsiColor.GREEN,
        "PROGRESS": AnsiColor.GREEN,
        "SECTION": AnsiColor.CYAN
    }

    def __init__(self, msg="", use_azure=False):
        logging.Formatter.__init__(self, msg)
        self.use_azure = use_azure

    def format(self, record):
        levelname = record.levelname
        org_message = record.msg

        if not self.use_azure and levelname in ColoredFormatter.COLORS:
            # just color the level name
            if record.levelno < logging.WARNING:
                levelname_color = get_ansi_string(ColoredFormatter.COLORS[levelname]) + levelname + get_ansi_string()
            # otherwise color the wholes message
            else:
                levelname_color = get_ansi_string(ColoredFormatter.COLORS[levelname]) + levelname
                record.msg += get_ansi_string()
            record.levelname = levelname_color

        if self.use_azure and levelname in ColoredFormatter.AZURE_COLORS:
            levelname_color = "##[" + \
                ColoredFormatter.AZURE_COLORS[levelname] + "]"
            record.levelname = levelname_color

        result = logging.Formatter.format(self, record)

        record.levelname = levelname
        record.msg = org_message
        return result


# returns the string formatted ANSI command for the specific color
def get_ansi_string(color=AnsiColor.RESET):
    CSI = '\033['
    colors = AnsiColor()
    if color not in colors:
        color = AnsiColor.RESET
    return CSI + str(color) + 'm'


class ColoredStreamHandler(logging.StreamHandler):

    # Control Sequence Introducer
    ANSI_CSI_RE = re.compile('\001?\033\\[((?:\\d|;)*)([a-zA-Z])\002?')

    def __init__(self, stream=None, strip=None, convert=None):
        logging.StreamHandler.__init__(self, stream)
        self.on_windows = GetHostInfo().os == "Windows"
        # We test if the WinAPI works, because even if we are on Windows
        # we may be using a terminal that doesn't support the WinAPI
        # (e.g. Cygwin Terminal). In this case it's up to the terminal
        # to support the ANSI codes.
        self.conversion_supported = (self.on_windows and Win32Console.winapi_test())
        self.strip = False
        # should we strip ANSI sequences from our output?
        if strip is None:
            strip = self.conversion_supported or (
                not self.stream.closed and not self.stream.isatty())
        self.strip = strip

        # should we should convert ANSI sequences into win32 calls?
        if convert is None:
            convert = (self.conversion_supported and not self.stream.closed and self.stream.isatty())
        self.convert = convert
        self.win32_calls = None

        if stream is not None:
            self.stream = stream

        if self.on_windows:
            self.win32_calls = self.get_win32_calls()
            self._light = 0
            self._default = Win32Console.GetConsoleScreenBufferInfo(
                Win32Console.STDOUT).wAttributes
            self.set_attrs(self._default)
            self._default_fore = self._fore
            self._default_back = self._back
            self._default_style = self._style

    def handle(self, record):
        """
        Conditionally emit the specified logging record.
        Emission depends on filters which may have been added to the handler.
        Wrap the actual emission of the record with acquisition/release of
        the I/O thread lock. Returns whether the filter passed the record for
        emission.
        """

        rv = self.filter(record)
        if rv and record.levelno >= self.level:
            self.acquire()
            try:
                self.emit(record)
            finally:
                self.release()
        return rv

    def get_win32_calls(self):
        if self.convert:
            return {
                AnsiColor.BLACK: (self.set_foreground, WinColor.BLACK),
                AnsiColor.RED: (self.set_foreground, WinColor.RED),
                AnsiColor.GREEN: (self.set_foreground, WinColor.GREEN),
                AnsiColor.YELLOW: (self.set_foreground, WinColor.YELLOW),
                AnsiColor.BLUE: (self.set_foreground, WinColor.BLUE),
                AnsiColor.MAGENTA: (self.set_foreground, WinColor.MAGENTA),
                AnsiColor.CYAN: (self.set_foreground, WinColor.CYAN),
                AnsiColor.WHITE: (self.set_foreground, WinColor.GREY),
                AnsiColor.RESET: (self.set_foreground, None),
                AnsiColor.LIGHTBLACK_EX: (self.set_foreground, WinColor.BLACK, True),
                AnsiColor.LIGHTRED_EX: (self.set_foreground, WinColor.RED, True),
                AnsiColor.LIGHTGREEN_EX: (self.set_foreground, WinColor.GREEN, True),
                AnsiColor.LIGHTYELLOW_EX: (self.set_foreground, WinColor.YELLOW, True),
                AnsiColor.LIGHTBLUE_EX: (self.set_foreground, WinColor.BLUE, True),
                AnsiColor.LIGHTMAGENTA_EX: (self.set_foreground, WinColor.MAGENTA, True),
                AnsiColor.LIGHTCYAN_EX: (self.set_foreground, WinColor.CYAN, True),
                AnsiColor.LIGHTWHITE_EX: (self.set_foreground, WinColor.GREY, True),
                AnsiColor.BG_BLACK: (self.set_background, WinColor.BLACK),
                AnsiColor.BG_RED: (self.set_background, WinColor.RED),
                AnsiColor.BG_GREEN: (self.set_background, WinColor.GREEN),
                AnsiColor.BG_YELLOW: (self.set_background, WinColor.YELLOW),
                AnsiColor.BG_BLUE: (self.set_background, WinColor.BLUE),
                AnsiColor.BG_MAGENTA: (self.set_background, WinColor.MAGENTA),
                AnsiColor.BG_CYAN: (self.set_background, WinColor.CYAN),
                AnsiColor.BG_WHITE: (self.set_background, WinColor.GREY),
                AnsiColor.BG_RESET: (self.set_background, None),
                AnsiColor.BG_LIGHTBLACK_EX: (self.set_background, WinColor.BLACK, True),
                AnsiColor.BG_LIGHTRED_EX: (self.set_background, WinColor.RED, True),
                AnsiColor.BG_LIGHTGREEN_EX: (self.set_background, WinColor.GREEN, True),
                AnsiColor.BG_LIGHTYELLOW_EX: (self.set_background, WinColor.YELLOW, True),
                AnsiColor.BG_LIGHTBLUE_EX: (self.set_background, WinColor.BLUE, True),
                AnsiColor.BG_LIGHTMAGENTA_EX: (self.set_background, WinColor.MAGENTA, True),
                AnsiColor.BG_LIGHTCYAN_EX: (self.set_background, WinColor.CYAN, True),
                AnsiColor.BG_LIGHTWHITE_EX: (self.set_background, WinColor.GREY, True),
            }
        return dict()

    # does the win32 call to set the foreground
    def set_foreground(self, fore=None, light=False, on_stderr=False):
        if fore is None:
            fore = self._default_fore
        self._fore = fore
        # Emulate LIGHT_EX with BRIGHT Style
        if light:
            self._light |= WinColor.BRIGHT
        else:
            self._light &= ~WinColor.BRIGHT
        self.set_console(on_stderr=on_stderr)

    # does the win32 call to see the background
    def set_background(self, back=None, light=False, on_stderr=False):
        if back is None:
            back = self._default_back
        self._back = back
        # Emulate LIGHT_EX with BRIGHT_BACKGROUND Style
        if light:
            self._light |= WinColor.BRIGHT_BACKGROUND
        else:
            self._light &= ~WinColor.BRIGHT_BACKGROUND
        self.set_console(on_stderr=on_stderr)

    # the win32 call to set the console text attribute
    def set_console(self, attrs=None, on_stderr=False):
        if attrs is None:
            attrs = self.get_attrs()
        handle = Win32Console.STDOUT
        if on_stderr:
            handle = Win32Console.STDERR
        Win32Console.SetConsoleTextAttribute(handle, attrs)

    # gets the current settings for the style and colors selected
    def get_attrs(self):
        return self._fore + self._back * 16 + (self._style | self._light)

    # sets the attributes for the style and colors selected
    def set_attrs(self, value):
        self._fore = value & 7
        self._back = (value >> 4) & 7
        self._style = value & (WinColor.BRIGHT | WinColor.BRIGHT_BACKGROUND)

    # writes to stream, stripping ANSI if specified
    def write(self, text):
        if self.strip or self.convert:
            self.write_and_convert(text)
        else:
            self.write_plain_text(text)

    # write the given text to the strip stripping and converting ANSI
    def write_and_convert(self, text):
        cursor = 0
        for match in self.ANSI_CSI_RE.finditer(text):
            start, end = match.span()
            if (cursor < start):
                self.write_plain_text(text, cursor, start)
            self.convert_ansi(*match.groups())
            cursor = end

        self.write_plain_text(text, cursor, len(text))

    # writes plain text to our stream
    def write_plain_text(self, text, start=None, end=None):
        if start is None:
            self.stream.write(text)
        elif start < end:
            self.stream.write(text[start:end])
        self.flush()

    # converts an ANSI command to a win32 command
    def convert_ansi(self, paramstring, command):
        if self.convert:
            params = self.extract_params(command, paramstring)
            self.call_win32(command, params)
    # extracts the parameters in the ANSI command

    def extract_params(self, command, paramstring):
        params = tuple(int(p) for p in paramstring.split(';') if len(p) != 0)
        if len(params) == 0:
            params = (0,)

        return params

    # calls the win32 apis set_foreground and set_background
    def call_win32(self, command, params):
        if command == 'm':
            for param in params:
                if param in self.win32_calls:
                    func_args = self.win32_calls[param]
                    func = func_args[0]
                    args = func_args[1:]
                    kwargs = dict()
                    func(*args, **kwargs)

    # logging.handler method we are overriding to emit a record
    def emit(self, record):
        try:
            if record is None:
                return
            msg = self.format(record)
            if msg is None:
                return
            self.write(str(msg))
            self.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)
