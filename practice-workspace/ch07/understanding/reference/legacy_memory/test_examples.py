"""출력 문구 대신 실패·재시도 뒤 DB 조회 결과를 확인합니다."""
import sqlite3
import unittest

from transaction_example import observe_failure
from sale_example import open_database, read_state, sell


class TransactionTests(unittest.TestCase):
    def test_intermediate_commit_leaves_partial_change(self):
        """주문 저장 실패가 앞서 확정한 재고 9를 복구하지 못합니다."""
        self.assertEqual(observe_failure(True), {"failed": True, "stock": 9, "orders": 0})

    def test_transaction_rolls_back_stock(self):
        """주문 INSERT 실패 후 같은 트랜잭션의 재고 차감도 취소됩니다."""
        self.assertEqual(observe_failure(False), {"failed": True, "stock": 10, "orders": 0})

    def test_repeated_runs_start_from_independent_databases(self):
        """초기화 명령 없이 여러 번 실행해도 같은 초기값에서 검사합니다."""
        for _ in range(2):
            self.assertEqual(observe_failure(False)["stock"], 10)
            self.assertEqual(observe_failure(True)["stock"], 9)


class SaleTests(unittest.TestCase):
    def setUp(self):
        self.db = open_database()
        self.addCleanup(self.db.close)

    def test_success_and_same_request_retry(self):
        """2개 판매 후 같은 요청은 같은 번호를 반환하며 DB 상태를 바꾸지 않습니다."""
        first = sell(self.db, "request-1", "A001", 2)
        self.assertEqual(read_state(self.db), {"stock": 3, "sales": [(first, "request-1", "A001", 2)]})
        before = read_state(self.db)
        self.assertEqual(sell(self.db, "request-1", "A001", 2), first)
        self.assertEqual(read_state(self.db), before)

    def test_same_key_different_quantity_is_conflict(self):
        """수량을 바꿔 같은 키로 보내면 거부하고 기존 판매 행과 재고를 보존합니다."""
        sell(self.db, "request-1", "A001", 2)
        before = read_state(self.db)
        with self.assertRaisesRegex(ValueError, "같은 키"):
            sell(self.db, "request-1", "A001", 3)
        self.assertEqual(read_state(self.db), before)

    def test_same_key_different_product_is_conflict(self):
        """상품만 바꿔 같은 키로 보내면 충돌로 거부하고 기존 판매·재고를 보존합니다."""
        sell(self.db, "request-1", "A001", 2)
        before = read_state(self.db)
        with self.assertRaisesRegex(ValueError, "같은 키"):
            sell(self.db, "request-1", "A002", 2)
        self.assertEqual(read_state(self.db), before)

    def test_invalid_quantities_preserve_database_state(self):
        """각 새 DB에서 0·음수·논리값·문자열 수량을 거부하고 판매·재고를 보존합니다."""
        for qty in (0, -1, True, "2"):
            with self.subTest(qty=qty):
                db = open_database()
                try:
                    before = read_state(db)
                    self.assertEqual(before, {"stock": 5, "sales": []})
                    with self.assertRaisesRegex(ValueError, "입력 오류"):
                        sell(db, "invalid-request", "A001", qty)
                    self.assertEqual(read_state(db), before)
                finally:
                    db.close()

    def test_exact_stock_sale_leaves_zero_stock(self):
        """재고 5개를 모두 판매하면 새 번호·판매 1건·재고 0이 남습니다."""
        number = sell(self.db, "request-all", "A001", 5)
        self.assertGreater(number, 0)
        self.assertEqual(read_state(self.db), {"stock": 0, "sales": [(number, "request-all", "A001", 5)]})

    def test_different_keys_create_separate_sales(self):
        """서로 다른 키로 2개씩 판매하면 서로 다른 번호·판매 2건·재고 1이 남습니다."""
        first = sell(self.db, "request-1", "A001", 2)
        second = sell(self.db, "request-2", "A001", 2)
        self.assertNotEqual(first, second)
        self.assertEqual(read_state(self.db), {
            "stock": 1,
            "sales": [(first, "request-1", "A001", 2), (second, "request-2", "A001", 2)],
        })

    def test_database_rejects_duplicate_request_key(self):
        """판매 함수를 거치지 않은 중복 키 INSERT도 DB 제약이 막고 기존 기록을 보존합니다."""
        sell(self.db, "request-1", "A001", 2)
        before = read_state(self.db)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db:
                self.db.execute(
                    "INSERT INTO sales(request_key, prod_code, qty) VALUES (?, ?, ?)",
                    ("request-1", "A001", 1),
                )
        self.assertEqual(read_state(self.db), before)

    def test_insufficient_stock_changes_nothing(self):
        """재고 5에서 6개 요청은 판매를 남기거나 재고를 차감하지 않습니다."""
        with self.assertRaisesRegex(ValueError, "재고 부족"):
            sell(self.db, "request-2", "A001", 6)
        self.assertEqual(read_state(self.db), {"stock": 5, "sales": []})

    def test_failed_sale_insert_rolls_back_stock(self):
        """테스트 전용 트리거로 판매 INSERT를 실패시키면 앞선 차감도 취소됩니다."""
        self.db.execute("""
            CREATE TEMP TRIGGER reject_sale BEFORE INSERT ON sales
            BEGIN SELECT RAISE(ABORT, 'intentional sale failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "intentional"):
            sell(self.db, "request-3", "A001", 2)
        self.assertEqual(read_state(self.db), {"stock": 5, "sales": []})
        self.db.execute("DROP TRIGGER reject_sale")
        number = sell(self.db, "request-3", "A001", 2)
        self.assertEqual(read_state(self.db), {"stock": 3, "sales": [(number, "request-3", "A001", 2)]})


if __name__ == "__main__":
    unittest.main()
