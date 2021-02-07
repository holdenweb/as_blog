pytest:
	pytest --doctest-modules -v src/snippets

doctest:
	python -m doctest -v src/snippets/*.py
