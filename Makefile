PYTHON ?= python3

.PHONY: setup build-deps build-macos build-macos-app build-macos-onefile test

setup:
	$(PYTHON) -m pip install -r requirements.txt

build-deps:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-build.txt

build-macos: build-macos-app build-macos-onefile

build-macos-app:
	$(PYTHON) scripts/build_macos.py --target app

build-macos-onefile:
	$(PYTHON) scripts/build_macos.py --target onefile

test:
	$(PYTHON) -m unittest discover -v
