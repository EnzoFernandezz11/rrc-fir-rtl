PYTHON ?= python3

.PHONY: check-contract smoke full verify

check-contract:
	$(PYTHON) scripts/validate_project.py

smoke:
	$(PYTHON) scripts/ci.py smoke

full:
	$(PYTHON) scripts/ci.py full

verify: smoke full
