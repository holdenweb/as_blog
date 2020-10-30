#!/usr/bin/python3

# snippet sep-concerns-1
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class PurchasedItem:
    name: str
    category: str
    unit_price: Decimal
    units: int = 0

example_items = [
    PurchasedItem('Bordeaux', 'wine', Decimal('21.12'), 6),
    PurchasedItem('Viognier', 'wine', Decimal('23.99'), 6)
]

# snippet sep-concerns-2
from typing import List

def total_sum1(items: List[PurchasedItem]) -> Decimal:
  """Simple sum of total item prices
  >>> print(total_sum1(example_items))
  270.66
  """
  return sum(it.unit_price*it.units for it in items)


# snippet sep-concerns-3
SALES_TAX_PERCENT = {
  'beer': 8,
  'wine': 10,
  'spirits': 13,
  'staples': 0,
}

# snippet sep-concerns-4
def total_sum2(items: List[PurchasedItem]) -> Decimal:
  """Sum of total item prices with sales tax
  >>> print(total_sum2(example_items))
  297.726
  """
  return sum((it.unit_price*it.units)*Decimal(1+Decimal(SALES_TAX_PERCENT.get(it.category, 6))/100) for it in items)

# snippet sep-concerns-5
def net_price(item: PurchasedItem) -> Decimal:
  """Price of a single item, net of tax
  >>> print(net_price(example_items[0]))
  126.72
  """
  return item.unit_price*item.units

def post_tax_price(item: PurchasedItem, net_price: Decimal) -> Decimal:
  """Price of a single item, including sales tax
  >>> print(post_tax_price(example_items[0], net_price(example_items[0])))
  139.392
  """
  tax_percent = Decimal(SALES_TAX_PERCENT.get(item.category, 6))/100
  tax_multiplier = Decimal(1+tax_percent)
  return net_price * tax_multiplier

def total_sum3(items: List[PurchasedItem]) -> Decimal:
  """Sum of total item prices with sales tax
  >>> print(total_sum3(example_items))
  297.726
  """
  return sum(post_tax_price(it, net_price(it)) for it in items)

