"""Check the generated example using fixed business expectations, not its tests."""

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


class OrderRules(unittest.TestCase):
    def test_normal_and_tampered_requests(self):
        for price in (None, 1, 7, 999999):
            with self.subTest(request_price=price):
                payload = {"prod_code": "A001", "qty": 5}
                if price is not None:
                    payload["unit_price"] = price
                payload["total_amount"] = 1
                item = self.example.validate_item(payload)
                self.assertEqual(item, {"prod_code": "A001", "qty": 5})
                amounts = self.example.calculate_amounts(
                    item, server_unit_price=1000, is_vat="2"
                )
                self.assertEqual(amounts, {
                    "unit_price": 1000, "supply_amount": 5000,
                    "vat_amount": 500, "total_amount": 5500,
                })

    def test_trimmed_product_code(self):
        self.assertEqual(
            self.example.validate_item({"prod_code": "  A001  ", "qty": 2}),
            {"prod_code": "A001", "qty": 2},
        )

    def test_invalid_product_codes(self):
        for code in (None, "", "  ", 123, True):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    self.example.validate_item({"prod_code": code, "qty": 1})

    def test_invalid_quantities(self):
        for qty in (True, False, "5", 0, -1, 1.5, None):
            with self.subTest(qty=qty):
                with self.assertRaises(ValueError):
                    self.example.validate_item({"prod_code": "A001", "qty": qty})

    def test_vat_and_server_price(self):
        # Literal expectations come from business rules, never the generated formula.
        for price, qty, category, supply, vat, total in (
            (104, 1, "2", 104, 10, 114),
            (105, 1, "2", 105, 11, 116),
            (106, 1, "2", 106, 11, 117),
            (105, 1, "1", 105, 0, 105),
            (200, 3, "2", 600, 60, 660),
            (1000, 5, "1", 5000, 0, 5000),
        ):
            with self.subTest(price=price, qty=qty, category=category):
                item = self.example.validate_item({"prod_code": "A001", "qty": qty})
                amounts = self.example.calculate_amounts(
                    item, server_unit_price=price, is_vat=category
                )
                self.assertEqual(amounts, {
                    "unit_price": price, "supply_amount": supply,
                    "vat_amount": vat, "total_amount": total,
                })

    def test_invalid_server_prices(self):
        for price in (True, False, "1000", 0, -1, 100.5, None):
            with self.subTest(price=price):
                item = self.example.validate_item({"prod_code": "A001", "qty": 1})
                with self.assertRaises(ValueError):
                    self.example.calculate_amounts(item, server_unit_price=price, is_vat="2")

    def test_invalid_vat_categories(self):
        for category in (None, "", "3", 1, 2, True):
            with self.subTest(category=category):
                item = self.example.validate_item({"prod_code": "A001", "qty": 1})
                with self.assertRaises(ValueError):
                    self.example.calculate_amounts(item, server_unit_price=1000, is_vat=category)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--example-file", type=Path,
        default=Path(__file__).resolve().parents[1] / "order_example.py",
    )
    args = parser.parse_args()
    if not args.example_file.is_file():
        print("NOT RUN: generate understanding/order_example.py first.")
        return 1
    try:
        spec = importlib.util.spec_from_file_location("chapter8_checked_example", args.example_file.resolve())
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f"FAIL: cannot import example: {type(exc).__name__}: {exc}")
        return 1
    OrderRules.example = module
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(OrderRules)
    )
    print("PASS: fixed order rules" if result.wasSuccessful() else "FAIL: fixed order rules")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
