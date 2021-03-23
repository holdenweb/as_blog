pytest:
	pytest --doctest-modules src/snippets

fullpytest:
	pytest --doctest-modules -vv src/snippets

doctest:
	python -m doctest -v src/snippets/*.py
