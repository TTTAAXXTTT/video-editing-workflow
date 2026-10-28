.PHONY: help check clean gui screenshot

help:
	@echo "Available commands:"
	@echo "  make gui         Start the Tkinter GUI"
	@echo "  make screenshot  Generate the main-window screenshot without popup"
	@echo "  make check       Run Python and shell syntax checks"
	@echo "  make clean       Remove generated caches and output"

gui:
	python3 scripts/gui.py

screenshot:
	bash scripts/make_screenshot.sh

check:
	python3 -m py_compile scripts/*.py
	bash -n scripts/*.sh

clean:
	rm -rf scripts/__pycache__
	rm -rf output
