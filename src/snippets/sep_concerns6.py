import collections
import contextlib
import datetime
import itertools
import operator
import os
import sqlite3
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Optional

from sep_concerns2 import example_items  # noqa: F401
from sep_concerns2 import LineItem  # noqa: F401
from sep_concerns2 import make_line_items
from sep_concerns2 import print_detail
from sep_concerns2 import PurchasedItem
from sep_concerns2 import total_sum4
from sep_concerns2 import TWO_DP
from sep_concerns5 import Storage as Store5

# `Bills` is a mapping from username to list of lists of line items
Bills = Dict[str, List[List[LineItem]]]


# snippet sep-concerns6-1
def create_test_store() -> None:
    try:
        os.remove("test")
    except FileNotFoundError:
        pass
    conn = sqlite3.connect("test")
    conn.close()


class Storage(Store5):
    """
    Store and retrieve invoice in a sqlite DB, including customer identity,
    date of the invoice, and line items in that invoice. A customer may
    have zero, one, or several invoices, at any particular date.
    """

    def __init__(self, store_name: str = "bills"):
        self._store_name = store_name

    def _open(self) -> "Storage":
        self._db = sqlite3.connect(self._store_name)
        self._db.row_factory = sqlite3.Row
        cursor = self._db.cursor()
        cursor.executescript(
            """
          PRAGMA foreign_keys = ON;

          CREATE TABLE IF NOT EXISTS
          Invoice (
            id INTEGER PRIMARY KEY,
            date INTEGER,
            user TEXT
          );

          CREATE TABLE IF NOT EXISTS
          Item (
            invoice_id INTEGER,
            name TEXT,
            category TEXT,
            unit_price INTEGER,
            units INTEGER,
            net_price INTEGER,
            tax_percent INTEGER,
            FOREIGN KEY(invoice_id) REFERENCES Invoice(id)
          );
        """
        )
        self._db.commit()
        cursor.close()
        return self

    def close(self) -> None:
        self._db.close()

    def _row_to_line_item(self, row: sqlite3.Row) -> LineItem:
        name = row["name"]
        category = row["category"]
        unit_price = (Decimal(row["unit_price"]) / 100).quantize(TWO_DP)
        units = row["units"]
        purchased_item = PurchasedItem(name, category, unit_price, units)
        net_price = (Decimal(row["net_price"]) / 100).quantize(TWO_DP)
        tax_percent = row["tax_percent"]
        line_item = LineItem(purchased_item, net_price, tax_percent)
        return line_item

    def _get(self, gregorian_date: int) -> Bills:
        """
        Retrieve a given day's invoices and their items.
        """
        result = collections.defaultdict(list)
        cursor = self._db.cursor()
        cursor.execute(
            """
          SELECT * FROM Invoice JOIN Item
          ON Invoice.id=Item.invoice_id
          WHERE Invoice.date=:date
          ORDER BY invoice_id
          """,
            {"date": gregorian_date},
        )
        if not cursor.rowcount:
            # there are no invoice at that date
            return {}
        for invoice_id, rows in itertools.groupby(
            cursor, operator.itemgetter("invoice_id")
        ):
            for user, item_rows in itertools.groupby(rows, operator.itemgetter("user")):
                result[user].append([])
                for row in item_rows:
                    line_item = self._row_to_line_item(row)
                    result[user][-1].append(line_item)
        return result

    def bills_for_date(self, d: datetime.date) -> Bills:
        """
        Retrieve all the invoices for a particular date and their items.
        """
        with contextlib.closing(self._open()):
            gregorian_date = d.toordinal()
            bills = self._get(gregorian_date)
        return bills

    def _new_invoice(self, gregorian_date: int, user: str) -> int:
        cursor = self._db.cursor()
        cursor.execute(
            "INSERT INTO Invoice(date,user) VALUES(:date,:user)",
            {"date": gregorian_date, "user": user},
        )
        return cursor.lastrowid

    def write_order(
        self, d: datetime.date, user: str, line_items: List[LineItem]
    ) -> None:
        """
        Save an invoice given the invoice's date, user, and all items.
        """
        with contextlib.closing(self._open()):
            gregorian_date = d.toordinal()
            invoice_id = self._new_invoice(gregorian_date, user)
            cursor = self._db.cursor()
            for item in line_items:
                cursor.execute(
                    """
                INSERT INTO Item
                    VALUES(:invoice_id, :name, :category, :unit_price,
                           :units, :net_price, :tax_percent)
                """,
                    {
                        "invoice_id": invoice_id,
                        "name": item.it.name,
                        "category": item.it.category,
                        "unit_price": int(100 * item.it.unit_price),
                        "units": item.it.units,
                        "net_price": int(100 * item.net_price),
                        "tax_percent": int(item.tax_percent),
                    },
                )
            self._db.commit()


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
