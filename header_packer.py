#!/usr/bin/env python
##-*-python-*-#################################################################
# Copyright 2016 - 2023 Inesonic, LLC
#
# This file is licensed under two licenses.
#
# Inesonic Commercial License, Version 1:
#   All rights reserved.  Inesonic, LLC retains all rights to this software,
#   including the right to relicense the software in source or binary formats
#   under different terms.  Unauthorized use under the terms of this license is
#   strictly prohibited.
#
# GNU Public License, Version 2:
#   This program is free software; you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the Free
#   Software Foundation; either version 2 of the License, or (at your option)
#   any later version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#   more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc., 51
#   Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
###############################################################################

"""
Command line tool that aggregates C++ headers into a single tightly compressed,
packed representation suitable for inclusion as a data payload in C++ source.

"""

###############################################################################
# Import:
#

import os
import sys
import re
import tempfile
import argparse

import header_aggregator

###############################################################################
# Globals:
#

if sys.platform.startswith("linux"):
    __DEFAULT_CLANG_EXECUTABLE_PATH = "/opt/llvm-8.0.0/release/bin/clang++"
elif sys.platform.startswith("darwin"):
    __DEFAULT_CLANG_EXECUTABLE_PATH = "/opt/llvm-8.0.0/release/bin/clang++"
elif sys.platform.startswith("win"):
    __DEFAULT_CLANG_EXECUTABLE_PATH = "C:\\opt\\llvm-8.0.0\\Release\\x86_64\\bin\clang++.exe"
else:
    sys.stderr.write("*** Unknown platform.\n")
    exit(1)

VERSION_STRING = "1.00A"
"""
The program version.

"""

DESCRIPTION = """Copyright 2019 Inesonic, LLC.  All rights reserved.

Use without explicit written permission from Inesonic, LLC is prohibited.

You can use this command line tool to aggregate a collection of C++ header
files into a tightly compressed packed representation that you can then include
into your C++ source.

The script will aggregate the C++ source, run the CLANG preprocessor on the
aggregated source, remove additional whitespace and preprocessor inserted tags
and then zlib compress the resulting file.

"""

DEFAULT_CLANG_EXECUTABLE_PATH = __DEFAULT_CLANG_EXECUTABLE_PATH
"""
The default path to the CLANG executable.

"""

DEFAULT_ADDITIONAL_CLANG_SWITCHES = [ "-E" ]
"""
Additional switches to be included on the CLANG command line.

"""

###############################################################################
# HeaderPacker:
#

