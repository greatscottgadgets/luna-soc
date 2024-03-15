# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS	  =
SPHINXBUILD	  = sphinx-build
SOURCEDIR	  = source
BUILDDIR	  = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile


# To make everything:
#
#  install d2: https://github.com/terrastruct/d2
#
#  make apidocs d2 registers html

# Generate api docs
apidocs:
	rm -rf source/api_docs/
	sphinx-apidoc -o source/api_docs/ ../luna_soc

# Compile all d2 diagrams
d2:
	@for f in $(shell ls ./images/eptri/*.d2); do d2 $${f}; done

# Compile all register maps
SVD = ~/GreatScott/cynthion.git/firmware/lunasoc-pac/svd/lunasoc.svd
registers:
	python bin/svd2rst.py USB0			  $(SVD) images/eptri/registers-USB0.rst
	python bin/svd2rst.py USB0_EP_CONTROL $(SVD) images/eptri/registers-USB0_EP_CONTROL.rst
	python bin/svd2rst.py USB0_EP_IN	  $(SVD) images/eptri/registers-USB0_EP_IN.rst
	python bin/svd2rst.py USB0_EP_OUT	  $(SVD) images/eptri/registers-USB0_EP_OUT.rst


# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
