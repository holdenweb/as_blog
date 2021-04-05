pytest:
	pytest -v --doctest-modules src/snippets tests

doctest:
	python -m doctest src/snippets/*.py