class HeaderPacker(header_aggregator.HeaderAggregator):
    """
    Class that compiles and packs a collection of C++ headers.

    +---------------------------+---------------------------------------------+
    | Property                  | Function                                    |
    +===========================+=============================================+
    | clang_executable_path     | Path to the clang executable used to        |
    |                           | generate the .PCH file.                     |
    +---------------------------+---------------------------------------------+
    | preprocessed_file         | The path to the preprocessed C++ source.    |
    +---------------------------+---------------------------------------------+
    | packed_file               | The path to the generated packed file.      |
    +---------------------------+---------------------------------------------+
    | additional_clang_switches | Additional (optional) switches to include   |
    |                           | on the CLANG command line.                  |
    +---------------------------+---------------------------------------------+
    | headers                   | ordered list of headers to process.         |
    |                           | Note that the tool will make a best attempt |
    |                           | to honor #include directives so you do not  |
    |                           | need to include headers required to satisfy |
    |                           | dependencies.                               |
    +---------------------------+---------------------------------------------+
    | include_search_paths      | List of directories to search for headers.  |
    +---------------------------+---------------------------------------------+
    | aggregation_file          | The file to contain the aggregated headers. |
    +---------------------------+---------------------------------------------+
    | ignore_files              | List of files to skip during the            |
    |                           | aggregation process.                        |
    +---------------------------+---------------------------------------------+

    """

    __PREPROCESSOR_TAG_RE = re.compile(r'^(.*)# [0-9]+ "[^"]*"( *[0-9]+)?$')
    """
    Regular expression used to find and remove clang preprocessor tags.

    """

    def __init__(self):
        """
        Initialization method.

        """

        header_aggregator.HeaderAggregator.__init__(self)

        self.__clang_executable_path = DEFAULT_CLANG_EXECUTABLE_PATH
        self.__preprocessed_file = None
        self.__packed_file = None
        self.__additional_clang_switches = DEFAULT_ADDITIONAL_CLANG_SWITCHES



    @property
    def clang_executable_path(self):
        """
        Read/write property you can use to determine or set the clang
        executable location.

        :type: str

        """

        return self.__clang_executable_path


    @clang_executable_path.setter
    def clang_executable_path(self, value):
        self.__clang_executable_path = value


    @property
    def preprocessed_file(self):
        """
        Read/write property you can use to determine or set the preprocessor
        output.

        :type: str or None

        """

        return self.__preprocessed_file


    @preprocessed_file.setter
    def preprocessed_file(self, value):
        self.__preprocessed_file = value


    @property
    def packed_file(self):
        """
        Read/write property you can use to determine or set the packed
        preprocessor output.

        :type: str or None

        """

        return self.__packed_file


    @packed_file.setter
    def packed_file(self, value):
        self.__packed_file = value


    @property
    def additional_clang_switches(self):
        """
        Read/write property you can use to specify additional switches to pass
        to the CLANG compiler.

        :type: str or list

        """

        return self.__additional_clang_switches


    @additional_clang_switches.setter
    def additional_clang_switches(self, value):
        if isinstance(value, str):
            self.__additional_clang_switches = [ value ]
        elif isinstance(value, list):
            self.__additional_clang_switches = value
        elif isinstance(value, dict):
            self.__additional_clang_switches = list()
            for item_key in value.keys():
                item_value = value[item_key]
                self.__additional_clang_switches.append(item_key)
                self.__additional_clang_switches.append(item_value)
        else:
            raise TypeError(
                "Invalid value for "
                "HeaderPackerCompiler.additional_clang_switches"
            )


    def run(self):
        """
        Method you can call to run the header packer.

        The method will raise an exception if an error is detected.

        """

        header_aggregator.HeaderAggregator.run(self)

        if not self.__preprocessed_file is None:
            self.__run_preprocessor(
                self.aggregation_file,
                self.__preprocessed_file,
                self.__clang_executable_path,
                self.__additional_clang_switches
            )

            if not self.__packed_file is None:
                self.__scrub(self.__preprocessed_file, self.__packed_file)


    def __run_preprocessor(
        self,
        aggregation_file,
        preprocessed_filename,
        clang_executable_path,
        additional_clang_switches = []
        ):
        """
        Method that runs the CLANG preprocessor compiler on the provided
        file.

        :param aggregationtemporary_file:
            The name of the aggregation file containing the aggregated headers.

        :param preprocessed_filename:
            The name of the preprocessor output file to be generated.

        :param clang_executable_path:
            The path to the CLANG executable.

        :param additional_clang_switches:
            Additional switches to be provided with the CLANG executable.

        :type aggregation_file:          str
        :type preprocessed_filename:     str
        :type clang_executable_path:     str
        :type additional_clang_switches: str

        """

        arguments = [ clang_executable_path, "-x", "c++", "-E" ]
        arguments += additional_clang_switches

        arguments.append(aggregation_file)
        arguments.append("-o")
        arguments.append(preprocessed_filename)

        command_line = " ".join(arguments)

        result = os.system(command_line)

        if result != 0:
            raise IOError("CLANG executable failed")


    def __scrub(self, preprocessed_filename, packed_filename):
        """
        Method that scrubs the preprocessor output to remove blank lines and
        preprocessor generated tags.

        :param preprocessed_filename:
            The name of the preprocessed file to be scrubbed.

        :param packed_filename:
            The name of the packed file to be generated.

        :type preprocessed_filename: str
        :type packed_filename:       str

        """

        preprocessed = open(preprocessed_filename, "r")
        packed = open(packed_filename, "w")

        for l in preprocessed:
            line = l.strip()
            if HeaderPacker.__PREPROCESSOR_TAG_RE.match(line):
                line = HeaderPacker.__PREPROCESSOR_TAG_RE.sub(
                    r'\1',
                    line
                ).strip()

            if line:
                packed.write("%s\n"%line)

        preprocessed.close()
        packed.close()

