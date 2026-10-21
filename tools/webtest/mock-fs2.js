// in-memory Firestore stand-in; the test server applies the same rules as firestore.rules
const subs=[];
const me=()=>{const g=localStorage.getItem("mock-user");return g?JSON.parse(g):null};
window.__notify=()=>subs.forEach(f=>f());
export function getFirestore(){return {}}
export function doc(fs,...p){return {path:p.join("/"),id:p[p.length-1]}}
export function collection(fs,...p){return {path:p.join("/"),col:true}}
const C=()=>window.__cache||{};
const canRead=async(path)=>JSON.parse(await window.__canRead(path,JSON.stringify(me())));
const snapD=(path)=>{const v=C()[path];return{id:path.split("/").pop(),exists:()=>v!==undefined,data:()=>v}};
const list=(c)=>Object.keys(C()).filter(k=>k.startsWith(c+"/")&&k.split("/").length===c.split("/").length+1);
const deny=()=>Object.assign(new Error("Missing or insufficient permissions."),{code:"permission-denied"});
const sync=async()=>{window.__cache=JSON.parse(await window.__sync())};
export async function getDoc(r){await sync();if(!await canRead(r.path))throw deny();return snapD(r.path)}
export async function getDocs(r){await sync();if(!await canRead(r.path+"/x"))throw deny();return{docs:list(r.path).map(snapD)}}
export async function setDoc(r,d){const res=JSON.parse(await window.__set(r.path,JSON.stringify(d),JSON.stringify(me())));if(!res.ok)throw deny()}
export async function deleteDoc(r){const res=JSON.parse(await window.__del(r.path,JSON.stringify(me())));if(!res.ok)throw deny()}
export function onSnapshot(r,next,err){let alive=true;
  canRead(r.col?r.path+"/x":r.path).then(ok=>{if(!alive)return;if(!ok){err&&err(deny());return}
    const f=()=>{if(!alive)return;if(r.col)next({docs:list(r.path).map(snapD)});else next(snapD(r.path))};subs.push(f);setTimeout(f,window.__delay&&r.col?window.__delay:0)});
  return()=>{alive=false}}
