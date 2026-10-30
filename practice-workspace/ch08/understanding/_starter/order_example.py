"""AI와 완성할 발주 검증·계산 시작본입니다."""


def validate_item(payload):
    """상품코드·수량을 검증하고 두 필드만 반환하세요."""
    raise NotImplementedError('품목 검증을 AI와 구현하세요.')


def calculate_amounts(item, *, server_unit_price, is_vat):
    """별도 서버 단가와 VAT 규칙으로 계산하세요."""
    raise NotImplementedError('서버 기준 계산을 AI와 구현하세요.')


if __name__ == '__main__':
    raise NotImplementedError('실제 세 대표 사례의 출력을 AI와 구현하세요.')
