(() => {
    'use strict';

    const STORAGE_KEY = 'saathi_anon_id';
    const WARNING_ID = 'saathi-anon-warning';
    let cachedId = null;
    let storageHealthy = true;
    let warningScheduled = false;

    function storageAvailable() {
        try {
            const probeKey = '__saathi_storage_probe__';
            window.localStorage.setItem(probeKey, '1');
            window.localStorage.removeItem(probeKey);
            return true;
        } catch (error) {
            console.warn('Saathi anon_id storage unavailable', error);
            return false;
        }
    }

    storageHealthy = storageAvailable();

    function generateAnonId() {
        if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
            return globalThis.crypto.randomUUID();
        }
        const timePart = Date.now().toString(36);
        const randomPart = Math.random().toString(36).slice(2, 11);
        return `anon_${timePart}_${randomPart}`;
    }

    function ensureAnonId() {
        if (cachedId) {
            return cachedId;
        }

        let storedId = null;
        if (storageHealthy) {
            try {
                storedId = window.localStorage.getItem(STORAGE_KEY);
            } catch (error) {
                console.warn('Saathi anon_id read failed', error);
                storageHealthy = false;
            }
        }

        if (storedId) {
            cachedId = storedId;
            return cachedId;
        }

        cachedId = generateAnonId();
        if (storageHealthy) {
            try {
                window.localStorage.setItem(STORAGE_KEY, cachedId);
            } catch (error) {
                console.warn('Saathi anon_id write blocked', error);
                storageHealthy = false;
                scheduleWarning();
            }
        } else {
            scheduleWarning();
        }
        return cachedId;
    }

    function scheduleWarning() {
        if (warningScheduled) {
            return;
        }
        warningScheduled = true;

        const injectBanner = () => {
            if (document.getElementById(WARNING_ID)) {
                return;
            }
            const banner = document.createElement('div');
            banner.id = WARNING_ID;
            banner.textContent = 'Private mode detected: Saathi will reset your anonymous ID when this tab closes.';
            banner.style.cssText = [
                'position:fixed',
                'top:12px',
                'left:50%',
                'transform:translateX(-50%)',
                'background:#c05621',
                'color:#fff',
                'padding:10px 18px',
                'border-radius:999px',
                'font-size:13px',
                'z-index:2147483647',
                'box-shadow:0 12px 24px rgba(0,0,0,0.35)' 
            ].join(';');
            document.body.appendChild(banner);
            setTimeout(() => {
                banner.style.opacity = '0';
                banner.style.transition = 'opacity 0.6s ease';
                setTimeout(() => banner.remove(), 800);
            }, 6000);
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', injectBanner, { once: true });
        } else if (document.body) {
            injectBanner();
        } else {
            setTimeout(injectBanner, 500);
        }
    }

    const api = {
        getId: () => ensureAnonId(),
        ensure: () => ensureAnonId(),
        isPersistent: () => storageHealthy,
        headers(base = {}) {
            const id = ensureAnonId();
            if (!id) {
                return { ...base };
            }
            return { ...base, 'X-Anon-Id': id };
        },
        attachToPayload(payload = {}) {
            const id = ensureAnonId();
            if (!id || typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
                return payload;
            }
            return { ...payload, anon_id: id };
        }
    };

    globalThis.saathiAnon = api;
    globalThis.SAATHI_ANON_ID = ensureAnonId();
    if (!storageHealthy) {
        scheduleWarning();
    }
})();
