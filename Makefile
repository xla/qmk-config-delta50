PYTHON ?= python3
QMK_HOME ?= $(CURDIR)/.build/qmk_firmware
HARDWARE ?= hardware/delta50.json
KEYMAP ?= via

.PHONY: check setup build
check:
	$(PYTHON) tools/validate.py
	$(PYTHON) -m unittest discover -s tests -v

setup:
	$(PYTHON) tools/setup_qmk.py --qmk-home "$(QMK_HOME)"

build:
	$(PYTHON) tools/build_firmware.py --qmk-home "$(QMK_HOME)" --hardware "$(HARDWARE)" --keymap "$(KEYMAP)"
