# @file BaseParser.py
# Code to support parsing EDK2 files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to support parsing EDK2 files."""
import logging
import os
from warnings import warn

from edk2toollib.uefi.edk2 import path_utilities


class BaseParser(object):
    """Base Parser for other parser objects.

    Attributes:
        Parsed (bool): If a file has been parsed or not
        Lines (list): order list of lines in the file
        LocalVars (dict): Dict of local variables
        InputVars (dict): Dict of Input variables
        ConditionalStack (list): list of current condition expressions
        RootPath (str): Workspace root
        PPs (list): List of PPs
        TargetFilePath (list): file being parsed
    """
    operators = ["OR", "AND", "IN", "==", "!=", ">", "<", "<=", ">="]

    def __init__(self, log="BaseParser"):
        """Inits an empty Parser."""
        self.Logger = logging.getLogger(log)
        self.Lines = []
        self.LocalVars = {}
        self.InputVars = {}
        self.CurrentSection = ""
        self.CurrentFullSection = ""
        self.Parsed = False
        self.ConditionalStack = []
        self.RootPath = ""
        self.PPs = []
        self._Edk2PathUtil = None
        self.TargetFilePath = None  # the abs path of the target file
        self.FilePathStack = []  # a stack containing a tuple of a file, and lines left to parse in that file
        self.ParsedFiles = set()
        self.CurrentLine = -1
        self._MacroNotDefinedValue = "0"  # value to used for undefined macro

    #
    # For include files set the base root path
    #

    def SetEdk2Path(self, pathobj: path_utilities.Edk2Path):
        """Sets the internal attribute Edk2PathUtil.

        !!! note
            This is a drop in replacement for SetBaseAbsPath and SetPackagePaths as it will asssign both RootPath
            and PPs using the Edk2Path object attributes WorkspacePath and PackagePathList respectively.

        SetBaseAbsPath/SetPackagePaths integration instructions:

        ```python
        # Previous Way
        parser = BaseParser()
        parser.SetBaseAbsPath(path)
        parser.SetPackagePaths(pps)
        ```

        ```python
        # Integration
        parser = BaseParser()
        parser.SetEdk2Path(Edk2Path(path, pps))
        ```

        ```python
        # Integrate with no pps
        parser = BaseParser()
        parser.SetEdk2Path(Edk2Path(path, []))

        Args:
          pathobj (Edk2Path): Edk2Path object

        Returns:
            (BaseParser): self
        """
        self.RootPath = pathobj.WorkspacePath
        self.PPs = pathobj.PackagePathList
        self._Edk2PathUtil = pathobj
        return self

    def SetBaseAbsPath(self, path):
        """Sets the attribute RootPath.

        Args:
          path (str): Abs root path

        Returns:
            (BaseParser): self
        """
        warn("SetBaseAbsPath is deprecated.  Use SetEdk2Path instead", DeprecationWarning)
        self.RootPath = os.path.abspath(path)
        self._ConfigEdk2PathUtil()
        return self

    def _ConfigEdk2PathUtil(self):
        """Creates the path utility object based on the root path and package paths."""
        self._Edk2PathUtil = path_utilities.Edk2Path(self.RootPath, self.PPs, error_on_invalid_pp=False)

    def SetPackagePaths(self, pps=[]):
        """Sets the attribute PPs.

        Args:
          pps (:obj:`list`, optional): list of pps

        NOTE: This must be called after SetBaseAbsPath

        Returns:
            (BaseParser): self
        """
        warn("SetPackagePaths is deprecated.  Use SetEdk2Path instead", DeprecationWarning)
        self.PPs = pps
        self._ConfigEdk2PathUtil()
        return self

    def SetInputVars(self, inputdict):
        """Sets the attribute InputVars.

        Args:
          inputdict (dict): The input vars dictionary

        Returns:
            (BaseParser): self
        """
        self.InputVars = inputdict
        return self

    def PushTargetFile(self, abs_path, line_count):
        """Adds a target file to the stack."""
        self.FilePathStack.append((abs_path, line_count))
        self.ParsedFiles.add(abs_path)

    def DecrementLinesParsed(self) -> bool:
        """Decrements line count for the current target file by one.

        Returns:
            (bool): True if there are still lines to parse, False otherwise.
        """
        if not self.FilePathStack:
            return False
        (abs_path, line_count) = self.FilePathStack[-1]
        if line_count - 1 > 0:
            self.FilePathStack[-1] = (abs_path, line_count - 1)
            return True

        self.FilePathStack.pop()
        return False

    def FindPath(self, *p):
        """Given a path, it will find it relative to the root, the current target file, or the packages path.

        Args:
          *p (obj): any number of strings or path like objects

        Returns:
            (str): a full absolute path if the file exists
            (None): None on failure

        """
        # check if we're getting a None
        if p is None or (len(p) == 1 and p[0] is None):
            return None

        Path = os.path.join(*p)
        # check if it it is absolute
        if os.path.isabs(Path) and os.path.exists(Path):
            return Path

        # If the absolute path exists, return it.
        Path = os.path.join(self.RootPath, *p)
        if os.path.exists(Path):
            return os.path.abspath(Path)

        # If that fails, check a path relative to the target file.
        if self.FilePathStack:
            Path = os.path.abspath(os.path.join(os.path.dirname(self.FilePathStack[-1][0]), *p))
            if os.path.exists(Path):
                return os.path.abspath(Path)

        # If that fails, check in every possible Pkg path.
        if self._Edk2PathUtil is not None:
            target_path = os.path.join(*p)
            Path = self._Edk2PathUtil.GetAbsolutePathOnThisSystemFromEdk2RelativePath(target_path, log_errors=False)
            if Path is not None:
                return Path

        # log invalid file path
        self.Logger.error(f"Invalid file path: {p}")
        return None

    def WriteLinesToFile(self, filepath):
        """Write all parsed lines to a file.

        Args:
          filepath (str): path to an unopened file
        """
        self.Logger.debug("Writing all lines to file: %s" % filepath)
        file_handle = open(filepath, "w")
        for line in self.Lines:
            file_handle.write(line + "\n")
        file_handle.close()

    def ComputeResult(self, value, cond, value2):
        """Compute a logical comaprison.

        Args:
          value (str, int): First value
          cond (str): comparison to do
          value2 (str, int): Second value

        Returns:
            (bool): result of comparison
        """
        ivalue = value
        ivalue2 = value2
        if isinstance(value, str):
            ivalue = value.strip("\"")
        if isinstance(value2, str):
            ivalue2 = value2.strip("\"")

        # convert it to interpretted value
        if (cond.upper() == "IN"):
            # strip quotes
            self.Logger.debug(f"{ivalue} in {ivalue2}")

            return ivalue in ivalue2

        try:
            ivalue = self.ConvertToInt(ivalue)
        except ValueError:
            pass
        try:
            if (cond.lower() == "in"):
                ivalue2 = set(ivalue2.split())
            else:
                ivalue2 = self.ConvertToInt(ivalue2)
        except ValueError:
            pass

        # First check our boolean operators
        if (cond.upper() == "OR"):
            return ivalue or ivalue2
        if (cond.upper() == "AND"):
            return ivalue and ivalue2

        # check our truthyness
        if (cond == "=="):
            # equal
            return (ivalue == ivalue2) or (value == value2)

        elif (cond == "!="):
            # not equal
            return (ivalue != ivalue2) and (value != value2)

        # check to make sure we only have digits from here on out
        if (isinstance(value, str) and value.upper() in ["TRUE", "FALSE"]) \
            or (isinstance(value, str) and value2.upper() in ["TRUE", "FALSE"]):
            self.Logger.error(f"Invalid comparison: {value} {cond} {value2}")
            self.Logger.debug(f"Invalid comparison: {value} {cond} {value2}")
            raise ValueError("Invalid comparison")

        if not isinstance(ivalue, int) and not str.isdigit(value):
            self.Logger.error(f"{self.__class__}: Unknown value: {value} {ivalue.__class__}")
            self.Logger.debug(f"{self.__class__}: Conditional: {value} {cond}{value2}")
            raise ValueError("Unknown value")

        if not isinstance(ivalue2, int) and not str.isdigit(value2):
            self.Logger.error(f"{self.__class__}: Unknown value: {value2} {ivalue2}")
            self.Logger.debug(f"{self.__class__}: Conditional: {value} {cond} {value2}")
            raise ValueError("Unknown value")

        if (cond == "<"):
            return (ivalue < ivalue2)

        elif (cond == "<="):
            return (ivalue <= ivalue2)

        elif (cond == ">"):
            return (ivalue > ivalue2)

        elif (cond == ">="):
            return (ivalue >= ivalue2)

        else:
            self.Logger.error(f"{self.__class__}: Unknown conditional: {cond}")
            raise RuntimeError("Unknown conditional")

    def ConvertToInt(self, value):
        """Converts a str or int to an int based on prefix.

        Args:
          value (str, int): value to convert

        Returns:
            (int): Converted value
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.upper() == "TRUE":
            return 1
        elif isinstance(value, str) and value.upper() == "FALSE":
            return 0
        elif isinstance(value, str) and value.upper().startswith("0X"):
            return int(value, 16)
        else:
            return int(value, 10)

    def PushConditional(self, v: bool, already_true: bool = False):
        """Push new value onto the conditional stack.

        Args:
          v (bool): Value to push
          already_true (bool): A boolean that specifies if this condition
            (if/elseif/else) block has already been true.

        !!! note
            already_true is needed when calling PopConditional() to know if the next
            part of the conditional block needs evaluated or not.

        """
        self.ConditionalStack.append((v, already_true))

    def PopConditional(self):
        """Pops the current conditional and return the value.

        Additionally returns a value specifying if the if/elseif/else block has already
        returned true.  This is needed to know if the next part of the conditional block
        needs evaluated or not.

        Returns (bool, bool): (value, already_true)
        """
        if (len(self.ConditionalStack) > 0):
            return self.ConditionalStack.pop()
        else:
            self.Logger.critical("Tried to pop an empty conditional stack.  Line Number %d" % self.CurrentLine)
            return self.ConditionalStack.pop()  # this should cause a crash but will give trace.

    def _FindReplacementForToken(self, token, replace_if_not_found=False):

        v = self.LocalVars.get(token)

        if (v is None):
            v = self.InputVars.get(token)

        if (v is None and replace_if_not_found):
            v = self._MacroNotDefinedValue

        elif (v is None):
            return None

        if (isinstance(v, bool)):
            v = "true" if v else "false"

        if (isinstance(v, str) and (v.upper() == "TRUE" or v.upper() == "FALSE")):
            v = v.upper()

        return str(v)

    def ReplaceVariables(self, line):
        """Replaces a variable in a string.

        Args:
          line (str): The line to process

        Returns:
            (str): The line with the replaced variable.
        """
        # first tokenize and look for tokens require special macro
        # handling without $.  This must be done first otherwise
        # both syntax options can not be supported.
        result = line
        tokens = result.split()
        replace = len(tokens) > 1 and tokens[0].lower() in ["!ifdef", "!ifndef", "!if", "!elseif"]
        if len(tokens) > 1 and tokens[0].lower() in ["!ifdef", "!ifndef"]:
            if not tokens[1].startswith("$("):
                v = self._FindReplacementForToken(tokens[1], replace)
                if v is not None:
                    result = result.replace(tokens[1], v, 1)

        # use line to avoid change by handling above
        rep = line.count("$")
        index = 0
        while (rep > 0):
            start = line.find("$(", index)
            end = line.find(")", start)

            token = line[start + 2:end]
            replacement_token = line[start:end + 1]
            self.Logger.debug("Token is %s" % token)
            v = self._FindReplacementForToken(token, replace)
            if v is not None:
                result = result.replace(replacement_token, v, 1)

            index = end + 1
            rep = rep - 1

        return result

    def ProcessConditional(self, text):
        """Processes a conditional.

        Args:
          text (str): The text to process

        Returns:
            (bool): true if a line is a conditiona otherwise false
        """
        if '"' in text:
            tokens = text.split('"')
            tokens = tokens[0].split() + [tokens[1]] + tokens[2].split()
        else:
            tokens = text.split()
        if (tokens[0].lower() == "!if"):
            result = self.EvaluateConditional(text)
            self.PushConditional(result, result)
            return True

        elif (tokens[0].lower() == "!elseif"):
            if not self.InActiveCode():
                (_, already_been_true) = self.PopConditional()

                if already_been_true:
                    self.PushConditional(False, True)
                else:
                    result = self.EvaluateConditional(text)
                    self.PushConditional(result, result)
            # already in active code, i.e. the previous if/elseif was true
            else:
                self.PopConditional()
                self.PushConditional(False, True)
            return True

        elif (tokens[0].lower() == "!ifdef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1] != self._MacroNotDefinedValue))
            return True

        elif (tokens[0].lower() == "!ifndef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1] == self._MacroNotDefinedValue))
            return True

        elif (tokens[0].lower() == "!else"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            (value, already_been_true) = self.PopConditional()
            # TODO make sure we can't do multiple else statements

            # If we've already hit a true condition, we need to be false,
            # otherwise, lets process!
            if already_been_true:
                self.PushConditional(False, True)
            else:
                self.PushConditional(True, True)
            return True

        elif (tokens[0].lower() == "!endif"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PopConditional()
            return True

        return False

    def EvaluateConditional(self, text):
        """Uses a pushdown resolver."""
        text = str(text).strip()
        if text.lower().startswith("!if "):
            text = text[3:].strip()
        elif text.lower().startswith("!elseif "):
            text = text[7:].strip()
        else:
            raise RuntimeError(f"Invalid conditional cannot be validated: {text}")

        self.Logger.debug(f"STAGE 1: {text}")
        text = self.ReplaceVariables(text)
        self.Logger.debug(f"STAGE 2: {text}")
        tokens = self._TokenizeConditional(text)
        self.Logger.debug(f"STAGE 3: {tokens}")
        expression = self._ConvertTokensToPostFix(tokens)
        self.Logger.debug(f"STAGE 4: {expression}")

        # Now we evaluate the post fix expression
        if len(expression) == 0:
            raise RuntimeError(f"Malformed !if conditional expression {text} {expression}")
        while len(expression) != 1:
            first_operand_index = -1
            # find the first operator
            for index, item in enumerate(expression):
                if self._IsOperator(item):
                    first_operand_index = index
                    break
            if first_operand_index == -1:
                raise RuntimeError(f"We didn't find an operator to execute in {expression}: {text}")
            operand = expression[first_operand_index]

            if operand == "NOT":
                # Special logic for handling the not
                if first_operand_index < 1:
                    raise RuntimeError(f"We have a stray operand {operand}")
                # grab the operand right before the NOT and invert it
                operator1_raw = expression[first_operand_index - 1]
                operator1 = self.ConvertToInt(operator1_raw)
                result = not operator1
                # grab what was before the operator and the operand, then squish it all together
                new_expression = expression[:first_operand_index - 1] if first_operand_index > 1 else []
                new_expression += [result, ] + expression[first_operand_index + 1:]
                expression = new_expression
            else:
                if first_operand_index < 2:
                    raise RuntimeError(f"We have a stray operand {operand}")
                operator1 = expression[first_operand_index - 2]
                operator2 = expression[first_operand_index - 1]

                do_invert = False
                # check if we have a special operator that has a combined not on it
                if str(operand).startswith("!+"):
                    operand = operand[2:]
                    do_invert = True
                # compute the result now that we have the three things we need
                result = self.ComputeResult(operator1, operand, operator2)

                if do_invert:
                    result = not result
                # grab what was before the operator and the operand, then smoosh it all together
                new_expression = expression[:first_operand_index - 2] if first_operand_index > 2 else []
                new_expression += [result, ] + expression[first_operand_index + 1:]
                expression = new_expression

        final = self.ConvertToInt(expression[0])
        self.Logger.debug(f" FINAL {expression} {final}")

        return bool(final)

    @classmethod
    def _TokenizeConditional(cls, text):
        """Takes in a string that has macros replaced."""
        # TOKENIZER
        # first we create tokens
        TEXT_MODE = 0
        QUOTE_MODE = 1
        MACRO_MODE = 2
        token = ""
        mode = 0
        tokens = []
        for character in text:
            if character == "\"" and len(token) == 0:
                mode = QUOTE_MODE
            elif character == "\"" and mode == QUOTE_MODE:
                if len(token) > 0:
                    tokens.append(f"\"{token}\"")
                    token = ""
                mode = TEXT_MODE
            elif character == "$" and len(token) == 0:
                token += character
                mode = MACRO_MODE
            elif character == ')' and mode == MACRO_MODE:
                token += character
                tokens.append(token)
                token = ""
                mode = TEXT_MODE
            elif mode == TEXT_MODE and (character == "(" or character == ")"):
                if len(token) > 0:
                    tokens.append(token)
                    token = ""
                tokens.append(character)
            elif character == " " and (mode == TEXT_MODE or mode == MACRO_MODE):
                if len(token) > 0:
                    tokens.append(token)
                    token = ""
                    mode = TEXT_MODE
            else:
                token += character
        # make sure to add in the last token just in case
        if len(token) > 0:
            tokens.append(token)

        # then we do the lexer and convert operands as necessary
        for index in range(len(tokens)):
            token = tokens[index]
            token_upper = token.upper()
            if token_upper in cls.operators:
                token = token_upper
            elif token_upper == "||":
                token = "OR"
            elif token_upper == "&&":
                token = "AND"
            elif token_upper == "EQ":
                token = "=="
            elif token_upper == "NE":
                token = "!="
            elif token == "!":
                token = "NOT"
            tokens[index] = token

        # collapse the not
        collapsed_tokens = []
        found_not = False
        for token in tokens:
            if str(token).upper() == "NOT":
                found_not = True
                continue
            if not found_not:
                collapsed_tokens.append(token)
            elif token in cls.operators:
                collapsed_tokens.append("!+" + token)
                found_not = False
            else:  # add the not back
                found_not = False
                collapsed_tokens.append("NOT")
                collapsed_tokens.append(token)

        return collapsed_tokens

    @classmethod
    def _ConvertTokensToPostFix(cls, tokens):
        # convert infix into post fix
        stack = ["("]
        tokens.append(")")  # add an extra parathesis
        expression = []
        for token in tokens:
            # If the incoming symbol is a left parenthesis, push it on the stack.
            if token == "(":
                stack.append(token)
            # If the incoming symbol is a right parenthesis,
            # pop the stack and print the operators until you see a left parenthesis.
            # Discard the pair of parentheses.
            elif token == ")":
                while len(stack) > 0 and stack[-1] != '(':
                    expression.append(stack.pop())
                stack.pop()  # pop the last (
            # If this isn't a operator ignore it
            elif not cls._IsOperator(token):
                expression.append(token)
            # If the stack is empty or contains a left parenthesis on top, push the incoming operator onto the stack.
            elif len(stack) == 0 or stack[-1] == '(':
                stack.append(token)
            # If the incoming symbol has higher precedence than the top of the stack, push it on the stack.
            elif len(stack) == 0 or cls._GetOperatorPrecedence(token) > cls._GetOperatorPrecedence(stack[-1]):
                stack.append(token)
            # If the incoming symbol has equal precedence with the top of the stack, use association.
            # If the association is left to right, pop and print the top of the stack and
            # then push the incoming operator. If the association is right to left, push the incoming operator.
            elif len(stack) != 0 and cls._GetOperatorPrecedence(token) == cls._GetOperatorPrecedence(stack[-1]):
                expression.append(stack.pop())
                stack.append(token)
            # If the incoming symbol has lower precedence than the symbol on the top of the stack,
            # pop the stack and print the top operator.
            # Then test the incoming operator against the new top of stack.
            elif len(stack) != 0 and cls._GetOperatorPrecedence(token) < cls._GetOperatorPrecedence(stack[-1]):
                while len(stack) > 0 and cls._GetOperatorPrecedence(token) <= cls._GetOperatorPrecedence(stack[-1]):
                    expression.append(stack.pop())
                stack.append(token)
            else:
                logging.error("We don't know what to do with " + token)
        while len(stack) > 0:
            val = stack.pop()
            expression.append(val)
        return expression

    @classmethod
    def _IsOperator(cls, token):
        if not isinstance(token, str):
            return False
        if token.startswith("!+"):
            token = token[2:]
        if token == "NOT":  # technically an operator
            return True
        return token in cls.operators

    @classmethod
    def _GetOperatorPrecedence(cls, token):
        if not cls._IsOperator(token):
            return -1
        if token == "(" or token == ")":
            return 100
        if token == "NOT":  # not is the lowest
            return -2
        if token == "IN":
            return 1
        return 0

    def InActiveCode(self):
        """Determines what the state of the conditional you are currently in.

        Returns:
            (bool): result of the state of the conditional you are in.
        """
        ret = True
        for (a, _) in self.ConditionalStack:
            if not a:
                ret = False
                break

        return ret

    def IsGuidString(self, line):
        """Determines if a line is a guid string.

        Args:
            line (str): line representing a possible guid string

        Returns:
            (bool): whether the string is a guid string

        NOTE: format = { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
        Will return true if the the line has
        """
        if (line.count("{") == 2 and line.count("}") == 2 and line.count(",") == 10 and line.count("=") == 1):
            return True
        return False

    def ParseGuid(self, line):
        """Parse a guid into a different format.

        Args:
          line (str): the guid to parse ex:
            { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}

        Returns:
            (str): guid. ex: D3B36F2C-D551-11D4-9A46-0090273FC14D

        Raises:
            (RuntimeError): if missing any of the 11 parts, or it isn't long enough.
        """
        entries = line.lstrip(' {').rstrip(' }').split(',')
        if len(entries) != 11:
            raise RuntimeError(
                f"Invalid GUID found {line}. We are missing some parts since we only found: {len(entries)}")
        gu = entries[0].lstrip(' 0').lstrip('x').strip()
        # pad front until 8 chars
        while (len(gu) < 8):
            gu = "0" + gu

        gut = entries[1].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[2].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        # strip off extra {
        gut = entries[3].lstrip(' { 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[4].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[5].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[6].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[7].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[8].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[9].lstrip(' 0').lstrip('x').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[10].split()[0].lstrip(' 0').lstrip('x').rstrip(' } ').strip()
        while (len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        proper_guid_length = 36
        if len(gu) > proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too long: {gu}")
        if len(gu) < proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too short: {gu}")

        return gu.upper()

    def ResetParserState(self):
        """Resets the state of the parser."""
        self.ConditionalStack = []
        self.CurrentSection = ''
        self.CurrentFullSection = ''
        self.FilePathStack = []
        self.Parsed = False


class HashFileParser(BaseParser):
    """Base class for Edk2 build files that use # for comments."""

    def __init__(self, log):
        """Inits an empty Parser for files that use # for comments.."""
        BaseParser.__init__(self, log)

    def StripComment(self, line):
        """Removes a comment from a line.

        Args:
          line (str): line with a comment (#)
        """
        if "#" not in line:
            return line.strip()

        result = []
        inside_quotes = False
        quote_char = None
        escaped = False

        for char in line:
            if char in ('"', "'") and not escaped:
                if not inside_quotes:
                    inside_quotes = True
                    quote_char = char
                elif char == quote_char:
                    inside_quotes = False
                    quote_char = None
            elif char == '#' and not inside_quotes:
                break
            elif char == '\\' and not escaped:
                escaped = True
            else:
                escaped = False

            result.append(char)

        return ''.join(result).rstrip()

    def ParseNewSection(self, line):
        """Parses a new section line.

        Args:
          line (str): line representing a new section.
        """
        if (line.count("[") == 1 and line.count("]") == 1):  # new section
            section = line.strip().lstrip("[").split(".")[0].split(",")[0].rstrip("]").strip()
            self.CurrentFullSection = line.strip().lstrip("[").split(",")[0].rstrip("]").strip()
            return (True, section)
        return (False, "")
