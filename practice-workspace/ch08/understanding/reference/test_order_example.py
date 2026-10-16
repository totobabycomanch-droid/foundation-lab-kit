"""발주 예제의 대표 사례와 입력·VAT 규칙을 확인하는 참고 테스트입니다."""

import unittest
import os
from pathlib import Path
import subprocess
import sys

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


class InteractiveTests(unittest.TestCase):
    def execute(self, entries, *arguments):
        """실제 CLI에 입력을 전달하고 입력 대기는 제한 시간으로 확인합니다."""
        result = subprocess.run(
            [sys.executable, "-B", "order_example.py", *arguments],
            input="\n".join(entries) + "\n", capture_output=True, text=True,
            encoding="utf-8", timeout=5, cwd=Path(__file__).parent,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_request_prices_use_server_price(self):
        """요청 단가 100·10원 모두 서버 단가와 합계가 유지됩니다."""
        for price in (100, 10):
            with self.subTest(price=price):
                output = self.execute(["A001", "5", str(price), "n"], "--interactive")
                self.assertIn(f"'unit_price': {price}}}", output)
                self.assertIn("검증된 품목: {'prod_code': 'A001', 'qty': 5}", output)
                self.assertIn("적용한 서버 단가: 1,000원", output)
                self.assertIn("공급가액: 5,000원", output)
                self.assertIn("VAT: 500원", output)
                self.assertIn("합계: 5,500원", output)
                self.assertIn("실습을 종료합니다.", output)

    def test_invalid_quantity_has_no_success_result(self):
        """수량 -3·0은 실제 입력 경로에서 거부되고 계산 결과를 표시하지 않습니다."""
        for qty in (-3, 0):
            with self.subTest(qty=qty):
                output = self.execute(["A001", str(qty), "100", "n"], "--interactive")
                self.assertIn("계산 전 거부:", output)
                self.assertNotIn("검증된 품목:", output)
                self.assertNotIn("계산 결과:", output)
                self.assertNotIn("합계:", output)

    def test_conversion_errors_do_not_calculate(self):
        """소수·문자 수량과 잘못된 단가는 입력 변환에서 거부합니다."""
        for qty, price in (("1.5", "100"), ("abc", "100"), ('"5"', "100"), ("True", "100"), ("5", "abc")):
            with self.subTest(qty=qty, price=price):
                output = self.execute(["A001", qty, price, "n"], "--interactive")
                self.assertIn("입력 오류:", output)
                self.assertNotIn("계산 결과:", output)

    def test_rejected_quantity_can_be_corrected(self):
        """거부 뒤 새로 입력한 수량 5는 검증·계산에 성공합니다."""
        output = self.execute(["A001", "-3", "100", "y", "A001", "5", "10", "n"], "--interactive")
        self.assertLess(output.index("계산 전 거부:"), output.index("검증된 품목:"))
        self.assertEqual(output.count("계산 결과:"), 1)
        self.assertIn("합계: 5,500원", output)

    def test_new_attempt_does_not_reuse_previous_result(self):
        """성공 뒤 실패해도 이전 결과를 재표시하지 않고 새 수량으로 다시 계산합니다."""
        output = self.execute([
            "A001", "2", "100", "y", "A001", "0", "100", "y",
            "A001", "6", "10", "n",
        ], "--interactive")
        self.assertEqual(output.count("계산 결과:"), 2)
        self.assertIn("합계: 2,200원", output)
        self.assertIn("합계: 6,600원", output)
        middle = output.split("계산 전 거부:")[1].split("검증된 품목:")[0]
        self.assertNotIn("합계:", middle)

    def test_repeat_answer_is_checked(self):
        """재입력 선택은 y/n을 확인하고 n이면 종료합니다."""
        output = self.execute(["A001", "5", "100", "maybe", "n"], "--interactive")
        self.assertIn("y 또는 n을 입력해 주세요.", output)
        self.assertEqual(output.count("계산 결과:"), 1)

    def test_default_run_does_not_request_input(self):
        """기본 실행은 입력 없이 기존 세 사례를 출력합니다."""
        output = self.execute([])
        for label in ("정상 요청:", "조작 단가 1원:", "수량 0 요청:"):
            self.assertIn(label, output)
        self.assertNotIn("다시 입력하시겠습니까?", output)
        self.assertNotIn("입력을 종료합니다.", output)

    def test_import_has_no_input_or_output(self):
        """import는 입력을 요구하거나 예제를 실행하지 않습니다."""
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import order_example"], input="",
            capture_output=True, text=True, timeout=5, cwd=Path(__file__).parent,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
