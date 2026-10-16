UV ?= uv
PYTHON ?= 3.12
ARGS ?=
RUN = $(UV) --no-config run --no-project --python $(PYTHON) --with-requirements requirements.txt

.PHONY: run test

run:
	$(RUN) demo.py $(ARGS)

test:
	$(RUN) --with 'pytest>=8,<9' pytest -v -c /dev/null --rootdir=. .
