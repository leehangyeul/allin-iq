# ALLIN IQ · 홀덤 GTO 퀴즈 (웹앱)

PLAY SMARTER · THINK DEEPER — 홀덤 GTO 퀴즈와 프리플랍 오픈 연습.
GitHub Pages(사이트) + Firebase(로그인·실시간 순위 저장)로 동작하는 웹앱이에요. 빌드 과정 없이 이 폴더 그대로 배포돼요.

## 파일
| 파일 | 역할 |
|---|---|
| `index.html` | 게임 전체 (화면·채점·순위·관리자 페이지) |
| `fb.js` | Firebase 연결 (익명 로그인 = 플레이어, 구글 로그인 = 관리자) |
| `config.js` | **Firebase 설정값과 관리자 이메일** — 처음 한 번 채워야 해요 |
| `firestore.rules` | 서버 보안 규칙 (접속 코드·관리자 권한을 서버에서 검사) |
| `manifest.webmanifest`, `sw.js`, `icons/` | 홈 화면 앱(PWA) |
| `version.json` | 배포할 때마다 바뀌어서 '새 버전이 있어요' 알림을 띄움 |
| `fonts/` | Pretendard (SIL OFL 1.1) |

## 처음 설정 (한 번만)
1. `config.js` 에 Firebase 콘솔의 `firebaseConfig` 값과 관리자 구글 이메일을 넣어요.
2. Firebase 콘솔 → Firestore → **규칙** 탭에 `firestore.rules` 내용을 붙여 넣고, 관리자 이메일(17gyeul@gmail.com)이 들어 있는지 확인한 뒤 **게시**.
3. Firebase 콘솔 → Authentication → 설정 → **승인된 도메인**에 `아이디.github.io` 추가 (관리자 구글 로그인용).
4. GitHub 저장소 → Settings → Pages → Source: `Deploy from a branch`, Branch: `main` / `(root)` → Save.
5. 1~2분 뒤 `https://아이디.github.io/저장소이름/` 접속 → 아래 '관리자 로그인' → 관리자 페이지에서 접속 코드 설정.

## 운영
- 플레이어: 링크 → 접속 코드 + 닉네임 → 바로 게임. 점수는 각자 실시간 저장(관리자 접속 불필요).
- 관리자: 순위·플레이어 관리(기록 삭제·차단)·접속 코드·등급·문제 난이도·초기화.
- 업데이트: 저장소에 올리면 1~2분 뒤 반영, 열려 있는 화면엔 '새 버전이 있어요' 안내.

## 알아 둘 점
- 플레이어 신원은 브라우저 단위(익명 로그인)예요. 같은 브라우저는 계속 같은 사람, 다른 기기에서 들어오면 새 플레이어로 시작해요.
- 점수 계산은 브라우저에서 해요. 서버 규칙은 접속 코드·본인 기록·값 범위만 검사하므로, 개발자 도구로 점수를 조작하는 것까지 완전히 막지는 못해요.
- 프리플랍 차트 데이터와 핸드 퀴즈 빈도(예시 수치)는 공개 출시 전에 권리 확인·교체가 필요해요.
