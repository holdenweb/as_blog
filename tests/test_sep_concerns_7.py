import sys
from datetime import datetime

import pytest
import sep_concerns7
from sep_concerns6 import create_test_store as SQL_create
from sep_concerns6 import Storage as SQL_Storage
from sep_concerns7 import create_test_store
from sep_concerns7 import example_items
from sep_concerns7 import print_and_save_bill2
from sep_concerns7 import PurchasedItem
from sep_concerns7 import Storage

this_module = sys.modules[__name__]


@pytest.mark.parametrize(
    "storage",
    [(Storage, create_test_store), (SQL_Storage, SQL_create)],
    ids=["DBM", "SQL"],
)
def test_bills_for_range_by_user(monkeypatch, storage):
    """
    Verify that bills can be extracted by user and date.

    """
    test_store, create_function = ts, cf = storage
    monkeypatch.setattr(sep_concerns7, "Storage", test_store)
    monkeypatch.setattr(sep_concerns7, "create_test_store", create_function)
    create_test_store()
    store = Storage("test")
    #
    # Current issue: print_and_save_bill2 creates its own
    # storage object and is not affected by the monkey patching.
    # We should inject the storage object via the API.
    #
    print_and_save_bill2(
        example_items, user="steve", store=store, date=datetime(2020, 1, 1)
    )
    b = dict(store.bills_for_range_by_user(datetime(2020, 1, 1), 1))
    assert list(b.keys()) == ["steve"]
    bills = b["steve"]
    assert len(bills) == 1
    bill = bills[0]
    assert len(bill) == 2
    assert b == dict(store.bills_for_range_by_user(datetime(2020, 1, 1), 25))
    # Verify that adding another bill for the same user does not affect existing results.
    print_and_save_bill2(
        example_items, user="steve", store=store, date=datetime(2020, 1, 2)
    )
    assert list(b.keys()) == ["steve"]
    bills = b["steve"]
    assert len(bills) == 1
    bill = bills[0]
    assert len(bill) == 2
    bills = dict(store.bills_for_range_by_user(datetime(2020, 1, 1), 1))
