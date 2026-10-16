"""발주 품목 한 건의 검증·계산을 관찰하는 예제입니다. DB 저장은 하지 않습니다."""

import argparse


def validate_item(payload):
    """품목 입력에서 상품코드와 양의 정수 수량만 남깁니다."""
    if not isinstance(payload, dict):
        raise ValueError("품목은 JSON 객체여야 합니다.")
    prod_code = payload.get("prod_code")
    qty = payload.get("qty")
    if not isinstance(prod_code, str) or not prod_code.strip():
        raise ValueError("상품코드가 필요합니다.")
    # 이 예제는 개수로 주문하는 상품을 가정합니다. bool도 수량으로 받지 않습니다.
    if type(qty) is not int or qty <= 0:
        raise ValueError("이 예제의 수량은 1 이상의 정수여야 합니다.")
    # 클라이언트 단가를 복사하지 않고 검증된 두 값만 계산 단계에 전달합니다.
    return {"prod_code": prod_code.strip(), "qty": qty}


def calculate_amounts(item, *, server_unit_price, is_vat):
    """검증된 품목과 별도로 전달된 서버 단가로 금액을 계산합니다."""
    if type(server_unit_price) is not int or server_unit_price <= 0:
        raise ValueError("서버 단가는 양의 정수 원 금액이어야 합니다.")
    if is_vat not in ("1", "2"):
        raise ValueError('VAT 구분은 문자열 "1" 또는 "2"여야 합니다.')
    supply_amount = server_unit_price * item["qty"]
    # 정수 원 금액의 10%를 반올림하며 0.5원은 올립니다.
    vat_amount = (supply_amount + 5) // 10 if is_vat == "2" else 0
    # 계산 결과이며 저장된 발주가 아닙니다.
    return {
        "unit_price": server_unit_price,
        "supply_amount": supply_amount,
        "vat_amount": vat_amount,
        "total_amount": supply_amount + vat_amount,
    }


def run_examples():
    """같은 서버 단가로 정상·조작 요청을 계산하고 수량 0은 거부합니다."""
    # 실제 ERP는 DB에서 조회합니다. 이 예제는 조회된 단가를 1000으로 가정합니다.
    server_unit_price = 1000
    for label, payload in (
        ("정상 요청", {"prod_code": "A001", "qty": 5}),
        ("조작 단가 1원", {"prod_code": "A001", "qty": 5, "unit_price": 1}),
    ):
        item = validate_item(payload)
        amounts = calculate_amounts(item, server_unit_price=server_unit_price, is_vat="2")
        print(f"{label}:")
        print(f"  입력: {payload}")
        print(f"  검증된 품목: {item}")
        print(f"  계산 결과: {amounts}")
    invalid_payload = {"prod_code": "A001", "qty": 0}
    print("수량 0 요청:")
    print(f"  입력: {invalid_payload}")
    try:
        validate_item(invalid_payload)
    except ValueError as exc:
        print(f"  계산 전 거부: {exc}")
    else:
        raise AssertionError("수량 0이 거부되지 않았습니다.")
    print("확인 범위: 입력 검증과 금액 계산. DB 조회·저장과 HTTP 실행은 하지 않았습니다.")


def ask_again():
    """성공·실패 뒤 새 품목을 입력할지 확인합니다."""
    while True:
        answer = input("다시 입력하시겠습니까? (y/n): ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("y 또는 n을 입력해 주세요.")


def run_interactive():
    """요청 값을 직접 입력하고 서버 기준 계산과 거부 결과를 확인합니다."""
    print('직접 입력 실습: 서버 단가 1,000원·VAT "2"로 계산합니다. DB 저장은 하지 않습니다.')
    try:
        while True:
            prod_code = input("상품코드: ")
            raw_qty = input("수량: ")
            raw_price = input("요청 단가(원): ")
            try:
                # 터미널의 숫자 문자열을 변환합니다. 검증 함수의 문자열 거부 규칙은 유지합니다.
                payload = {"prod_code": prod_code, "qty": int(raw_qty), "unit_price": int(raw_price)}
            except ValueError:
                print("입력 오류: 수량과 요청 단가는 정수로 입력해 주세요.")
            else:
                print(f"입력: {payload}")
                try:
                    item = validate_item(payload)
                    # 사용자가 입력한 요청 단가는 제외하고 고정된 서버 단가를 전달합니다.
                    amounts = calculate_amounts(item, server_unit_price=1000, is_vat="2")
                except ValueError as exc:
                    print(f"계산 전 거부: {exc}")
                else:
                    print(f"검증된 품목: {item}")
                    print(f"계산 결과: {amounts}")
                    print(f"적용한 서버 단가: {amounts['unit_price']:,}원")
                    print(f"공급가액: {amounts['supply_amount']:,}원")
                    print(f"VAT: {amounts['vat_amount']:,}원")
                    print(f"합계: {amounts['total_amount']:,}원")
            if not ask_again():
                print("실습을 종료합니다.")
                return
    except (EOFError, KeyboardInterrupt):
        print("\n입력을 종료합니다.")


def main():
    """기본 실행은 세 사례를 출력하고 --interactive일 때만 입력을 받습니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="수량과 요청 단가를 직접 입력합니다.")
    args = parser.parse_args()
    if args.interactive:
        run_interactive()
    else:
        run_examples()


if __name__ == "__main__":
    main()
