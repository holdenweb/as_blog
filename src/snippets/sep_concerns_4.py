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
from sep_concerns_2 import TWO_DP


# snippet sep-concerns4-1
def create_test_store():
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
def print_and_save_bill2(
    p_items: List[PurchasedItem],
    user: str = "",
    store: str = "bills",
    date: Optional[datetime.date] = None,
) -> None:
    """Output total, then item prices with sales tax. For example:
    >>> create_test_store()    # Isolate tests from production data
    >>> print_and_save_bill2(example_items, store='test')
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
