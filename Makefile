clean:
	@find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.png
toxbinlinks:
	cd ${TOX_ENVBINDIR}; find $(TOX_NRNBINDIR) -type f -exec ln -sf \{\} . \;
