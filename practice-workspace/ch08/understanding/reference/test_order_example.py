"""AI가 입력과 실제 단언문을 대조할 수 있는 세 대표 테스트입니다."""

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


if __name__ == "__main__":
    unittest.main()
