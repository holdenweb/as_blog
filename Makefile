pytest:
	pytest --doctest-modules src/snippets

doctest:
	python -m doctest -v src/snippets/*.py
