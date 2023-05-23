=========================
Build Declaration Payload
=========================
You can use this small collection of Python scripts to:

* Combine a collection of C++ headers.

* Run the CLANG preprocessor on the combined headers to remove comments and
  and perform any additional, required, preprocessing.

* Remove additional whitespace

* Compress the headers using zlib compression.

* Express the combined C++ headers as a C++ source file that can be compiled as
  a payload into other C++ files.

This collection of Python script depends on the CLANG compiler and the
build_payload utility available at
https://github.com/inesonic/build_payload.git

The main script is called ``build_declaration_payload.py``.  For details on
how to use this tool, run the tool with the ``--help`` switch.
