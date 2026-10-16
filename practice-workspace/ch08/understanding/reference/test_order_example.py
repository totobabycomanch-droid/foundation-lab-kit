"""발주 예제의 대표 사례와 입력·VAT 규칙을 확인하는 참고 테스트입니다."""

import unittest

from order_example import calculate_amounts, validate_item


class OrderExampleTests(unittest.TestCase):
    def test_normal_order_totals_5500(self):
        """A001·수량 5·서버 단가 1000·VAT 별도는 5000·500·5500입니다."""
        item = validate_item({"prod_code": "A001", "qty": 5})
        self.assertEqual(item, {"prod_code": "A001", "qty": 5})
        amounts = calculate_amounts(item, server_unit_price=1000, is_vat="2")
        self.assertEqual(amounts, {
            "unit_price": 1000, "supply_amount": 5000,
            "vat_amount": 500, "total_amount": 5500,
        })

    def test_tampered_price_is_ignored(self):
        """클라이언트 단가 1원은 제외하고 상품코드·수량과 서버 계산 결과는 유지합니다."""
        payload = {"prod_code": "A001", "qty": 5, "unit_price": 1}
        item = validate_item(payload)
        self.assertEqual(item, {"prod_code": "A001", "qty": 5})
        self.assertNotIn("unit_price", item)
        self.assertEqual(payload["unit_price"], 1)
        amounts = calculate_amounts(item, server_unit_price=1000, is_vat="2")
        self.assertEqual(amounts, {
            "unit_price": 1000, "supply_amount": 5000,
            "vat_amount": 500, "total_amount": 5500,
        })

    def test_zero_qty_is_rejected_before_calculation(self):
        """수량 0은 검증에서 거부되므로 계산 함수가 실행되지 않습니다."""
        calculation_ran = False
        with self.assertRaisesRegex(ValueError, "수량은 1 이상의 정수"):
            item = validate_item({"prod_code": "A001", "qty": 0})
            calculation_ran = True
            calculate_amounts(item, server_unit_price=1000, is_vat="2")
        self.assertFalse(calculation_ran)

    def test_product_code_is_trimmed(self):
        """상품코드의 앞뒤 공백은 제거하고 수량은 유지합니다."""
        item = validate_item({"prod_code": "  A001  ", "qty": 5})
        self.assertEqual(item, {"prod_code": "A001", "qty": 5})

    def test_invalid_product_codes_are_rejected(self):
        """상품코드는 비어 있지 않은 문자열이어야 합니다."""
        for code in (None, "", "   ", 123, True):
            with self.subTest(prod_code=code):
                with self.assertRaises(ValueError):
                    validate_item({"prod_code": code, "qty": 1})

    def test_only_positive_integer_quantities_are_accepted(self):
        """논리값·문자열·0·음수·소수·null 수량은 검증에서 거부합니다."""
        for qty in (True, False, "5", 0, -1, 1.5, None):
            with self.subTest(qty=qty):
                with self.assertRaises(ValueError):
                    validate_item({"prod_code": "A001", "qty": qty})

    def test_vat_one_adds_no_tax(self):
        """VAT 구분 1은 공급가액 5000원에 VAT를 더하지 않습니다."""
        item = validate_item({"prod_code": "A001", "qty": 5})
        amounts = calculate_amounts(item, server_unit_price=1000, is_vat="1")
        self.assertEqual(amounts["supply_amount"], 5000)
        self.assertEqual(amounts["vat_amount"], 0)
        self.assertEqual(amounts["total_amount"], 5000)

    def test_vat_rounding_boundary(self):
        """104·105·106원의 VAT는 10·11·11원이며 합계에 반영됩니다."""
        # 기대값은 구현의 계산식이 아니라 책에서 정한 업무 규칙으로 고정합니다.
        for price, vat, total in ((104, 10, 114), (105, 11, 116), (106, 11, 117)):
            with self.subTest(server_unit_price=price):
                item = validate_item({"prod_code": "A001", "qty": 1})
                amounts = calculate_amounts(item, server_unit_price=price, is_vat="2")
                self.assertEqual(amounts["supply_amount"], price)
                self.assertEqual(amounts["vat_amount"], vat)
                self.assertEqual(amounts["total_amount"], total)

    def test_server_price_must_be_positive_integer(self):
        """별도로 제공하는 서버 단가도 양의 정수 원 금액이어야 합니다."""
        item = validate_item({"prod_code": "A001", "qty": 1})
        for price in (True, False, "1000", 0, -1, 100.5, None):
            with self.subTest(server_unit_price=price):
                with self.assertRaises(ValueError):
                    calculate_amounts(item, server_unit_price=price, is_vat="2")

    def test_invalid_vat_categories_are_rejected(self):
        """VAT 구분은 문자열 1 또는 2만 허용합니다."""
        item = validate_item({"prod_code": "A001", "qty": 1})
        for category in (None, "", "3", 1, 2, True):
            with self.subTest(is_vat=category):
                with self.assertRaises(ValueError):
                    calculate_amounts(item, server_unit_price=1000, is_vat=category)


if __name__ == "__main__":
    unittest.main()
