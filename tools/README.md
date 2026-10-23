# 개발 도구 (사이트에는 쓰이지 않음)

- `build_web.py` — claude.ai 원본 게임(holdem-gto-quiz.html)으로 웹앱 `index.html`과 `version.json`을 만들어요.
  `python3 tools/build_web.py <원본 게임 html 경로>`
- `webtest/` — 가상 Firebase(로그인·데이터·보안 규칙 흉내)로 휴대폰 여러 대를 띄워 확인하는 테스트.
  `python3 tools/webtest/t_web2.py` (가입·이어하기·중복·초기화·차단), `python3 tools/webtest/t_all.py` (종합 점수 각 5판)
  보안 규칙을 바꾸면 `harness2.py`의 규칙 흉내도 같이 바꿔야 해요.

- `webtest/audit.py` — 전체 점검. 버전·금지 표현을 확인하고 아래 테스트를 모두 돌려 PASS/FAIL로 요약해요. `python3 tools/webtest/audit.py`
  - `t_chk.py` 핸드 데이터(카드 중복·보드·빈도 합) · `t_avg.py` 종합 점수·평균 · `t_wait.py` 측정 중 플레이어 숨김 · `t_playall.py` 전체 핸드 4경로 + 연습 400문제 전수 풀이 · `t_timer.py` · `t_coach.py` · `t_coachsync.py` 코치 기록 서버 저장·기기 간 합치기·권한·초기화 · `t_coachdetail.py` 코치 상세 분석(기록 항목·EV 값·화면·! 설명·극단 데이터) · `t_jj.py`(JJ 멀티웨이 재현)

## 핸드 퀴즈 새 문제 생성기 (tools/gen150, 참고용)
- 10/23에 핸드 퀴즈를 41개 → 150개로 늘릴 때 쓴 생성기예요. `lib.py`(카드 평가·핸드 분석), `rules.py`(빈도 규칙, 푸시/폴드는 자체 계산 데이터 사용), `texts.py`(설명 문구), `gen.py`·`gen2.py`(문제 생성), `build150.py`(난이도·종류별 선택), `new_hands.json`(적용된 109문제).
- 새 109문제 중 91개의 빈도는 규칙 기반 예시 값이고, 18개(헤즈업 10·15·20·25BB, 9인 10BB 푸시/폴드)는 자체 계산 값이에요. 솔버 값이 생기면 `new_hands.json`의 `f`를 바꿔 끼우면 돼요.
- 앱에는 원본 게임의 `NEW150` 배열로 들어 있어요.

## 코치 상세 분석 (10/23)
- 핸드 퀴즈 기록(coach/{uid}의 h)에 새 항목이 붙어요: `k` 고른 행동(F 폴드·P 콜/체크·A 베팅/레이즈·J 올인), `g` GTO 비율 [F,P,A,J], `sit` 상황(o 오픈·b 블라인드 방어·p 포지션 방어·t 3벳 대응·m 멀티웨이·f 푸시·폴드), `t` 핸드 강도(첫 결정만), `ev`·`hc` 헤즈업 푸시·폴드의 칩 EV 손해(BB)와 핸드 분류. 이전 기록에는 없어서 분석에서 빠져요.
- EV는 `tools/gen150/own/hu_ev.json`(10·15·20·25BB 헤즈업 균형 기준, ICM 없음, 폴드=0 기준 이득)에서 와요. 만드는 코드는 `tools/gen150/hu_ev.py`(eqmat.json과 own/hu_nash.json 필요, eqmat.json은 저장소에 없음). 앱에는 `HU_EV` 표로 들어 있고, `HSIT`(문제별 상황)·`HEV`(EV 계산 대상 12문제)도 같이 들어 있어요.
- 보안 규칙은 바꾸지 않았어요(`validCoach`는 필드 내용을 보지 않고 개수만 제한).
