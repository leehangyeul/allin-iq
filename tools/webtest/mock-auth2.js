// mock Firebase Auth: anonymous, Google (admin) and email/password accounts shared across browsers via the test server
const subs=[];
const wrap=(u)=>u?Object.assign({},u,{getIdToken:async()=>"t"}):null;
const cur=()=>{const g=localStorage.getItem("mock-user");return g?wrap(JSON.parse(g)):null};
const setU=(u)=>{if(u)localStorage.setItem("mock-user",JSON.stringify(u));else localStorage.removeItem("mock-user");const w=wrap(u);a.currentUser=w;subs.slice().forEach(f=>f(w));return w};
const a={currentUser:null};
const E=(c)=>Object.assign(new Error(c),{code:c});
export function getAuth(){a.currentUser=cur();return a}
export function onAuthStateChanged(x,cb){subs.push(cb);setTimeout(()=>cb(cur()),5);return()=>{const i=subs.indexOf(cb);if(i>=0)subs.splice(i,1)}}
export async function signInAnonymously(){const k="mock-anon-n";const n=+(localStorage.getItem(k)||0)+1;localStorage.setItem(k,n);const u={uid:window.__ID.anon+(n>1?"_"+n:""),email:null,emailVerified:false,isAnonymous:true};return{user:setU(u)}}
export class GoogleAuthProvider{}
export const EmailAuthProvider={credential:(email,pw)=>({email,pw})};
export async function signInWithPopup(){const g=window.__ID.google;if(!g)throw E("auth/popup-closed-by-user");setU({uid:g.uid,email:g.email,emailVerified:true,isAnonymous:false});return{}}
export async function signInWithRedirect(){return signInWithPopup()}
export async function getRedirectResult(){return null}
export async function signOut(){setU(null)}
export async function linkWithCredential(u,c){const r=JSON.parse(await window.__acct("create",c.email,c.pw,u.uid));if(r.err)throw E(r.err);return{user:setU({uid:u.uid,email:c.email,emailVerified:false,isAnonymous:false})}}
export async function signInWithEmailAndPassword(x,email,pw){const r=JSON.parse(await window.__acct("login",email,pw,""));if(r.err)throw E(r.err);return{user:setU({uid:r.uid,email,emailVerified:false,isAnonymous:false})}}
export async function deleteUser(u){await window.__acct("delete",u.email||"","",u.uid);setU(null)}
