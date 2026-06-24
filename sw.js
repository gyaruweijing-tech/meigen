/*
 * Service Worker
 * オフラインでもアプリが起動できるよう、必要なファイルをキャッシュします。
 * 名言を差し替えた（quotes.js を更新した）ときは、下の CACHE のバージョン番号を
 * 1つ上げると、確実に最新版が反映されます（例: v1 -> v2）。
 */
const CACHE = "meigen-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./quotes.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        // ネットワークがあれば裏で更新（stale-while-revalidate）
        fetch(event.request)
          .then((res) => {
            if (res && res.status === 200) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(event.request, copy));
            }
          })
          .catch(() => {});
        return cached;
      }
      return fetch(event.request).catch(() => cached);
    })
  );
});
