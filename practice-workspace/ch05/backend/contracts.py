class MovementError(Exception):
    """업무상 거부 사유와 HTTP 응답 번호를 API 연결 코드에 전달한다."""

    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail
