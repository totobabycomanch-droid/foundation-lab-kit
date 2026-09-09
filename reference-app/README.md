# Chapter 2~3 완성 기준 참조 앱

이 앱은 원고에서 조사하는 가맹점 등록과 가맹점 입고확정 흐름만 떼어 낸 고정 스냅숏입니다.
새 기능을 구현하는 프로젝트가 아니며, `AGENTS.md`에 따라 파일을 수정하지 않습니다.

백엔드 계약 테스트:

```powershell
Set-Location backend
python -m pip install -r requirements.txt
python -m pytest tests -q -p no:cacheprovider
```

화면 계약 테스트:

```powershell
Set-Location frontend
npm ci
npm run test:e2e:day05
```

