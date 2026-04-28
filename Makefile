PYTHON ?= python3

.PHONY: setup build-deps icons build-macos build-macos-app build-macos-onefile build-windows build-windows-app build-windows-onefile test

setup:
	$(PYTHON) -m pip install -r requirements.txt

build-deps:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-build.txt

icons:
	$(PYTHON) scripts/build_icons.py

build-macos: build-macos-app build-macos-onefile

build-macos-app:
	$(PYTHON) scripts/build_macos.py --target app

build-macos-onefile:
	$(PYTHON) scripts/build_macos.py --target onefile

build-windows: build-windows-app build-windows-onefile

build-windows-app:
	$(PYTHON) scripts/build_windows.py --target app

build-windows-onefile:
	$(PYTHON) scripts/build_windows.py --target onefile

test:
	$(PYTHON) -m unittest discover -v
