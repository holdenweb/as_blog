import json
import shelve
from collections import defaultdict
from decimal import Decimal

from dataclasses import dataclass
from hu import ObjectDict
from sep_concerns_2 import make_line_items
from sep_concerns_2 import PurchasedItem


@dataclass
class Product:
    category: str
    price: str


with open("test_data/test_data_01.json") as data_file:
    data = json.load(data_file, object_hook=ObjectDict)
    d_products = {
        name: Product(category, Decimal(price))
        for (name, (category, price)) in data.products.items()
    }
    d_orders = data.orders
    tax_percent = data.tax_percent

result_dict = defaultdict(list)
for date, user_orders in d_orders.items():
    for user, orders in user_orders:
        for product_name, quantity in orders:
            product = d_products[product_name]
            p_items = [
                PurchasedItem(
                    product_name, product.category, product.price, units=quantity
                )
            ]
            result_dict[date].append((user, make_line_items(p_items)))

with shelve.open("test_data/test_data_01") as out_s:
    for date, orders in result_dict.items():
        out_s[date] = orders
