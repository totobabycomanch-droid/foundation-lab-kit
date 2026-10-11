"""발주 품목 한 건의 검증·계산을 관찰하는 예제입니다. DB 저장은 하지 않습니다."""


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


def main():
    """같은 서버 단가로 정상·조작 요청을 계산하고 수량 0은 거부합니다."""
    # 실제 ERP는 DB에서 조회합니다. 이 예제는 조회된 단가를 1000으로 가정합니다.
    server_unit_price = 1000
    for label, payload in (
        ("정상 요청", {"prod_code": "A001", "qty": 5}),
        ("조작 단가 1원", {"prod_code": "A001", "qty": 5, "unit_price": 1}),
    ):
        item = validate_item(payload)
        amounts = calculate_amounts(item, server_unit_price=server_unit_price, is_vat="2")
        print(
            f"{label}: {item['prod_code']}·수량 {item['qty']}·서버 단가 {amounts['unit_price']}원 "
            f"→ 공급가액 {amounts['supply_amount']}원·VAT {amounts['vat_amount']}원"
            f"·합계 {amounts['total_amount']}원"
        )
    try:
        validate_item({"prod_code": "A001", "qty": 0})
    except ValueError as exc:
        print(f"수량 0 요청: 거부: {exc}")
    else:
        raise AssertionError("수량 0이 거부되지 않았습니다.")
    print("확인 범위: 입력 검증과 금액 계산. DB 조회·저장과 HTTP 실행은 하지 않았습니다.")


if __name__ == "__main__":
    main()
