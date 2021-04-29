import datetime
import json
import os
import shelve
import sys
from collections import defaultdict
from decimal import Decimal

from dataclasses import dataclass
from hu import ObjectDict
from sep_concerns5 import create_store
from sep_concerns5 import Storage
from sep_concerns7 import make_line_items
from sep_concerns7 import PurchasedItem

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

    # Write orders to storage
    db_path = location(unit)
    create_store(db_path)
    store = Storage(db_path)
    for date, orders in result_dict.items():
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        for order in orders:
            store.write_order(date, *order)


def location(unit, dir="fixtures"):
    return os.path.join(DATA_DIR, "fixtures", f"{unit}")


def default_key(data, key, unit):
    if key not in data:
        try:
            with open(os.path.join(DATA_DIR, "defaults", f"{key}.json")) as dflt_file:
                data[key] = json.load(dflt_file, object_hook=ObjectDict)
        except Exception:
            sys.exit(f"Fixture {unit!r}: neither data nor defaults for {key!r}.")


def main(args=sys.argv[1:]):
    for arg in args:
        build_fixture(arg)


if __name__ == "__main__":
    """
    Discovery code used to verify understanding of operations.
    Note that until the assertions are moved into Storage this
    code only works for dbm-based Storages (shelve).
    """
    paths = (p1, p2) = ("test_data_01", "test_data_02")
    main(paths)
    assert all(os.path.exists(location(p)) for p in paths)
    with shelve.open(location(p1)) as s1, shelve.open(location(p2)) as s2:
        assert s1 and s2  # Not newly-created!!
        for k in s1:
            assert s1[k] == s2[k]
        assert s1 == s2
