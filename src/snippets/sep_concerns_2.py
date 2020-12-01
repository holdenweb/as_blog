from decimal import Decimal
from typing import List

from dataclasses import dataclass

# snippet sep-concerns2-1


@dataclass
class PurchasedItem:
    name: str
    category: str
    unit_price: Decimal
    units: int = 0


example_items = [
    PurchasedItem("Bordeaux", "wine", Decimal("21.12"), 6),
    PurchasedItem("Viognier", "wine", Decimal("23.99"), 6),
]

# snippet sep-concerns2-2
SALES_TAX_PERCENT = {"beer": 8, "wine": 10, "spirits": 13, "staples": 0}


# snippet sep-concerns2-3
def print_bill1(items: List[PurchasedItem]) -> None:
    """By-line output item prices with sales tax, then total. For example:
    >>> print_bill1(example_items)
    6  Bordeaux         (wine            ) 10% 21.12 266.11
    6  Viognier         (wine            ) 10% 23.99 302.27
    Total: 568.39
    """
    item_prices = []
    for it in items:
        item_price = it.unit_price * it.units
        item_tax_percent = SALES_TAX_PERCENT.get(it.category, 6)
        item_tax = item_price * Decimal(1 + item_tax_percent / 100)
        line = (
            f"{it.units:<2d} {it.name:<16s} ({it.category:<16s}) "
            f"{item_tax_percent:<2d}% {it.unit_price:4<.2f} "
            f"{(item_price+item_tax):4<.2f}"
        )
        print(line)
        item_prices.append(item_price + item_tax)
    total = sum(item_prices)
    print(f"Total: {total:5<.2f}")


# snippet sep-concerns2-4
@dataclass
class LineItem:
    it: PurchasedItem
    net_price: Decimal = 0
    tax_percent: Decimal = 0

    @property
    def sales_tax(self) -> Decimal:
        return Decimal(self.net_price * self.tax_percent) / 100

    @property
    def total_price(self) -> Decimal:
        return self.net_price + self.sales_tax


def net_price(item: PurchasedItem) -> Decimal:
    """Price of a single item, net of tax. For example:
    >>> print(net_price(example_items[0]))
    126.72
    """
    return item.unit_price * item.units


def post_tax_price(item: PurchasedItem) -> Decimal:
    """Price of a single item, including sales tax. For example:
    >>> print(post_tax_price(example_items[0]))
    139.392
    """
    return net_price(item) * Decimal((100 + tax_percent(item))) / 100


def tax_percent(item: PurchasedItem) -> int:
    """
    Return tax percentage to apply to a purchased item. For example:
    >>>
    print(tax_percent(example_items[0]))
    10
    """
    return SALES_TAX_PERCENT.get(item.category, 6)


def make_line_items(p_items: List[PurchasedItem]) -> List[LineItem]:
    """Produce LineItems from PurchasedItems, for example:
    >>> lines = make_line_items(example_items)
    >>> for line in lines:
    ...     print(line.net_price, line.tax_percent)
    126.72 10
    143.94 10
    """
    line_items = [LineItem(it, net_price(it), tax_percent(it)) for it in p_items]
    return line_items


def total_sum4(line_items: List[LineItem]) -> Decimal:
    """Sum of total item prices with sales tax. For example:
    >>> print(total_sum4(make_line_items(example_items)))
    297.726
    """
    return sum(it.total_price for it in line_items)


def print_detail(line_items: List[LineItem]) -> None:
    """Render iterable of LineItems for an invoice or simlar printed output."""
    for it in line_items:
        line = (
            f"{it.it.units:<2d} {it.it.name:<16s} ({it.it.category:<16s}) "
            f"{it.tax_percent:<2d}% {it.it.unit_price:4<.2f} "
            f"{(it.total_price):4<.2f}"
        )
        print(line)


def print_bill2(p_items: List[PurchasedItem]) -> None:
    """By-line output total, then item prices with sales tax. For example:
    >>> print_bill2(example_items)
    Total: 568.39
    6  Bordeaux         (wine            ) 10% 21.12 266.11
    6  Viognier         (wine            ) 10% 23.99 302.27
    """
    line_items = make_line_items(p_items)
    print("Total:", total_sum4(line_items))
    print_detail(line_items)
