// Firebase bridge: gives the game the same small db/user interface it used on claude.ai,
// plus nickname + password accounts so a player is the same person on every device.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, onAuthStateChanged, signInAnonymously, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult, signOut,
  EmailAuthProvider, linkWithCredential, signInWithEmailAndPassword, deleteUser } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, collection, getDoc, getDocs, setDoc, deleteDoc, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { FIREBASE_CONFIG, ADMIN_EMAILS } from "./config.js";

const fail = (why) => { console.warn("[ALLIN IQ] Firebase unavailable:", why); window.__fbSet(null); };
// nickname → account key: spaces collapsed, lower-case; the key is also the names/{key} document id
export const nameClean = (v) => String(v || "").normalize("NFC").replace(/\s+/g, " ").trim().slice(0, 12);
const nameKey = (n) => nameClean(n).toLowerCase();
const nameBad = (n) => !n || /[\/]/.test(n) || n === "." || n === ".." || /^__.*__$/.test(n);
const pinOk = (p) => /^[0-9]{4,6}$/.test(String(p || ""));
async function sha(t) { const b = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t))); return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join(""); }
// each nickname signs in with an internal address; players never see or type it
const emailFor = async (key, gen) => "p" + (await sha("allin-iq:" + key + ":" + (gen || 0))).slice(0, 32) + "@players.allin-iq.app";
const pwFor = (pin) => "aiq-" + pin + "-pin";
const code = (e) => (e && e.code) || "";

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

    // the signed-in player's nickname comes from the server, never from this browser
    let myName = "";
    if (!u.isAnonymous && !isAdmin) { try { const m = await getDoc(ref("members/" + u.uid)); if (m.exists()) myName = String((m.data() || {}).name || ""); } catch (e) {} }
    const lookup = async (key) => { const s = await getDoc(ref("names/" + key)); return s.exists() ? s.data() : null; };
    const authErr = (e) => {
      const c = code(e);
      if (c === "auth/email-already-in-use" || c === "auth/credential-already-in-use") return "taken";
      if (c === "auth/invalid-credential" || c === "auth/wrong-password" || c === "auth/user-not-found" || c === "auth/invalid-login-credentials") return "badpw";
      if (c === "auth/too-many-requests") return "wait";
      if (c === "auth/operation-not-allowed") return "setup";
      if (c === "auth/network-request-failed") return "net";
      if (c === "permission-denied") return "denied";
      return "net";
    };
    const freshAnon = async () => { const cu = auth.currentUser; if (cu && cu.isAnonymous) return cu; await signOut(auth); return (await signInAnonymously(auth)).user; };

    window.HGQ_AUTH = {
      isAdmin, email: isAdmin ? (u.email || "") : "", anon: !!u.isAnonymous, name: myName, uid: u.uid,
      nameClean, nameBad, pinOk,
      admin: async () => {
        const p = new GoogleAuthProvider();
        try { await signInWithPopup(auth, p); location.reload(); }
        catch (e) { if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) await signInWithRedirect(auth, p); else alert("관리자 로그인에 실패했어요. 다시 시도해 주세요."); }
      },
      out: async () => { await signOut(auth); location.reload(); },
      // switch this device to a different nickname: back to a blank guest, then the join screen
      leave: async () => { await signOut(auth); location.reload(); },

      // first time: nickname + password become an account; this device's uid (and any record) is kept
      async register({ name, pin, code: acc }) {
        name = nameClean(name); const key = name.toLowerCase();
        if (nameBad(name)) return { err: "badname" };
        try {
          const nd = await lookup(key);
          const cu = auth.currentUser;
          if (nd && !(cu && nd.uid === cu.uid)) return { err: "taken" };
          if (cu.isAnonymous) {
            if (!pinOk(pin)) return { err: "badpin" };
            await linkWithCredential(cu, EmailAuthProvider.credential(await emailFor(key, 0), pwFor(pin)));
            await auth.currentUser.getIdToken(true);
          } else if (!nd && cu.email !== await emailFor(key, 0)) return { err: "other" };
          const uid = auth.currentUser.uid;
          if (!nd) await setDoc(ref("names/" + key), { uid, name, gen: 0, at: Date.now() });
          await setDoc(ref("members/" + uid), { code: acc, name, at: Date.now() });
          this.anon = false; this.name = name; this.uid = uid;
          return { ok: true, name, uid, switched: false };
        } catch (e) { return { err: authErr(e) }; }
      },

      // another device (or after clearing the browser): nickname + password bring back the same player
      async login({ name, pin, code: acc }) {
        name = nameClean(name); const key = name.toLowerCase();
        if (nameBad(name)) return { err: "nouser" };
        if (!pinOk(pin)) return { err: "badpw" };
        try {
          const nd = await lookup(key);
          if (!nd) return { err: "nouser" };
          if (nd.reset) return { err: "reset", name: nd.name };
          const cu = auth.currentUser;
          if (!(cu && !cu.isAnonymous && cu.uid === nd.uid)) await signInWithEmailAndPassword(auth, await emailFor(key, nd.gen || 0), pwFor(pin));
          const uid = auth.currentUser.uid;
          await setDoc(ref("members/" + uid), { code: acc, name: nd.name, at: Date.now() });
          return { ok: true, name: nd.name, uid, switched: uid !== u.uid };
        } catch (e) { return { err: authErr(e) }; }
      },

      // the admin reset this nickname: the one-time code from the admin + a new password move the record over
      async claim({ name, temp, pin, code: acc }) {
        name = nameClean(name); const key = name.toLowerCase();
        if (!pinOk(pin)) return { err: "badpin" };
        try {
          const nd = await lookup(key);
          if (!nd || !nd.reset) return { err: "noreset" };
          const gen = (nd.gen || 0) + 1, email = await emailFor(key, gen), pw = pwFor(pin);
          const cu = await freshAnon();
          let made = false;
          try { await linkWithCredential(cu, EmailAuthProvider.credential(email, pw)); made = true; await auth.currentUser.getIdToken(true); }
          catch (e) { if (authErr(e) !== "taken") throw e; await signInWithEmailAndPassword(auth, email, pw); }
          const uid = auth.currentUser.uid;
          try { await setDoc(ref("names/" + key), { uid, name: nd.name, gen, at: Date.now(), prev: nd.uid, claim: String(temp || "").trim() }); }
          catch (e) {
            // wrong one-time code: drop the half-made account so the next try starts clean
            if (made) { try { await deleteUser(auth.currentUser); } catch (x) {} } else { try { await signOut(auth); } catch (x) {} }
            try { await signInAnonymously(auth); } catch (x) {}
            return { err: "badtemp" };
          }
          await setDoc(ref("members/" + uid), { code: acc, name: nd.name, at: Date.now() });
          try {
            const old = await getDoc(ref("scores/" + nd.uid));
            if (old.exists()) { const d = { ...old.data(), name: nd.name, at: Date.now() }; await setDoc(ref("scores/" + uid), d); await deleteDoc(ref("scores/" + nd.uid)); }
          } catch (e) { console.warn("[ALLIN IQ] record move:", e); }
          try {
            const oc = await getDoc(ref("coach/" + nd.uid));
            if (oc.exists()) { await setDoc(ref("coach/" + uid), { ...oc.data(), at: Date.now() }); await deleteDoc(ref("coach/" + nd.uid)); }
          } catch (e) { console.warn("[ALLIN IQ] coach move:", e); }
          try {
            const oh = await getDoc(ref("hreview/" + nd.uid));
            if (oh.exists()) { await setDoc(ref("hreview/" + uid), { ...oh.data(), at: Date.now() }); await deleteDoc(ref("hreview/" + nd.uid)); }
          } catch (e) { console.warn("[ALLIN IQ] review move:", e); }
          return { ok: true, name: nd.name, uid, switched: true };
        } catch (e) { return { err: authErr(e) }; }
      },

      // the access code changed: a signed-in player only re-enters the code
      async recode(acc) {
        try { await setDoc(ref("members/" + auth.currentUser.uid), { code: acc, name: this.name, at: Date.now() }); return { ok: true }; }
        catch (e) { return { err: authErr(e) }; }
      },

      // admin: issue a one-time code so the player can set a new password and keep their record
      async adminReset(name) {
        const key = nameKey(name);
        try {
          const nd = await lookup(key);
          if (!nd) return { err: "nouser" };
          const t = String(Math.floor(100000 + Math.random() * 900000));
          await setDoc(ref("secret/rs_" + key), { t, at: Date.now() });
          const { claim, prev, ...keep } = nd;
          await setDoc(ref("names/" + key), { ...keep, reset: true, at: Date.now() });
          return { ok: true, temp: t, name: nd.name };
        } catch (e) { return { err: authErr(e) }; }
      },
      // admin: keep the admin's own nickname out of the player pool
      async reserve(name) {
        name = nameClean(name); const key = name.toLowerCase();
        if (nameBad(name)) return { err: "badname" };
        try {
          const nd = await lookup(key);
          if (nd && nd.uid !== auth.currentUser.uid) return { err: "taken" };
          if (!nd) await setDoc(ref("names/" + key), { uid: auth.currentUser.uid, name, gen: 0, at: Date.now() });
          return { ok: true, name };
        } catch (e) { return { err: authErr(e) }; }
      },
      async hasAccount(name) { try { return !!(await lookup(nameKey(name))); } catch (e) { return false; } },
    };
    window.__fbSet({ db, user });
  }
} catch (e) { fail(e && e.message); }
