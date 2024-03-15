# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS	  =
SPHINXBUILD	  = sphinx-build
SOURCEDIR	  = source
BUILDDIR	  = build

# Compile all d2 diagrams
D2DIR = ./images/
d2:
	@for f in $(shell ls $(D2DIR)/*.d2); do d2 $${f}; done

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