###############################################################################
# Main:
#

if __name__ == "__main__":
    success = True;

    command_line_parser = argparse.ArgumentParser(description = DESCRIPTION)
    command_line_parser.add_argument(
        "-V",
        "--version",
        help = "You can use this switch to obtain the software release "
               "version.",
        action = "version",
        version = VERSION_STRING
    )

    command_line_parser.add_argument(
        "--clang",
        help = "You can use this switch to specify the path the CLANG PCH "
               "compiler executable.  The default path will "
               "be " + DEFAULT_CLANG_EXECUTABLE_PATH,
        type = str,
        default = DEFAULT_CLANG_EXECUTABLE_PATH,
        dest = "clang_executable_path"
    )

    command_line_parser.add_argument(
        "-p",
        "--preprocessed",
        help = "You can use this switch to specify the name of the "
               "preprocessed file to be used.  If no preprocessed file is "
               "specified then a temporary file is used.",
        type = str,
        dest = "preprocessed_filename",
    )

    command_line_parser.add_argument(
        "-w",
        "--switch",
        help = "You can use this switch to inject additional switches into "
               "the CLANG preprocessor compiler when it's run.",
        action = "append",
        default = list(),
        dest = "additional_clang_switches"
    )

    command_line_parser.add_argument(
        "-I",
        "--include-path",
        help = "You can use this switch to specify a single path to be "
               "searched for header files.  If not specified, the tool will "
               "search: " +
               ", ".join(header_aggregator.DEFAULT_INCLUDE_SEARCH_PATHS),
        action = "append",
        dest = "include_search_paths"
    )

    command_line_parser.add_argument(
        "-a",
        "--aggregation-file",
        help = "You can use this switch to specify the name of the file to "
               "contain the aggregated headers.",
        type = str,
        dest = "aggregation_file"
    )

    command_line_parser.add_argument(
        "-o",
        "--output",
        help = "You can use this switch to specify name of the file to "
               "receive the generated output.  Output will be dumped to "
               "stdout if this switch is not included.",
        type = str,
        dest = "output_file",
    )

    command_line_parser.add_argument(
        "-i",
        "--ignore",
        help = "You can use this switch to specify a base-name for a given "
               "file to be ignored.",
        action = "append",
        dest = "ignore_files"
    )

    command_line_parser.add_argument(
        "headers",
        help = "Header files to be parsed.",
        nargs = "*"
    )

    arguments = command_line_parser.parse_args()

    clang_executable_path = arguments.clang_executable_path
    preprocessed_file = arguments.preprocessed_filename
    additional_clang_switches = arguments.additional_clang_switches
    include_search_paths = arguments.include_search_paths
    aggregation_file = arguments.aggregation_file
    output_filename = arguments.output_file
    ignore_files = arguments.ignore_files
    output_file = arguments.output_file
    header_files = arguments.headers

    full_path_ignored_files = []
    for ignored_file in ignore_files:
        full_path = os.path.realpath(os.path.abspath(ignored_file))
        full_path_ignored_files.append(full_path)

    if not output_file and not aggregation_file and not preprocessed_file:
        sys.stderr.write("*** You must specify some type of output.\n")
        exit(1)
    else:
        if output_file:
            if not aggregation_file:
                aggregation_file = output_file + ".agr"

            if not preprocessed_file:
                preprocessed_file = output_file + ".pp"
        else:
            packed_file = None
            if preprocessed_file:
                if not aggregation_file:
                    aggregation_file = preprocessed_file + ".agr"

    header_packer = HeaderPacker()
    header_packer.clang_executable_path = clang_executable_path
    header_packer.aggregation_file = aggregation_file
    header_packer.preprocessed_file = preprocessed_file
    header_packer.packed_file = output_file
    header_packer.additional_clang_switches = additional_clang_switches
    header_packer.headers = header_files
    header_packer.include_search_paths = include_search_paths
    header_packer.aggregation_file = aggregation_file
    header_packer.ignore_files = full_path_ignored_files

    header_packer.run()

    exit(0)
