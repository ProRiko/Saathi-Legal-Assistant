(() => {
  'use strict';

  const CONSENT_KEY = 'saathi_consent';
  const ANON_ID_KEY = 'saathi_anon_id';
  const EVENT_ENDPOINT = '/api/event';

  function hasConsent() {
    try { return window.localStorage.getItem(CONSENT_KEY) === 'yes'; }
    catch { return false; }
  }

  function getAnonId() {
    try { return window.localStorage.getItem(ANON_ID_KEY) || null; }
    catch { return null; }
  }

  function buildHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const anon = getAnonId();
    if (anon) headers['X-Anon-Id'] = anon;
    return headers;
  }

  function postEvent(payload) {
    if (!hasConsent()) return;
    try {
      fetch(EVENT_ENDPOINT, {
        method: 'POST',
        headers: buildHeaders(),
        body: JSON.stringify(payload),
        keepalive: true,
        credentials: 'same-origin',
      }).catch(() => {});
    } catch (_) { /* no-op */ }
  }

  function trackEvent(event, properties) {
    postEvent({
      event,
      properties: properties || {},
      url: location.pathname,
      ts: new Date().toISOString(),
    });
  }

  function trackPageView() {
    trackEvent('page_view', { title: document.title });
  }

  // Expose API
  window.saathiAnalytics = { trackEvent, trackPageView };

  // Auto-fire page view after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', trackPageView, { once: true });
  } else {
    trackPageView();
  }
})();
