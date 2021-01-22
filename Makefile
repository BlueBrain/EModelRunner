TEST_REQUIREMENTS=nose coverage
 
all: install
install:
	pip install -i https://bbpteam.epfl.ch/repository/devpi/bbprelman/dev/+simple --upgrade .
test: clean install_tox
	tox -v
test-gpfs: clean install_tox
	tox -v -e py27-gpfs
install_tox:
	pip install tox
clean:
	@find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.png
install_test_requirements:
	pip install -q $(TEST_REQUIREMENTS) --upgrade
doc: clean install_tox
	tox -v -e py27-docs
devpi:
	rm -rf dist
	python setup.py sdist
	upload2repo -t python -r dev -f `ls dist/bglibpy-*.tar.gz` 
	-upload2repo -t python -r release -f `ls dist/bglibpy-*.tar.gz`
toxbinlinks:
	cd ${TOX_ENVBINDIR}; find $(TOX_NRNBINDIR) -type f -exec ln -sf \{\} . \;
