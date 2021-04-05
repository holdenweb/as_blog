"""
>>> create_test_store()
>>> # Write some data to it, and close it.
>>> with shelve.open("test") as store:
...     store['something'] = ['something']
>>> create_test_store()
>>> with shelve.open("test") as db:
...     print(len(db), list(db.keys()))
0 []
"""
import shelve

from sep_concerns5 import create_test_store


def local_create_test_store():
    """
    Create a new 'test' database in the current directory.
    """
    with shelve.open("test", flag="n") as store:
        pass


def test_create_test_store():
    create_test_store()
    # Write some data to it, and close it.
    with shelve.open("test") as store:
        store["something"] = ["something"]
    create_test_store()
    with shelve.open("test") as db:
        print(len(db), list(db.keys()))
    0
