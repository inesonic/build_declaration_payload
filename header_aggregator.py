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
Script that can be used to aggregate multiple C++ headers into a single file
based on the #include directives.  The associated #include directives are
removed during the process.

The script can also be used as a module by other scripts.

"""

###############################################################################
# Import:
#

import os
import sys
import re
import tempfile
import optparse # argparse has an ugly bug with nargs="*"

###############################################################################
# Globals:
#

VERSION_STRING = "1.00A"
"""
The program version.

"""

DESCRIPTION = """Copyright 2020 Inesonic, LLC.  All rights reserved.

Use without explicit written permission from Inesonic, LLC is prohibited.

You can use this command line tool to generate an aggregated .PCH file from a
collection of C++ headers.

"""

DEFAULT_HEADERS = []
"""
Default headers to be parsed.

"""

DEFAULT_INCLUDE_SEARCH_PATHS = [ "." ]
"""
The default search paths for headers.

"""

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+["<]([^">]+)[">]\s*')
"""
Regular expressed used to identify headers.

"""

INCLUDE_NEXT_RE = re.compile(r'^\s*#\s*include_next')
"""
Regular expressed used to identify #include_next statements.  We will
intentionally fail if we encounter an #include_next statement.

"""

###############################################################################
# HeaderAggregator:
#

class HeaderAggregator(object):
    """
    Class that performs the .PCH compilation operation.

    +---------------------------+---------------------------------------------+
    | Property                  | Function                                    |
    +===========================+=============================================+
    | headers                   | ordered list of headers to process.         |
    |                           | Note that the tool will make a best attempt |
    |                           | to honor #include directives so you do not  |
    |                           | need to include headers required to satisfy |
    |                           | dependencies.                               |
    +---------------------------+---------------------------------------------+
    | include_search_paths      | List of directories to search for headers.  |
    +---------------------------+---------------------------------------------+
    | aggregation_file          | The output file containing the aggregated   |
    |                           | headers.                                    |
    +---------------------------+---------------------------------------------+
    | ignore_files              | List of files to skip during the            |
    |                           | aggregation process.                        |
    +---------------------------+---------------------------------------------+

    """

    def __init__(self):
        """
        Initialization method.

        """

        self.__headers = DEFAULT_HEADERS
        self.__include_search_paths = DEFAULT_INCLUDE_SEARCH_PATHS
        self.__aggregation_file = None
        self.__aggregation_file_handle = None
        self.__ignore_files = []


    @property
    def headers(self):
        """
        Read/write property you can use to determine or set the list of
        headers.

        :type: str or list

        """

        return self.__headers


    @headers.setter
    def headers(self, value):
        if isinstance(value, str):
            self.__headers = [ value ]
        elif isinstance(value, list):
            self.__headers = value
        else:
            raise TypeError("Invalid value for PchCompiler.headers")


    @property
    def include_search_paths(self):
        """
        Read/write property you can use to determine or set the list of
        include search paths.

        :type: str or list

        """

        return self.__include_search_paths


    @include_search_paths.setter
    def include_search_paths(self, value):
        if isinstance(value, str):
            self.__include_search_paths = [ value ]
        elif isinstance(value, list):
            self.__include_search_paths = value
        else:
            raise TypeError(
                "Invalid value for PchCompiler.include_search_paths"
            )


    @property
    def aggregation_file(self):
        """
        Read/write property you can use to determine or set the temporary file
        to be used.  A value of None will cause the tool to automatically
        select a name for a output file when the .PCH file is generated.

        :type: str or None

        """

        return self.__aggregation_file


    @aggregation_file.setter
    def aggregation_file(self, value):
        self.__aggregation_file = value


    @property
    def ignore_files(self):
        """
        Read/write property you can use to determine or set the list of
        files to be ignored.

        :type: str or list

        """

        return self.__ignore_files


    @ignore_files.setter
    def ignore_files(self, value):
        if isinstance(value, str):
            self.__ignore_files = [ value ]
        elif isinstance(value, list):
            self.__ignore_files = value
        else:
            raise TypeError(
                "Invalid value for PchCompiler.ignore_files"
            )


    def run(self):
        """
        Method you can call to run the PCH compiler.

        The method will raise an exception if an error is detected.

        """

        if not self.__aggregation_file_handle is None:
            self.__aggregation_file_handle.close()

        if self.__aggregation_file is None:
            self.__aggregation_file_handle = sys.stdout
        else:
            self.__aggregation_file_handle = open(
                self.__aggregation_file,
                mode = "w+"
            )

        self.__aggregate_headers(
            self.__aggregation_file_handle,
            self.__headers,
            self.__include_search_paths,
            self.__ignore_files
        )

        self.__aggregation_file_handle.flush()

        if not self.__aggregation_file is None:
            self.__aggregation_file_handle.close()


    def __aggregate_headers(
        self,
        aggregation_file_handle,
        headers,
        include_search_paths,
        ignore_files
        ):
        """
        Method that aggregates headers into a single output file

        :param aggregation_file_handle:
            File handle to the file to contain the aggregated headers.

        :param headers:
            List of header files to be processed.  Dependencies will also be
            processed such that each header will only be included once.

        :param include_search_paths:
            List of search paths to be traversed to locate headers.  Search
            paths will be traversed, in order.  Note that the list should
            always contain at least one entry.

        :param ignore_files:
            List of files to be ignored by the PCH compiler.

        :type aggregation_file_handle: file
        :type headers:               list
        :type include_search_paths:  list

        """

        processed_headers = set(self.__ignore_files)
        for header in headers:
            self.__process_header(
                aggregation_file_handle,
                header,
                include_search_paths,
                processed_headers
            )


    def __process_header(
        self,
        aggregation_file_handle,
        header,
        include_search_paths,
        processed_headers
        ):
        """
        Method that processes a single header only if it does not already exist
        in the set of processed headers.

        :param aggregation_file_handle:
            File handle to the file to contain the aggregated headers.

        :param headers:
            List of header files to be processed.  Dependencies will also be
            processed such that each header will only be included once.

        :param include_search_paths:
            List of search paths to be traversed to locate headers.  Search
            paths will be traversed, in order.  Note that the list should
            always contain at least one entry.

        :param processed_headers:
            A set of headers that have already been processed.

        :type aggregation_file_handle:    file
        :type headers:               list
        :type include_search_paths:  list
        :type processed_headers:     set

        """

        full_header_path = str()
        process_this_header = False
        found_header = False

        for include_search_path in include_search_paths:
            if not process_this_header:
                trial_path = os.path.join(include_search_path, header)

                try:
                    path_is_valid = os.path.isfile(trial_path)
                except:
                    path_is_valid = False

                if path_is_valid:
                    found_header = True
                    full_path = os.path.realpath(os.path.abspath(trial_path))
                    if not full_path in processed_headers:
                        full_header_path = full_path
                        process_this_header = True

        if not found_header:
            raise IOError("Could not find " + header);

        if process_this_header:
            processed_headers.add(full_header_path)

            with open(full_header_path, mode = "r") as header_file:
                contents = header_file.readlines()

            for raw_line in contents:
                line = raw_line.rstrip()
                match_result = INCLUDE_RE.match(line)
                if match_result:
                    child_header = match_result.group(1)
                    self.__process_header(
                        aggregation_file_handle,
                        child_header,
                        include_search_paths,
                        processed_headers
                    )
                elif INCLUDE_NEXT_RE.match(line):
                    raise NotImplementedError("No support for #include_next")
                else:
                    aggregation_file_handle.write(line)
                    aggregation_file_handle.write('\n')

###############################################################################
# Main:
#

if __name__ == "__main__":
    success = True;

    command_line_parser = optparse.OptionParser(description = DESCRIPTION)
    command_line_parser.add_option(
        "-v",
        "--version",
        help = "You can use this switch to obtain the software release "
               "version.",
        action = "store_true",
        default = False,
    )

    command_line_parser.add_option(
        "-o",
        "--output",
        help = "You can use this switch to specify the output file to be "
               "generated.  Output will be directed to stdout if this switch "
               "is not used.",
        type = str,
        dest = "aggregation_filename",
    )

    command_line_parser.add_option(
        "-I",
        "--include-path",
        help = "You can use this switch to specify a single path to be "
               "searched for header files.  If not specified, the tool will "
               "search: " + ", ".join(DEFAULT_INCLUDE_SEARCH_PATHS),
        action = "append",
        dest = "include_search_paths"
    )

    command_line_parser.add_option(
        "--ignore",
        help = "You can use this switch to specify a base-name for a given "
               "file to be ignored.",
        action = "append",
        dest = "ignore_files"
    )

    (options, headers) = command_line_parser.parse_args()

    if options.version:
        sys.stdout.write("%s\n"%VERSION_STRING)
        exit(0)
    else:
        try:
            aggregation_filename = options.aggregation_filename
        except:
            aggregation_filename = None

        try:
            include_search_paths = options.include_search_paths
        except:
            include_search_paths = DEFAULT_INCLUDE_SEARCH_PATHS

        try:
            ignore_files = list(options.ignore_files)
        except:
            ignore_files = []

        try:
            aggregation_file = options.aggregation_file
        except:
            aggregation_file = None

        full_path_ignored_files = []
        for ignored_file in ignore_files:
            full_path = os.path.realpath(os.path.abspath(ignored_file))
            full_path_ignored_files.append(full_path)

        header_aggregator = HeaderAggregator()
        header_aggregator.headers = headers
        header_aggregator.include_search_paths = include_search_paths
        header_aggregator.aggregation_file = aggregation_file
        header_aggregator.ignore_files = full_path_ignored_files

        header_aggregator.run()
        success = True

        if success:
            exit(0)
        else:
            exit(1)
