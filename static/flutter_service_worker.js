// Placeholder service worker to satisfy requests for /flutter_service_worker.js
// This no-op worker avoids 404s and immediately takes control.

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', () => {
  // Intentionally pass-through; no caching implemented.
});
