# Chapter 2~3 조사용 참조 앱

이 앱은 원고에서 조사하는 가맹점 등록과 가맹점 입고확정 흐름만 떼어 낸 고정 스냅숏입니다.
현재 동작과 결함을 조사하는 읽기 전용 사례이며, 안전한 구현의 완성본이나 배포용 앱이 아닙니다.
가맹점 등록 흐름에는 원자 저장 경계가 빠진 사례가 포함되어 있습니다.
실제 DB 연결은 차단되어 있으며, 소스에서 예상한 결과와 실행으로 확인한 결과를 구분합니다.
`AGENTS.md`에 따라 코드와 SQL을 수정하지 않습니다.

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

