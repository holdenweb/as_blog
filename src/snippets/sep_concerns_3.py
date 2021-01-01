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


# snippet sep-concerns3-1
def print_and_save_bill(
    p_items: List[PurchasedItem],
    user: str = "",
    store: str = "bills",
    date: Optional[datetime.date] = None,
) -> None:
    """Output total, then item prices with sales tax. For example:
    >>> print_and_save_bill(example_items)
    Total: 297.72
    6  Bordeaux         (wine            ) 10% 21.12 139.39
    6  Viognier         (wine            ) 10% 23.99 158.33

    Also, save the bill’s line items to `store`.
    """
    line_items = make_line_items(p_items)
    print(f"Total: {total_sum4(line_items):5<.2f}")
    print_detail(line_items)
    if date is None:
        date = datetime.date.today()
    k = date.isoformat()
    db = shelve.open(store)
    if k in db:
        bills = db[k]
    else:
        bills = {}
    if user not in bills:
        bills[user] = []
    bills[user].append(line_items)
    db[k] = bills
    db.close()


# snippet sep-concerns3-2
def sales_tax_for_date(date: datetime.date, store: str = "bills") -> Decimal:
    """Retrieve total sales tax for a day from the `store`. For example:
    >>> print(sales_tax_for_date(datetime.date(1999, 1, 1)))
    0

    (since there were no sales on the given `date` in the example).
    """
    k = date.isoformat()
    db = shelve.open(store)
    if k in db:
        bills = db[k]
    else:
        bills = {}
    db.close()
    sales_tax_total = Decimal(0)
    for user in bills:
        for line_items in bills[user]:
            for item in line_items:
                sales_tax_total += item.sales_tax
    return sales_tax_total
