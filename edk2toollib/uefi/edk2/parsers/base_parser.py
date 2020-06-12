# @file BaseParser.py
# Code to support parsing EDK2 files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import os
import logging


class BaseParser(object):
    """ """
    operators = ["OR", "AND", "IN", "==", "!=", ">", "<", "<=", ">="]

    def __init__(self, log="BaseParser"):
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
        self.TargetFile = None
        self.TargetFilePath = None
        self.CurrentLine = -1
        self._MacroNotDefinedValue = "0"  # value to used for undefined macro

    #
    # For include files set the base root path
    #

    def SetBaseAbsPath(self, path):
        """

        Args:
          path:

        Returns:

        """
        self.RootPath = path
        return self

    def SetPackagePaths(self, pps=[]):
        """

        Args:
          pps:  (Default value = [])

        Returns:

        """
        self.PPs = pps
        return self

    def SetInputVars(self, inputdict):
        """

        Args:
          inputdict:

        Returns:

        """
        self.InputVars = inputdict
        return self

    def FindPath(self, *p):
        """

        Args:
          *p:

        Returns:

        """
        # NOTE: Some of this logic should be replaced
        #       with the path resolution from Edk2Module code.

        # If the absolute path exists, return it.
        Path = os.path.join(self.RootPath, *p)
        if os.path.exists(Path):
            return Path

        # If that fails, check a path relative to the target file.
        if self.TargetFilePath is not None:
            Path = os.path.join(self.TargetFilePath, *p)
            if os.path.exists(Path):
                return Path

        # If that fails, check in every possible Pkg path.
        for Pkg in self.PPs:
            Path = os.path.join(self.RootPath, Pkg, *p)
            if os.path.exists(Path):
                return Path

        # log invalid file path
        Path = os.path.join(self.RootPath, *p)
        self.Logger.error("Invalid file path %s" % Path)
        return Path

    def WriteLinesToFile(self, filepath):
        """

        Args:
          filepath:

        Returns:

        """
        self.Logger.debug("Writing all lines to file: %s" % filepath)
        file_handle = open(filepath, "w")
        for line in self.Lines:
            file_handle.write(line + "\n")
        file_handle.close()
    #
    # do logical comparisons
    #

    def ComputeResult(self, value, cond, value2):
        """

        Args:
          value:
          cond:
          value2:

        Returns:

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
            if(cond.lower() == "in"):
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
        if(cond == "=="):
            # equal
            return (ivalue == ivalue2) or (value == value2)

        elif (cond == "!="):
            # not equal
            return (ivalue != ivalue2) and (value != value2)

        # check to make sure we only have digits from here on out
        if not isinstance(value, int) and not str.isdigit(value):
            self.Logger.error(f"{self.__class__}: Unknown value: {value} {ivalue.__class__}")
            self.Logger.debug(f"{self.__class__}: Conditional: {value} {cond}{value2}")
            raise ValueError("Unknown value")

        if not isinstance(value2, int) and not str.isdigit(value2):
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

    #
    # convert to int based on prefix
    #

    def ConvertToInt(self, value):
        """

        Args:
          value: must be str or int

        Returns:

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

    #
    # Push new value on stack
    #
    def PushConditional(self, v):
        """

        Args:
          v:

        Returns:

        """
        self.ConditionalStack.append(v)

    #
    # Pop conditional and return the value
    #

    def PopConditional(self):
        """ """
        if(len(self.ConditionalStack) > 0):
            return self.ConditionalStack.pop()
        else:
            self.Logger.critical("Tried to pop an empty conditional stack.  Line Number %d" % self.CurrentLine)
            return self.ConditionalStack.pop()  # this should cause a crash but will give trace.

    def _FindReplacementForToken(self, token, replace_if_not_found=False):

        v = self.LocalVars.get(token)

        if(v is None):
            v = self.InputVars.get(token)

        if(v is None and replace_if_not_found):
            v = self._MacroNotDefinedValue

        elif(v is None):
            return None

        if (type(v) is bool):
            v = "true" if v else "false"

        if(type(v) is str and (v.upper() == "TRUE" or v.upper() == "FALSE")):
            v = v.upper()

        return str(v)

    #
    # Method to replace variables
    # in a line with their value from input dict or local dict
    #
    def ReplaceVariables(self, line):
        """

        Args:
          line:

        Returns:

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
        while(rep > 0):
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

    #
    # Process Conditional
    # return true if line is a conditional otherwise false
    #

    def ProcessConditional(self, text):
        """

        Args:
          text:

        Returns:

        """
        if '"' in text:
            tokens = text.split('"')
            tokens = tokens[0].split() + [tokens[1]] + tokens[2].split()
        else:
            tokens = text.split()
        if(tokens[0].lower() == "!if"):
            self.PushConditional(self.EvaluateConditional(text))
            return True

        elif(tokens[0].lower() == "!ifdef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1] != self._MacroNotDefinedValue))
            return True

        elif(tokens[0].lower() == "!ifndef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1] == self._MacroNotDefinedValue))
            return True

        elif(tokens[0].lower() == "!else"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            v = self.PopConditional()
            # TODO make sure we can't do multiple else statements
            self.PushConditional(not v)
            return True

        elif(tokens[0].lower() == "!endif"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PopConditional()
            return True

        return False

    def EvaluateConditional(self, text):
        ''' Uses a pushdown resolver '''
        text = str(text).strip()
        if not text.lower().startswith("!if "):
            raise RuntimeError(f"Invalid conditional cannot be validated: {text}")
        text = text[3:].strip()
        logging.debug(f"STAGE 1: {text}")
        text = self.ReplaceVariables(text)
        logging.debug(f"STAGE 2: {text}")
        tokens = self._TokenizeConditional(text)
        logging.debug(f"STAGE 3: {tokens}")
        expression = self._ConvertTokensToPostFix(tokens)
        logging.debug(f"STAGE 4: {expression}")

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
        logging.debug(f" FINAL {expression} {final}")

        return bool(final)

    @classmethod
    def _TokenizeConditional(cls, text):
        ''' takes in a string that has macros replaced '''
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
        if type(token) is not str:
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

    #
    # returns true or false depending on what state of conditional you are currently in
    #

    def InActiveCode(self):
        """ """
        ret = True
        for a in self.ConditionalStack:
            if not a:
                ret = False
                break

        return ret

    def IsGuidString(self, line):
        """
        will return true if the the line has
        = { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
        Args:
          line:

        Returns:

        """
        if(line.count("{") == 2 and line.count("}") == 2 and line.count(",") == 10 and line.count("=") == 1):
            return True
        return False

    def ParseGuid(self, line):
        """
        parse a guid into a different format
        Will throw exception if missing any of the 11 parts of isn't long enough
        Args:
          l: the guid to parse ex: { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}

        Returns: a string of the guid. ex: D3B36F2C-D551-11D4-9A46-0090273FC14D

        """
        entries = line.lstrip(' {').rstrip(' }').split(',')
        if len(entries) != 11:
            raise RuntimeError(
                f"Invalid GUID found {line}. We are missing some parts since we only found: {len(entries)}")
        gu = entries[0].lstrip(' 0').lstrip('x').strip()
        # pad front until 8 chars
        while(len(gu) < 8):
            gu = "0" + gu

        gut = entries[1].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[2].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        # strip off extra {
        gut = entries[3].lstrip(' { 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[4].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[5].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[6].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[7].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[8].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[9].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[10].split()[0].lstrip(' 0').lstrip('x').rstrip(' } ').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        proper_guid_length = 36
        if len(gu) > proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too long: {gu}")
        if len(gu) < proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too short: {gu}")

        return gu.upper()

    def ResetParserState(self):
        """ """
        self.ConditionalStack = []
        self.CurrentSection = ''
        self.CurrentFullSection = ''
        self.Parsed = False

#
# Base Class for Edk2 build files that use # for comments
#


class HashFileParser(BaseParser):
    """ """

    def __init__(self, log):
        BaseParser.__init__(self, log)

    def StripComment(self, line):
        """

        Args:
          line:

        Returns:

        """
        return line.split('#')[0].strip()

    def ParseNewSection(self, line):
        """

        Args:
          line:

        Returns:

        """
        if(line.count("[") == 1 and line.count("]") == 1):  # new section
            section = line.strip().lstrip("[").split(".")[0].split(",")[0].rstrip("]").strip()
            self.CurrentFullSection = line.strip().lstrip("[").split(",")[0].rstrip("]").strip()
            return (True, section)
        return (False, "")
