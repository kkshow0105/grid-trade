/* ================================================================
   网格交易助手 — Service Worker
   离线缓存策略：Cache First（缓存优先），网络更新缓存
   ================================================================ */

// 缓存名称（版本号用于更新时清除旧缓存）
const CACHE_NAME = 'grid-trading-v2-20260713';

// 需要预缓存的核心文件列表
const PRECACHE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

/* ----------------------------------------------------------
   install 事件：预缓存所有核心资源
   ---------------------------------------------------------- */
self.addEventListener('install', (event) => {
  console.log('[SW] 安装中 — 预缓存核心资源...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] 缓存已打开，添加资源...');
        // 逐个添加，失败不影响其他资源
        return Promise.allSettled(
          PRECACHE_ASSETS.map((url) =>
            cache.add(url).catch((err) => {
              console.warn(`[SW] 预缓存失败: ${url}`, err);
            })
          )
        );
      })
      .then(() => {
        console.log('[SW] 预缓存完成，立即激活');
        return self.skipWaiting();
      })
  );
});

/* ----------------------------------------------------------
   activate 事件：清理旧版本缓存，立即接管所有页面
   ---------------------------------------------------------- */
self.addEventListener('activate', (event) => {
  console.log('[SW] 激活中 — 清理旧缓存...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log(`[SW] 删除旧缓存: ${name}`);
            return caches.delete(name);
          })
      );
    })
    .then(() => {
      console.log('[SW] 接管所有客户端');
      return self.clients.claim();
    })
  );
});

/* ----------------------------------------------------------
   fetch 事件：缓存优先策略
   1. 先从缓存取
   2. 缓存未命中 → 发起网络请求
   3. 网络成功 → 缓存响应（供离线使用）
   4. 网络失败 → 返回离线页面或错误提示
   ---------------------------------------------------------- */
self.addEventListener('fetch', (event) => {
  // 只处理 GET 请求
  if (event.request.method !== 'GET') return;

  // 跳过 chrome-extension、blob、data 等非 http(s) 请求
  const { protocol } = new URL(event.request.url);
  if (protocol !== 'http:' && protocol !== 'https:') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // 缓存命中：立即返回缓存，同时在后台更新缓存
      if (cachedResponse) {
        // 后台发起网络请求更新缓存（Stale-While-Revalidate）
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        }).catch(() => {
          // 网络更新失败，静默处理 — 缓存版本仍然可用
        });

        // 立即返回缓存，不等网络更新
        return cachedResponse;
      }

      // 缓存未命中：发起网络请求
      return fetch(event.request).then((networkResponse) => {
        // 检查是否为有效响应
        if (!networkResponse || networkResponse.status !== 200) {
          return networkResponse;
        }

        // 缓存成功的 GET 响应
        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });

        return networkResponse;
      }).catch((error) => {
        // 网络请求失败且缓存未命中
        console.warn('[SW] 网络请求失败，资源未缓存:', event.request.url, error);

        // 如果是导航请求（HTML页面），返回缓存的 index.html
        if (event.request.mode === 'navigate') {
          return caches.match('./index.html').then((cachedIndex) => {
            return cachedIndex || new Response(
              '<html><body style="background:#0d1117;color:#e8ecf1;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;"><div style="text-align:center"><h1>📊</h1><h2>网格交易助手</h2><p>当前离线，请连接网络后重试</p></div></body></html>',
              { status: 503, statusText: 'Offline', headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
          });
        }

        // 非导航请求：返回错误
        return new Response('Network error', { status: 408, statusText: 'Network Error' });
      });
    })
  );
});

/* ----------------------------------------------------------
   message 事件：允许页面与 Service Worker 通信
   支持的操作：
   - skipWaiting：强制激活新版本
   - getVersion：返回当前缓存版本
   ---------------------------------------------------------- */
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  } else if (event.data === 'getVersion') {
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({ version: CACHE_NAME });
    }
  }
});
