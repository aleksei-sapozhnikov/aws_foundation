PYTHON ?= python

.PHONY: qa-format qa-check

qa-format:
	$(PYTHON) tools/qa/other.py --format
	$(PYTHON) tools/qa/tofu.py --format
	$(PYTHON) tools/qa/tofu.py --validate
	$(PYTHON) tools/qa/tflint.py --lint

qa-check:
	$(PYTHON) tools/qa/other.py --check-only
	$(PYTHON) tools/qa/tofu.py --check-only
	$(PYTHON) tools/qa/tofu.py --validate
	$(PYTHON) tools/qa/tflint.py --lint
