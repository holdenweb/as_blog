import json
import os
import shelve
import sys
from collections import defaultdict
from decimal import Decimal

from dataclasses import dataclass
from hu import ObjectDict
from sep_concerns2 import make_line_items
from sep_concerns2 import PurchasedItem

DATA_DIR = "test_data"


@dataclass
class Product:
    category: str
    price: str


def build_fixture(unit):
    with open(os.path.join(DATA_DIR, "src", f"{unit}.json")) as data_file:
        data = json.load(data_file, object_hook=ObjectDict)
        for key in ("products", "orders", "tax_percent", "users"):
            default_key(data, key, unit)
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

    with shelve.open(os.path.join(DATA_DIR, "fixtures", f"{unit}.dbm")) as out_s:
        for date, orders in result_dict.items():
            out_s[date] = orders


def default_key(data, key, unit):
    if key not in data:
        try:
            with open(os.path.join(DATA_DIR, "defaults", f"{key}.json")) as dflt_file:
                data[key] = json.load(dflt_file, object_hook=ObjectDict)
        except Exception:
            sys.exit(f"Fixture {unit!r}: could not find data for {key}.")


def main(args=sys.argv[1:]):
    for arg in args:
        build_fixture(arg)


if __name__ == "__main__":
    main()
