"""제공 HTTP 연결에 업무상 거부와 미구현을 전달한다."""


class LabError(Exception):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status, self.detail = status, detail
