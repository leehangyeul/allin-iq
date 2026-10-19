// ① Firebase 콘솔 → 프로젝트 설정 → 내 앱 → 웹 앱의 firebaseConfig 값을 그대로 붙여 넣으세요 (공개돼도 되는 값이에요)
export const FIREBASE_CONFIG = {
  apiKey: "AIzaSyCCYjYQ3iS9XpXNj--IoMII3B6MwhfyFWA",
  authDomain: "allin-iq.firebaseapp.com",
  projectId: "allin-iq",
  storageBucket: "allin-iq.firebasestorage.app",
  messagingSenderId: "81522024272",
  appId: "1:81522024272:web:b138d3db13deeaf9079655"
};
// ② 관리자로 쓸 구글 계정 이메일 (firestore.rules 의 ADMIN 목록과 같아야 해요)
export const ADMIN_EMAILS = ["17gyeul@gmail.com"];
