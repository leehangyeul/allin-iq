# 통합 GTO 차트 만들기·적용 순서 (11/4)
1. `python3 rfi2.py 15|25|40|75` — 자체 계산(참고용)
2. `solver_charts.json` — GTO 홀덤 테이블(솔버 게임)의 buildCharts(15·25·40·75)를 뽑은 값
3. `python3 merge_charts.py <원본.html>` → `merged.json` (솔버 ∩ 기준 차트: 같으면 그 액션, 다르면 믹스. 믹스는 공격적인 액션이 왼쪽. 75 = 100-75BB)
4. `python3 apply_merged.py <원본.html> <결과.html>` (notes1102.json 없이 한 번) → `node cmp_charts.js`(old/new 비교, 경로는 파일 안에서 맞춤) → `python3 gennotes.py cmp1102.json notes1102.json` → `apply_merged.py` 다시
5. 솔버 게임에도: `python3 apply_solver.py <솔버.html> <결과.html>` 후 GTO 홀덤 테이블 아티팩트 재게시
