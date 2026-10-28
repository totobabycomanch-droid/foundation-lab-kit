"""AI와 실습별 업무 검사를 추가한다. 제공 verify_web.py는 독립 검사다."""
import unittest


class ImplementationTests(unittest.TestCase):
    def test_implementation_required(self):
        """원고의 AI 요청으로 실제 업무 검사를 작성할 때 교체한다."""
        self.fail('아직 업무 검사를 작성하지 않았습니다. 원고 7.3·7.5에서 AI와 완성하세요.')


if __name__=='__main__':
    unittest.main()
