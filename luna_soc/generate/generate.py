#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Generate programming support files from SoC designs."""

#from .c   import GenerateC
from .svd import GenerateSVD
#from .rust import GenerateRust

#from ..gateware.lunasoc import LunaSoC


class Generate:
    # TODO add params: vendor, design_name, description, build_dir
    def __init__(self, soc):#: LunaSoC):
        self._soc = soc


    # - integration.genc --

    # TODO clean up parameters
    def c_header(self, macro_name="SOC_RESOURCES", file=None, platform_name="Generic Platform"):
        """ Generates a C header file that simplifies access to the platform's resources.

        Args:
            macro_name : Optional. The name of the guard macro for the C header, as a string without spaces.
            file       : Optional. If provided, this will be treated as the file= argument to the print()
                         function. This can be used to generate file content instead of printing to the terminal.
        """

        pass
        # TODO GenC(self._soc).generate_c_header(macro_name, file=file, platform_name=platform_name)


    def ld_script(self, file=None):
        """ Generates an ldscript that holds our primary RAM and ROM regions.

        Args:
            file       : Optional. If provided, this will be treated as the file= argument to the print()
                         function. This can be used to generate file content instead of printing to the terminal.
        """

        pass
        # TODO GenC(self._soc).generate_ld_script(file=file)


    # - integration.gensvd --

    def svd(self, file=None):
        """ Generates a svd file for the given SoC that can be used by external tools such as 'svdrust'.

        Args:
            file       : Optional. If provided, this will be treated as the file= argument to the print()
                         function. This can be used to generate file content instead of printing to the terminal.
        """

        pass
        # TODO GenSVD(self._soc).generate_svd(file=file)


    # - integration.genrust --

    def memory_x(self, file=None):
        """ Generates a svd file for the given SoC that can be used by external tools such as 'svdrust'.

        Args:
            file       :  Optional. If provided, this will be treated as the file= argument to the print()
                          function. This can be used to generate file content instead of printing to the terminal.
        """
        pass
        # TODO GenRust(self._soc).generate_memory_x(file=file)
