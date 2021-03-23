pytest:
	pytest --doctest-modules -v src/snippets

fullpytest:
	pytest --doctest-modules -vv src/snippets

doctest:
	python -m doctest -v src/snippets/*.py
