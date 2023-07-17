# @file fdf_parser.py
# Code to help parse EDK2 Fdf files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse EDK2 Fdf files."""
import os

from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser


class FdfParser(HashFileParser):
    """FDF parser object that represents an FDF file.

    Attributes:
        Parsed (bool): Whether the object contains a parsed FDF file
        Lines (list[str]): an ordered list of each line in the FDF file
        Dict (dict): dict of form: {"VariableName": Value}
        FVs (dict): dict of form: {"sectionName": {"Dict": {}, "Infs": [], "Files": {}}}
        FDs (dict): dict of form: {"sectionName": {}}
        CurrentSection (list): all lines in current section
        Path (str): path to FDF file

    Note: Dict Key Value pairs come from lines that contain a single =.
    """
    def __init__(self) -> None:
        """Inits an empty FDF parser."""
        HashFileParser.__init__(self, 'ModuleFdfParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}  # defines dictionary
        self.FVs = {}
        self.FDs = {}
        self.CurrentSection = []
        self.Path = ""

    def GetNextLine(self) -> str:
        """Returns the next line to parse.

        Performs manipulation on the line like replacing variables,
        processing conditionals, etc.
        """
        if len(self.Lines) == 0:
            return None

        line = self.Lines.pop()
        self.CurrentLine += 1
        sline = self.StripComment(line)

        if (sline is None or len(sline) < 1):
            return self.GetNextLine()

        sline = self.ReplaceVariables(sline)
        if self.ProcessConditional(sline):
            # was a conditional so skip
            return self.GetNextLine()
        if not self.InActiveCode():
            return self.GetNextLine()

        self._BracketCount += sline.count("{")
        self._BracketCount -= sline.count("}")

        return sline

    def InsertLinesFromFile(self, file_path: str) -> None:
        """Adds additional lines to the Lines Attribute from the provided file."""
        with open(file_path, 'r') as lines_file:
            self.Lines += reversed(lines_file.readlines())
            # Back off the line count to ignore the include line itself.
            self.CurrentLine -= 1

    def ParseFile(self, filepath: str) -> None:
        """Parses the provided FDF file."""
        self.Logger.debug("Parsing file: %s" % filepath)
        if (not os.path.isabs(filepath)):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp
        self.TargetFilePath = os.path.abspath(fp)
        self.CurrentLine = 0
        self._f = open(fp, "r")
        self.Lines = self._f.readlines()
        self.Lines.reverse()
        self._f.close()
        self._BracketCount = 0
        InDefinesSection = False
        InFdSection = False
        InFvSection = False
        InCapsuleSection = False
        InFmpPayloadSection = False
        InRuleSection = False

        sline = ""
        while sline is not None:
            sline = self.GetNextLine()

            if sline is None:
                break

            if sline.lower().startswith('!include'):
                tokens = sline.split()
                include_file = tokens[1]
                sp = self.FindPath(include_file)
                if sp is None:
                    raise FileNotFoundError(include_file)
                self.Logger.debug("Opening Include File %s" % sp)
                self.InsertLinesFromFile(sp)
                continue

            if sline.strip().startswith("[") and sline.strip().endswith("]"):  # if we're starting a new section
                # this basically gets what's after the . or if it doesn't have a period
                # the whole thing for every comma separated item in sline
                self.CurrentSection = [
                    x.split(".", 1)[1] if "." in x else x for x in sline.strip("[] ").strip().split(",")]
                InDefinesSection = False
                InFdSection = False
                InFvSection = False
                InCapsuleSection = False
                InFmpPayloadSection = False
                InRuleSection = False
                self.LocalVars = {}
                self.LocalVars.update(self.Dict)

            if InDefinesSection:
                if sline.count("=") == 1:
                    tokens = sline.replace("DEFINE", "").split('=', 1)
                    self.Dict[tokens[0].strip()] = tokens[1].strip()
                    self.Logger.info("Key,values found:  %s = %s" % (tokens[0].strip(), tokens[1].strip()))
                    continue

            # defining a local variable that is removed when entering a new section
            elif sline.strip().startswith("DEFINE"):
                tokens = sline.strip().replace("DEFINE", "").split('=', 1)
                self.LocalVars[tokens[0].strip()] = tokens[1].strip()
                self.Logger.info(f"Key,values found for local vars: {tokens[0].strip()}, {tokens[1].strip()}")
                continue

            elif InFdSection:
                for section in self.CurrentSection:
                    if section not in self.FVs:
                        self.FDs[section] = {"Dict": {}}
                        # TODO finish the FD section
                continue

            elif InFvSection:
                for section in self.CurrentSection:
                    if section not in self.FVs:
                        self.FVs[section] = {"Dict": {}, "Infs": [], "Files": {}}
                    # ex: INF  MdeModulePkg/Core/RuntimeDxe/RuntimeDxe.inf
                    if sline.upper().startswith("INF "):
                        InfValue = sline[3:].strip()
                        self.FVs[section]["Infs"].append(InfValue)
                    # ex: FILE FREEFORM = 7E175642-F3AD-490A-9F8A-2E9FC6933DDD {
                    elif sline.upper().startswith("FILE"):
                        sline = sline.strip("}").strip("{").strip()  # make sure we take off the { and }
                        file_def = sline[4:].strip().split("=", 1)  # split by =
                        if len(file_def) != 2:  # check to make sure we can parse this file
                            raise RuntimeError("Unable to properly parse " + sline)

                        currentType = file_def[0].strip()  # get the type FILE
                        currentName = file_def[1].strip()  # get the name (guid or otherwise)
                        if currentType not in self.FVs[section]:
                            self.FVs[section]["Files"][currentName] = {}
                        self.FVs[section]["Files"][currentName]["type"] = currentType

                        while self._BracketCount > 0:  # go until we get our bracket back
                            sline = self.GetNextLine().strip("}{ ")
                            # SECTION GUIDED EE4E5898-3914-4259-9D6E-DC7BD79403CF
                            if sline.upper().startswith("SECTION GUIDED"):  # get the guided section
                                section_def = sline[14:].strip().split("=", 1)
                                # EE4E5898-3914-4259-9D6E-DC7BD79403CF in this example
                                sectionType = section_def[0].strip()
                                if sectionType not in self.FVs[section]["Files"][currentName]:
                                    self.FVs[section]["Files"][currentName][sectionType] = {}
                                # TODO support guided sections
                            # ex: SECTION UI = "GenericGopDriver"
                            elif sline.upper().startswith("SECTION"):  # get the section
                                section_def = sline[7:].strip().split("=", 1)
                                sectionType = section_def[0].strip()  # UI in this example
                                sectionValue = section_def[1].strip()

                                if sectionType not in self.FVs[section]["Files"][currentName]:
                                    self.FVs[section]["Files"][currentName][sectionType] = []
                                self.FVs[section]["Files"][currentName][sectionType].append(sectionValue)
                            else:
                                self.Logger.info("Unknown line: {}".format(sline))

                continue

            elif InCapsuleSection:
                # TODO: finish capsule section
                continue

            elif InFmpPayloadSection:
                # TODO finish FMP payload section
                continue

            elif InRuleSection:
                # TODO finish rule section
                continue

            # check for different sections
            if sline.strip().lower().startswith('[defines'):
                InDefinesSection = True

            elif sline.strip().lower().startswith('[fd.'):
                InFdSection = True

            elif sline.strip().lower().startswith('[fv.'):
                InFvSection = True

            elif sline.strip().lower().startswith('[capsule.'):
                InCapsuleSection = True

            elif sline.strip().lower().startswith('[fmpPayload.'):
                InFmpPayloadSection = True

            elif sline.strip().lower().startswith('[rule.'):
                InRuleSection = True

        self.Parsed = True
