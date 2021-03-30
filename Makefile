pytest:
	pytest -v --doctest-modules src/snippets
	pytest -v tests

fullpytest:
	pytest --doctest-modules -vv src/snippets

doctest:
	python -m doctest -v src/snippets/*.py
