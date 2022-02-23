help:
	@echo  "CRANE CLI makefile"
	@echo
	@echo  "usage: make <target>"
	@echo  "Targets:"
	@echo  "	install		install CRANE client"


install:
	pip install -U pip wheel
	pip install unasync==0.5.0
	pip install -e crane