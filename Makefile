pytest:
	pytest -v --doctest-modules src/snippets/*.py tests

doctest:
	python -m doctest src/snippets/*.py
