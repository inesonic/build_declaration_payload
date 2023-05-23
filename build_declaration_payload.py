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
import header_packer

###############################################################################
# Globals:
#

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
and then zlib compress the resulting file.  The file is then converted into a
byte string that can be inserted into other C++ source files.

"""

###############################################################################
# Functions:
#

def build_payload(
    executable_path,
    inputs,
    output,
    copyright_message,
    description,
    indentation,
    width,
    namespace,
    variable_name,
    variable_type,
    size_variable_name,
    size_variable_type,
    use_zlib
    ):
    """
    Function you can use to run the build_payload executable.

    :param inputs:
        List of input files.

    :param output:
        The output file.

    :param executable_path:
        Path to the build_payload executable.

    :param copyright_message:
        The copyright message.  An empty string will cause the default
        copyright to be inserted.  None will cause the copyright to be
        suppressed.

    :param description:
        An optional description.  A value of None will suppress a description.

    :param indentation:
        The indentation setting.  A value of None will cause the default
        indentation to be used.

    :param width:
        The width setting.  A value of None will cause the default width
        to be used.

    :param namespace:
        An optional namespace to encapsulate the payload.  A value of None
        will suppress this option.

    :param variable_name:
        The name or suffix to apply to the payload variable(s).  A value of
        None will cause the default setting to be used.

    :param variable_type:
        The type to assign to the payload variable(s).  A value of None will
        cause the default setting to be used.

    :param size_variable_name:
        The name or suffix to apply to the payload size variable(s).  A value
        of None will cause the default setting to be used.

    :param size_variable_type:
        The type to assign to the payload variable(s).  A value of None will
        cause the default setting to be used.

    :param use_zlib:
        Indicates whether the payload should be zlib compressed.

    :type inputs:             list
    :type output:             str
    :type executable_path:    str
    :type copyright_message:  str or None
    :type description:        str or None
    :type indentation:        int or long
    :type width:              int or long
    :type namespace:          str or None
    :type variable_name:      str or None
    :type variable_type:      str or None
    :type size_variable_name: str or None
    :type size_variable_type: str or None
    :type use_zlib:           bool

    """

    arguments = [ executable_path ]

    if output:
        arguments.append("--output")
        arguments.append("\"%s\""%output)

    if isinstance(copyright_message, str):
        if copyright_message:
            arguments.append("--copyright")
            arguments.append("\"%s\""%copyright)
        else:
            arguments.append("--no-copyright")

    if description:
        arguments.append("--description")
        arguments.append("\"%s\""%description)

    if indentation:
        arguments.append("--indentation")
        arguments.append(str(indentation))

    if width:
        arguments.append("--width")
        arguments.append(str(width))

    if namespace:
        arguments.append("--namespace")
        arguments.append(namespace)

    if variable_name:
        arguments.append("--variable")
        arguments.append(variable_name)

    if variable_type:
        arguments.append("--type")
        arguments.append("\"%s\""%variable_type)

    if size_variable_name:
        arguments.append("--size-variable")
        arguments.append(size_variable_name)

    if size_variable_type:
        arguments.append("--size-type")
        arguments.append("\"%s\""%size_variable_type)

    if not use_zlib:
        arguments.append("--no-zlib")

    for input_file in inputs:
        arguments.append("\"%s\""%input_file)

    command_line = " ".join(arguments)

    result = os.system(command_line)

    if result != 0:
        raise IOError("build_payload executable failed")

###############################################################################
# Main:
#

if __name__ == "__main__":
    success = True;

    command_line_parser = argparse.ArgumentParser(description = DESCRIPTION)
    command_line_parser.add_argument(
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
               "be " + header_packer.DEFAULT_CLANG_EXECUTABLE_PATH,
        type = str,
        default = header_packer.DEFAULT_CLANG_EXECUTABLE_PATH,
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
        "-P",
        "--packed-file",
        help = "You can use this switch to specify name of the file to "
               "receive the packed output.",
        type = str,
        dest = "packed_file",
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
        "-b",
        "--build-payload",
        help = "You can use this switch to specify the path to the "
               "build_payload executable.",
        action = "store",
        default = "build_payload",
        dest = "build_payload"
    );

    command_line_parser.add_argument(
        "-z",
        "--zlib",
        help = "You can use this switch to specify that the output should be "
               "zlib compressed.  This is the default behavior.",
        action = "store_true",
        default = True,
        dest = "use_zlib"
    )

    command_line_parser.add_argument(
        "-Z",
        "--no-zlib",
        help = "You can use this switch to specify that the output should not "
               "be zlib compressed.",
        action = "store_false",
        default = True,
        dest = "use_zlib"
    )

    command_line_parser.add_argument(
        "-d",
        "--description",
        help = "You can use this switch to add an optional description to the "
               "top of the output file.",
        action = "store",
        type = str
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
        "-c",
        "--copyright",
        help = "You can use this switch to include a default Inesonic "
               "copyright message at the top of the generated file.  "
               "The default action is to include a copyright header.",
        action = "store",
        type = str,
        default = None,
        dest = "copyright"
    )

    command_line_parser.add_argument(
        "-C",
        "--no-copyright",
        help = "You can use this switch to suppress insertion of a default "
               "Inesonic copyright message at the top of the generated file.  "
               "The default action is to include a copyright header.",
        action = "store_const",
        const = str(),
        default = None,
        dest = "copyright"
    )

    command_line_parser.add_argument(
        "-e",
        "--indentation",
        help = "You can use this switch to specify the default indentation in "
               "spaces.  By default, the script will assume 4 spaces.",
        action = "store",
        type = int,
        default = None,
        dest = "indentation"
    )

    command_line_parser.add_argument(
        "-W",
        "--width",
        help = "You can use this switch to specify the maximum line width, in "
               "characters.  By default, the script will assume a maximum "
               "line width of 120 characters.",
        action = "store",
        type = int,
        default = None,
        dest = "maximum_width"
    )

    command_line_parser.add_argument(
        "-n",
        "--namespace",
        help = "You can use this switch to specify an optional namespace to "
               "embed the content into.",
        action = "store",
        type = str,
        dest = "namespace"
    )

    command_line_parser.add_argument(
        "-v",
        "--variable",
        help = "You can use this switch to specify the variable name or "
               "suffix of the variable containing the supplied content.",
        action = "append",
        type = str,
        default = None,
        dest = "variable_name"
    )

    command_line_parser.add_argument(
        "-t",
        "--type",
        help = "You can use this switch to specify the data type to assign to "
               "each created payload.",
        action = "store",
        type = str,
        default = None,
        dest = "variable_type"
    )

    command_line_parser.add_argument(
        "-V",
        "--size-variable",
        help = "You can use this switch to specify the variable name or "
               "suffix of the variable containing the supplied content size.",
        action = "append",
        type = str,
        default = None,
        dest = "size_variable_name"
    )

    command_line_parser.add_argument(
        "-T",
        "--size-type",
        help = "You can use this switch to specify the data type to assign to "
               "each created payload size.",
        action = "store",
        type = str,
        default = None,
        dest = "size_variable_type"
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
    packed_file = arguments.packed_file
    build_payload_executable = arguments.build_payload
    use_zlib = arguments.use_zlib
    description = arguments.description
    copyright = arguments.copyright
    output_file = arguments.output_file
    indentation = arguments.indentation
    maximum_width = arguments.maximum_width
    namespace = arguments.namespace
    variable_name = arguments.variable_name
    variable_type = arguments.variable_type
    size_variable_name = arguments.size_variable_name
    size_variable_type = arguments.size_variable_type
    headers = arguments.headers

    full_path_ignored_files = []
    for ignored_file in ignore_files:
        full_path = os.path.realpath(os.path.abspath(ignored_file))
        full_path_ignored_files.append(full_path)

    if not output_file       and \
       not aggregation_file  and \
       not preprocessed_file and \
       not packed_file           :
        sys.stderr.write("*** You must specify some type of output.\n")
        exit(1)
    else:
        if output_file:
            if not aggregation_file:
                aggregation_file = output_file + ".agr"

            if not preprocessed_file:
                preprocessed_file = output_file + ".pp"

            if not packed_file:
                packed_file = output_file + ".pk"
        elif packed_file:
            output_file = packed_file + ".inc"

            if not aggregation_file:
                aggregation_file = packed_file + ".agr"

            if not preprocessed_file:
                preprocessed_file = packed_file + ".pp"
        elif preprocessed_file:
            output_file = preprocessed_file + ".inc"
            packed_file = preprocessed_file + ".pk"

            if not aggregation_file:
                aggregation_file = preprocessed_file + ".agr"
        else:
            assert(aggregation_file)

            output_file = aggregation_file + ".inc"
            packed_file = aggregation_file + ".pk"
            preprocessed_file = aggregation_file + ".pp"

    hp = header_packer.HeaderPacker()
    hp.clang_executable_path = clang_executable_path
    hp.aggregation_file = aggregation_file
    hp.preprocessed_file = preprocessed_file
    hp.packed_file = packed_file
    hp.additional_clang_switches = additional_clang_switches
    hp.headers = headers
    hp.include_search_paths = include_search_paths
    hp.aggregation_file = aggregation_file
    hp.ignore_files = full_path_ignored_files

    hp.run()

    build_payload(
        executable_path = build_payload_executable,
        inputs = [ packed_file ],
        output = output_file,
        copyright_message = copyright,
        description = description,
        indentation = indentation,
        width = maximum_width,
        namespace = namespace,
        variable_name = variable_name,
        variable_type = variable_type,
        size_variable_name = size_variable_name,
        size_variable_type = size_variable_type,
        use_zlib = use_zlib
    )

    exit(0)
