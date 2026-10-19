.PHONY: help check clean

help:
	@echo "Available commands:"
	@echo "  make check   Run Python and shell syntax checks"
	@echo "  make clean   Remove generated caches and output"

check:
	python3 -m py_compile scripts/*.py
	bash -n scripts/*.sh

clean:
	rm -rf scripts/__pycache__
	rm -rf output
