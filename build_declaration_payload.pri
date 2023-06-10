##-*-makefile-*-########################################################################################################
# Copyright 2016 - 2023 Inesonic, LLC
# 
# This file is licensed under two licenses.
#
# Inesonic Commercial License, Version 1:
#   All rights reserved.  Inesonic, LLC retains all rights to this software, including the right to relicense the
#   software in source or binary formats under different terms.  Unauthorized use under the terms of this license is
#   strictly prohibited.
#
# GNU Public License, Version 2:
#   This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
#   License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later
#   version.
#   
#   This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#   details.
#   
#   You should have received a copy of the GNU General Public License along with this program; if not, write to the Free
#   Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
########################################################################################################################

defined(SETTINGS_PRI, var) {
    include($${SETTINGS_PRI})
}

build_declaration_payload.CONFIG = no_link combine
build_declaration_payload.input = BUILD_DECLARATION_PAYLOAD_SOURCE
build_declaration_payload.output = $${BUILD_DECLARATION_PAYLOAD_TARGET}

BUILD_DECLARATION_PAYLOAD_IGNORE_SWITCHES =
for(FILE, BUILD_DECLARATION_PAYLOAD_IGNORE_FILES) {
    BUILD_DECLARATION_PAYLOAD_IGNORE_SWITCHES += --ignore=$$FILE
}

build_declaration_payload.commands = $${PYTHON_EXECUTABLE} $${SOURCE_ROOT}/build_tools/build_declaration_payload.py \
                                     --clang $${CLANGPP_EXECUTABLE} \
                                     --build-payload $${BUILD_PAYLOAD} \
                                     $${BUILD_DECLARATION_PAYLOAD_IGNORE_SWITCHES} \
                                     $(INCPATH) \
                                     --output ${QMAKE_FILE_OUT} \
                                     $${BUILD_DECLARATION_PAYLOAD_SOURCE} \

build_declaration_payload.dependency_type = TYPE_C

build_declaration_payload.variable_out = PRE_TARGETDEPS

QMAKE_EXTRA_COMPILERS += build_declaration_payload
