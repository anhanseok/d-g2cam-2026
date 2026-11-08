# 학회 HWP 양식 자동 채우기 (2026-11-01)
- build.py: 원본 양식(.hwp)의 논문 부분(Section1)을 레코드 단위로 다시 만들어 DocInfo.bin, Section1.bin, BIN0002.png.bin 생성 (경로는 /tmp 기준이라 쓰기 전 수정 필요)
- pack.js: node `cfb` 패키지로 원본 hwp의 스트림만 교체해 저장 (cfb.js의 seed_cfb를 return 하도록 패치해야 Sh33tJ5 스트림이 안 생김)
- eqsizes.json: @rhwp/core로 계산한 수식 개체 크기/레코드. eqs.json이 수식 스크립트 목록
- 검증: @rhwp/core(브라우저 WASM)로 열어 SVG 렌더 → 미리보기 PDF
- 결과가 나오면 build.py의 노란색 Y(...) 부분과 표 4 값을 바꾸고 다시 빌드
