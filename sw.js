// pages and code: network first (always the newest deploy when online); fonts and icons: cache first
const CACHE = "allin-iq-v2"; // 11/5 AIQ 아이콘으로 바꾸며 v2
const STATIC = ["fonts/Pretendard-Regular.woff2", "fonts/Pretendard-SemiBold.woff2", "fonts/Pretendard-Bold.woff2", "fonts/Pretendard-ExtraBold.woff2", "icons/icon-192.png?v=aiq"];
self.addEventListener("install", (e) => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then((c) => c.addAll(STATIC)).catch(() => {})); });
self.addEventListener("activate", (e) => e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  if (/\/(fonts|icons)\//.test(u.pathname)) {
    e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request).then((res) => { const c = res.clone(); caches.open(CACHE).then((x) => x.put(e.request, c)); return res; })));
    return;
  }
  e.respondWith(fetch(e.request).then((res) => { if (res.ok && !u.pathname.endsWith("version.json")) { const c = res.clone(); caches.open(CACHE).then((x) => x.put(e.request, c)); } return res; }).catch(() => caches.match(e.request)));
});
