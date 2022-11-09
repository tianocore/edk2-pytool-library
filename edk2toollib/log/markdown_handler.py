##
# Handle basic logging outputting to markdown
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for handling basic logging to markdown.."""
import logging


class MarkdownFileHandler(logging.FileHandler):
    """Class for logging to markdown."""
    def __init__(self, filename, mode='w+'):
        """Init a MarkdownFileHandler."""
        logging.FileHandler.__init__(self, filename, mode=mode)
        if self.stream.writable:
            self.stream.write("  # Build Report\n")
            self.stream.write("[Go to table of contents](#table-of-contents)\n")
            self.stream.write("=====\n")
            self.stream.write(" [Go to Error List](#error-list)\n")
            self.stream.write("=====\n")
        self.contents = []
        self.error_records = []

    def emit(self, record):
        """Emit a record to the file."""
        if self.stream is None:
            self.stream = self._open()
        msg = record.message.strip("#- ")

        if len(msg) > 0:
            if logging.getLevelName(record.levelno) == "SECTION":
                self.contents.append((msg, []))
                msg = "## " + msg
            elif record.levelno == logging.CRITICAL:
                section_index = len(self.contents) - 1
                if section_index >= 0:
                    self.contents[section_index][1].append(msg)
                msg = "### " + msg
            elif record.levelno == logging.ERROR:
                self.error_records.append(record)
                msg = "#### ERROR: " + msg
            elif record.levelno == logging.WARNING:
                msg = "  _ WARNING: " + msg + "_"
            else:
                msg = "    " + msg
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)

            # self.flush()

    def handle(self, record):
        """Conditionally emit the specified logging record.

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
            except Exception:  # silently fail
                pass
            finally:
                self.release()
        return rv

    @staticmethod
    def __convert_to_markdownlink(text):
        # Using info from here https://stackoverflow.com/a/38507669
        # get rid of uppercase characters
        text = text.lower().strip()
        # get rid of punctuation
        text = text.replace(".", "").replace(",", "").replace("-", "")
        # replace spaces
        text = text.replace(" ", "-")
        return text

    def _output_error(self, record):
        output = " + \"{0}\" from {1}:{2}\n".format(record.msg, record.pathname, record.lineno)
        self.stream.write(output)

    def close(self):
        """Close the Markdown file. Appends the table of contents."""
        self.stream.write("## Table of Contents\n")
        for item, subsections in self.contents:
            link = MarkdownFileHandler.__convert_to_markdownlink(item)
            self.stream.write("+ [{0}](#{1})\n".format(item, link))
            for section in subsections:
                section_link = MarkdownFileHandler.__convert_to_markdownlink(section)
                self.stream.write("  + [{0}](#{1})\n".format(section, section_link))

        self.stream.write("## Error List\n")
        if len(self.error_records) == 0:
            self.stream.write("   No errors found")
        for record in self.error_records:
            self._output_error(record)

        self.flush()
        self.stream.close()
