import datetime
import shelve
from decimal import Decimal
from typing import List
from typing import Optional

from sep_concerns_2 import example_items  # noqa: F401
from sep_concerns_2 import LineItem  # noqa: F401
from sep_concerns_2 import make_line_items
from sep_concerns_2 import print_detail
from sep_concerns_2 import PurchasedItem
from sep_concerns_2 import total_sum4


# snippet sep-concerns4-1
def create_test_store():
    store = shelve.open("test", flag="n")
    store.close()


class Storage:
    """
    Store and retrieve orders in a shelve by customer within date.

    Each date's is represented as a dictionary where the keys are
    user identities and the values are lists of lists of LineItems.
    """

    def __init__(self, store: str = "bills"):
        self.store = store

    def open(self):
        self.db = shelve.open(self.store)

    def close(self):
        self.db.close()

    def get(self, d: datetime.date):
        """
        Retrieve a given day's bills.
        """
        k = d.isoformat()
        if k in self.db:
            bills = self.db[k]
        else:
            bills = {}
        return bills

    def put(self, d: datetime.date, bills):
        """
        Update the bills for a particular date.
        """
        k = d.isoformat()
        self.db[k] = bills

    def bills_for_date(self, d: datetime.date):
        """
        Retrieve the bills for a particular date.
        """
        self.open()
        bills = self.get(d)
        self.close()
        return bills

    def write_order(self, d: datetime.date, user: str, line_items):
        """
        Save a bill against a specific date and user.
        """
        self.open()
        bills = self.get(d)
        if user not in bills:
            bills[user] = []
        bills[user].append(line_items)
        self.put(d, bills)
        self.close()


# snippet sep-concerns4-2
def print_and_save_bill(
    p_items: List[PurchasedItem],
    user: str = "",
    store: str = "bills",
    date: Optional[datetime.date] = None,
) -> None:
    """Output total, then item prices with sales tax. For example:
    >>> create_test_store()    # Isolate tests from production dqta
    >>> print_and_save_bill(example_items, store='test')
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    The bill’s line items should now have been saved to `store`.
    """
    line_items = make_line_items(p_items)
    print(f"Total: {total_sum4(line_items):5<.2f}")
    print_detail(line_items)
    if date is None:
        date = datetime.date.today()
    storage = Storage(store)
    storage.write_order(date, user, line_items)


# snippet sep-concerns4-3
def sales_tax_for_date(date: datetime.date, store: str = "bills") -> Decimal:
    """Retrieve total sales tax for a day from the `store`. For example:
    >>> create_test_store()
    >>> print_and_save_bill(
    ...     example_items,
    ...     date=datetime.date(2021, 1, 1),
    ...     user='steve',
    ...     store='test')
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    The bill’s line items should now have been saved to `store`.
    >>> print(sales_tax_for_date(datetime.date(1999, 1, 1), store='test'))
    0

    (there were no sales on the given date in the example).
    >>> print(sales_tax_for_date(datetime.date(2021, 1, 1), store='test'))
    27.06
    """
    storage = Storage(store)
    bills = storage.bills_for_date(date)
    sales_tax_total = Decimal(0)
    for user in bills:
        for line_items in bills[user]:
            for item in line_items:
                sales_tax_total += round(item.sales_tax, 2)
    return sales_tax_total
