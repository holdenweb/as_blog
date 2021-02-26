import datetime
import json
import shelve
from collections import defaultdict
from decimal import Decimal
from typing import List
from typing import Optional

from sep_concerns_2 import example_items  # noqa: F401
from sep_concerns_2 import LineItem  # noqa: F401
from sep_concerns_2 import make_line_items
from sep_concerns_2 import print_detail
from sep_concerns_2 import PurchasedItem
from sep_concerns_2 import total_sum4
from sep_concerns_2 import TWO_DP


# snippet sep-concerns5-1
def create_test_store():
    """
    Create a new 'test' database.
    >>> create_test_store()
    >>> with shelve.open('test') as db:
    ...     print(len(db))
    ...     print(list(db.keys()))
    0
    []
    """
    store = shelve.open("test", flag="n")
    store.close()


class Storage:
    """
    Store and retrieve orders in a shelve by customer within date.

    Each date's value is a dictionary where the keys are
    user identities and the values are lists of lists of LineItems,
    one list per order.
    """

    def __init__(self, store: str = "bills"):
        self.store = store

    def dump(self):
        """
        Dump the storage content in JSON format. e.g.:
        >>> create_test_store()
        >>> Storage('test').dump()
        {}
        """
        with shelve.open(self.store) as self.db:
            content = json.dumps(dict(self.db.items()), indent=3)
            print(content)
        # with shelve.open(self.store) as self.db:
        # for (date, bill_dict) in self.db.items():
        # print(date)
        # for (user, bills) in bill_dict.items():
        # print(user)
        # print(*bills, sep='\n')

    def get(self, d: datetime.date):
        """
        Retrieve a given day's bills. e.g.:
        >>> create_test_store()
        >>> print_and_save_bill2(example_items, store='test', user='steve', date=datetime.date(2020, 1, 1))
        Total: 297.72
        6  Bordeaux         (wine            ) 10% 21.12 139.39
        6  Viognier         (wine            ) 10% 23.99 158.33
        >>> with shelve.open('test') as db:
        ...     print(list(db.keys()))
        ...     print(len(db))
        ...     print(len(db['2020-01-01']['steve']))
        ...     print(len(db['2020-01-01']['steve'][0]))
        ['2020-01-01']
        1
        1
        2
        >>>
        """
        k = d.isoformat()
        with shelve.open(self.store) as self.db:
            if k in self.db:
                bills = self.db[k]
            else:
                bills = {}
            return bills

    def put(self, d: datetime.date, bills):
        """
        Update the bills for a particular date. e.g.
        >>> create_test_store()
        >>> Storage('test').put(datetime.date(2019, 1, 1), ['0123456789'])
        >>> print(Storage('test').get(datetime.date(2019, 1, 1)))
        ['0123456789']
        """
        k = d.isoformat()
        with shelve.open(self.store) as self.db:
            self.db[k] = bills

    def bills_for_date(self, d: datetime.date):
        """
        Retrieve the bills for a particular date.
        >>> create_test_store()    # Isolate tests from production data
        >>> print_and_save_bill2(example_items, user='Steve', store='test', date=datetime.date(2020, 1, 1))
        Total: 297.72
        6  Bordeaux         (wine            ) 10% 21.12 139.39
        6  Viognier         (wine            ) 10% 23.99 158.33
        >>> bills = Storage('test').bills_for_date(datetime.date(2020, 1, 1))
        >>> print(len(bills))
        1
        >>> print(len(bills['Steve'][0]))
        2
        """
        bills = self.get(d)
        return bills

    # snippet sep-concerns5-1
    def bills_for_range_by_user(
        self, sd: datetime.date, days: int, store: str = "bills"
    ):
        """
        Return a dict keyed by user whose values
        are a list of all bills for that customer
        in the covered date range.
        """
        user_bills = defaultdict(list)
        for i in range(days):
            bills = self.bills_for_date(sd + datetime.timedelta(days=i))
            for user in bills:
                user_bills[user].extend(bills[user])
        return user_bills

    # end snippet

    def write_order(self, d: datetime.date, user: str, line_items):
        """
        Save a bill against a specific date and user.
        """
        with shelve.open(self.store) as self.db:
            bills = self.get(d)
            if user not in bills:
                bills[user] = []
            bills[user].append(line_items)
            self.put(d, bills)


def print_and_save_bill2(
    p_items: List[PurchasedItem],
    user: str = "",
    store: str = "bills",
    date: Optional[datetime.date] = None,
) -> None:
    """Output total, then item prices with sales tax. For example:
    >>> create_test_store()    # Isolate tests from production data
    >>> print_and_save_bill2(example_items, store='test', date=datetime.date(2020, 1, 1))
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    The bill’s line items should now have been saved to `store`.
    TODO: split into separate print and save routines so they can
    be called separately for testing purposes.
    """
    line_items = make_line_items(p_items)
    print(f"Total: {total_sum4(line_items):5<.2f}")
    print_detail(line_items)
    if date is None:
        date = datetime.date.today()
    storage = Storage(store)
    storage.write_order(date, user, line_items)


def sales_tax_for_date2(date: datetime.date, store: str = "bills") -> Decimal:
    """Retrieve total sales tax for a day from the `store`. For example:
    >>> create_test_store()
    >>> print_and_save_bill2(
    ...     example_items,
    ...     date=datetime.date(2021, 1, 1),
    ...     user='steve',
    ...     store='test')
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    The bill’s line items should now have been saved to `store`.
    >>> print(sales_tax_for_date2(datetime.date(1999, 1, 1), store='test'))
    0

    (there were no sales on that date).
    >>> print(sales_tax_for_date2(datetime.date(2021, 1, 1), store='test'))
    27.06
    """
    storage = Storage(store)
    bills = storage.bills_for_date(date)
    sales_tax_total = Decimal(0)
    for user in bills:
        for line_items in bills[user]:
            for item in line_items:
                sales_tax_total = (sales_tax_total + item.sales_tax).quantize(TWO_DP)
    return sales_tax_total


# snippet sep-concerns5-2
def print_discount_report(
    sd: datetime.date, days: int, threshold: Decimal, store="bills"
):
    """
    Print a list of all customers whose spending
    across the different dates exceeds the given
    threshold. For example:
    >>> create_test_store()
    >>> print_and_save_bill2(
    ...     example_items,
    ...     date=datetime.date(2021, 1, 1),
    ...     user='steve',
    ...     store='test')
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    The bill’s line items should now have been saved to `store`.
    >>> s = shelve.open('test')
    >>> len(s)
    1
    >>> list(s.keys())
    ['2021-01-01']
    >>> s.close()
    >>> print_discount_report(datetime.date(2021, 1, 1), 1, Decimal("0"))
    Something
    """
    storage = Storage(store)
    bills_by_user = storage.bills_for_range_by_user(sd, days)
    print(sd, len(bills_by_user))
    for user, bills in bills_by_user:
        for bill in bills:
            for line_item in bill:
                print(">>", line_item)