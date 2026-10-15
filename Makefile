PYTHON ?= python3

.PHONY: check-contract smoke full verify ppa-local ppa-package

check-contract:
	$(PYTHON) scripts/validate_project.py

smoke:
	$(PYTHON) scripts/ci.py smoke

full:
	$(PYTHON) scripts/ci.py full

verify: smoke full

ppa-local:
	$(PYTHON) scripts/ppa.py local

ppa-package:
	$(PYTHON) scripts/ppa.py package
