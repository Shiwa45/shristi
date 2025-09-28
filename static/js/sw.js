// Service Worker for Performance Optimization
const CACHE_NAME = 'shirsti-printing-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/css/mobile-optimization.css',
    '/static/js/performance-optimization.js',
    '/static/js/products/cart-integration.js',
    '/static/js/products/design-tool-integration.js',
    '/static/css/products/product-detail.css',
    '/static/css/accessibility-seo.css'
];

// API endpoints to cache with strategy
const API_CACHE_PATTERNS = [
    '/orders/api/cart/summary/',
    '/design-tool/api/user-designs/',
    '/orders/api/quotes/',
    '/services/api/static-products/'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => {
                return cache.addAll(STATIC_FILES);
            }),
            caches.open(DYNAMIC_CACHE)
        ]).then(() => {
            console.log('Service Worker: Static files cached');
            return self.skipWaiting();
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activated');
            return self.clients.claim();
        })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip external requests
    if (!url.origin.includes(self.location.origin)) {
        return;
    }

    // Strategy selection based on request type
    if (request.url.includes('/static/')) {
        // Static files: Cache First
        event.respondWith(cacheFirst(request, STATIC_CACHE));
    } else if (isAPIRequest(request.url)) {
        // API requests: Network First with cache fallback
        event.respondWith(networkFirst(request, DYNAMIC_CACHE));
    } else if (request.url.includes('/media/')) {
        // Media files: Cache First with network fallback
        event.respondWith(cacheFirst(request, DYNAMIC_CACHE));
    } else {
        // HTML pages: Stale While Revalidate
        event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
    }
});

// Cache First Strategy
async function cacheFirst(request, cacheName) {
    try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('Cache First strategy failed:', error);
        return new Response('Network error', { status: 408 });
    }
}

// Network First Strategy
async function networkFirst(request, cacheName) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);

        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline fallback for API requests
        if (isAPIRequest(request.url)) {
            return new Response(JSON.stringify({
                success: false,
                error: 'Offline',
                cached: false
            }), {
                headers: { 'Content-Type': 'application/json' },
                status: 503
            });
        }

        return new Response('Offline', { status: 503 });
    }
}

// Stale While Revalidate Strategy
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);

    // Fetch from network in background
    const networkResponsePromise = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(error => {
        console.log('Background fetch failed:', error);
    });

    // Return cached version immediately if available
    if (cachedResponse) {
        return cachedResponse;
    }

    // Otherwise wait for network response
    return networkResponsePromise;
}

// Helper function to check if request is API
function isAPIRequest(url) {
    return API_CACHE_PATTERNS.some(pattern => url.includes(pattern)) ||
           url.includes('/api/');
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'cart-update') {
        event.waitUntil(syncCartUpdates());
    } else if (event.tag === 'design-save') {
        event.waitUntil(syncDesignSaves());
    }
});

// Sync cart updates when back online
async function syncCartUpdates() {
    try {
        const pendingUpdates = await getStoredData('pending-cart-updates');

        if (pendingUpdates && pendingUpdates.length > 0) {
            for (const update of pendingUpdates) {
                await fetch('/orders/api/cart/update/' + update.itemId + '/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': update.csrfToken
                    },
                    body: JSON.stringify({ quantity: update.quantity })
                });
            }

            // Clear pending updates
            await clearStoredData('pending-cart-updates');
            console.log('Cart updates synced successfully');
        }
    } catch (error) {
        console.error('Failed to sync cart updates:', error);
    }
}

// Sync design saves when back online
async function syncDesignSaves() {
    try {
        const pendingSaves = await getStoredData('pending-design-saves');

        if (pendingSaves && pendingSaves.length > 0) {
            for (const save of pendingSaves) {
                await fetch('/design-tool/api/save/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': save.csrfToken
                    },
                    body: JSON.stringify(save.data)
                });
            }

            // Clear pending saves
            await clearStoredData('pending-design-saves');
            console.log('Design saves synced successfully');
        }
    } catch (error) {
        console.error('Failed to sync design saves:', error);
    }
}

// IndexedDB operations for offline storage
async function getStoredData(key) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('ShirstiDB', 1);

        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['offline-data'], 'readonly');
            const store = transaction.objectStore('offline-data');
            const getRequest = store.get(key);

            getRequest.onsuccess = () => {
                resolve(getRequest.result ? getRequest.result.data : null);
            };

            getRequest.onerror = () => reject(getRequest.error);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('offline-data')) {
                db.createObjectStore('offline-data', { keyPath: 'id' });
            }
        };

        request.onerror = () => reject(request.error);
    });
}

async function clearStoredData(key) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('ShirstiDB', 1);

        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['offline-data'], 'readwrite');
            const store = transaction.objectStore('offline-data');
            const deleteRequest = store.delete(key);

            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };

        request.onerror = () => reject(request.error);
    });
}

// Push notification handler (for future use)
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/badge-72x72.png',
        data: data.data,
        actions: data.actions || []
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action) {
        // Handle action buttons
        switch (event.action) {
            case 'view-cart':
                event.waitUntil(clients.openWindow('/orders/cart/'));
                break;
            case 'view-quotes':
                event.waitUntil(clients.openWindow('/orders/quotes/'));
                break;
            default:
                break;
        }
    } else {
        // Handle notification click
        const url = event.notification.data?.url || '/';
        event.waitUntil(clients.openWindow(url));
    }
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
    const { type, data } = event.data;

    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
        case 'CACHE_URLS':
            event.waitUntil(cacheUrls(data.urls));
            break;
        case 'CLEAR_CACHE':
            event.waitUntil(clearCache(data.cacheName));
            break;
        default:
            break;
    }
});

// Helper function to cache specific URLs
async function cacheUrls(urls) {
    const cache = await caches.open(DYNAMIC_CACHE);
    return cache.addAll(urls);
}

// Helper function to clear specific cache
async function clearCache(cacheName) {
    return caches.delete(cacheName);
}