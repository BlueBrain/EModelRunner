clean:
	@find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.png
remove_test_output:
	rm -f tests/sample_dir/hoc_recordings/*.dat
	rm -f tests/sample_dir/python_recordings/*.dat
	rm -f tests/sample_dir/factsheets/*.json
	rm -f tests/glusyn_sample_dir/output.h5
