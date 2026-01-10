importScripts('https://www.gstatic.com/firebasejs/12.4.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.4.0/firebase-messaging-compat.js');

const firebaseConfig = {
  apiKey: "AIzaSyCKmvxH0K1dyYqvJl5whVu2HYC4i-TsVEc",
  authDomain: "oxduerp.firebaseapp.com",
  projectId: "oxduerp",
  storageBucket: "oxduerp.firebasestorage.app",
  messagingSenderId: "980764244945",
  appId: "1:980764244945:web:1db7d8fd89ffe55e167ef0",
  measurementId: "G-NS90J1MG9Q"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

console.log('✅ FCM Service Worker initialized');

/* ✅ Keep only this push handler — removes duplicates */
self.addEventListener('push', function (event) {
  try {
    let payloadJson = {};
    if (event.data) {
      try { payloadJson = event.data.json(); }
      catch { payloadJson = { notification: { title: 'Notification', body: event.data.text() } }; }
    }

    const n = payloadJson.notification || {};
    const d = payloadJson.data || payloadJson;

    const title = n.title || d.title || 'New Notification';
    const body  = n.body  || d.body  || 'You have a new message';
    const icon  = n.icon  || '/static/app/assets/images/logo/manifest-logo.png';
    const tag   = d.tag || n.tag || (d.leave_id ? `leave-${d.leave_id}` : 'default-tag');

    const options = {
      body,
      icon,
      badge: n.badge || icon,
      image: n.image || undefined,
      tag, // ensures merging same leave
      data: { ...d, receivedAt: Date.now() },
      requireInteraction: !!(d.requireInteraction || n.requireInteraction),
      actions: n.actions || [{ action: 'view', title: 'Open' }, { action: 'close', title: 'Close' }]
    };

    event.waitUntil(self.registration.showNotification(title, options));
  } catch (err) {
    console.error('Error handling push event', err);
  }
});

/* ✅ Keep your notificationclick handler (unchanged) */
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  const data = event.notification?.data || {};
  const leaveId = data.leave_id || data.leaveId || null;
  const action = event.action;

  if (action === 'close') return;
  let url = '/';
  if (leaveId) url = `/masters/leave-requests/${leaveId}/`;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
