// Firebase bridge: gives the game the same small db/user interface it used on claude.ai
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, onAuthStateChanged, signInAnonymously, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult, signOut } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, collection, getDoc, getDocs, setDoc, deleteDoc, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { FIREBASE_CONFIG, ADMIN_EMAILS } from "./config.js";

const fail = (why) => { console.warn("[ALLIN IQ] Firebase unavailable:", why); window.__fbSet(null); };
try {
  if (!FIREBASE_CONFIG.projectId) throw new Error("config.js is empty");
  const app = initializeApp(FIREBASE_CONFIG);
  const auth = getAuth(app);
  const fs = getFirestore(app);
  try { await getRedirectResult(auth); } catch (e) { /* no pending redirect */ }
  const u = await new Promise((res) => {
    const off = onAuthStateChanged(auth, (x) => {
      if (x) { off(); res(x); return; }
      signInAnonymously(auth).catch((e) => { off(); res(null); console.warn(e); });
    });
  });
  if (!u) { fail("sign-in failed"); }
  else {
    const admins = ADMIN_EMAILS.map((e) => String(e).trim().toLowerCase()).filter(Boolean);
    const isAdmin = !!(u.email && u.emailVerified && admins.includes(u.email.toLowerCase()));
    const snap = (s) => ({ id: s.id, exists: s.exists(), data: () => s.data() });
    const wrapErr = (e) => { const x = new Error(e && e.message); x.code = e && e.code === "permission-denied" ? "invalid_argument" : (e && e.code); return x; };
    const ref = (p) => doc(fs, ...p.split("/"));
    const col = (p) => collection(fs, ...p.split("/"));
    const db = {
      doc: (p) => ({
        id: p.split("/").pop(), path: p,
        get: async () => { try { return snap(await getDoc(ref(p))); } catch (e) { throw wrapErr(e); } },
        set: async (d) => { try { await setDoc(ref(p), d); } catch (e) { throw wrapErr(e); } },
        delete: async () => { try { await deleteDoc(ref(p)); } catch (e) { throw wrapErr(e); } },
        onSnapshot: (next, err) => onSnapshot(ref(p), (s) => next(snap(s)), (e) => err && err(wrapErr(e))),
      }),
      collection: (p) => ({
        get: async () => { try { const q = await getDocs(col(p)); return { docs: q.docs.map(snap) }; } catch (e) { throw wrapErr(e); } },
        onSnapshot: (next, err) => onSnapshot(col(p), (q) => next({ docs: q.docs.map(snap) }), (e) => err && err(wrapErr(e))),
      }),
    };
    const user = { isOwner: async () => isAdmin, canEdit: async () => isAdmin, can: async () => true, id: async () => u.uid, me: async () => ({ id: u.uid }) };
    window.HGQ_AUTH = {
      isAdmin, email: u.email || "",
      admin: async () => {
        const p = new GoogleAuthProvider();
        try { await signInWithPopup(auth, p); location.reload(); }
        catch (e) { if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) await signInWithRedirect(auth, p); else alert("관리자 로그인에 실패했어요. 다시 시도해 주세요."); }
      },
      out: async () => { await signOut(auth); location.reload(); },
    };
    window.__fbSet({ db, user });
  }
} catch (e) { fail(e && e.message); }
