(() => {
    'use strict';

    const CONSENT_KEY = 'saathi_consent';
    const ANON_ID_KEY = 'saathi_anon_id';
    const LEGACY_ACCEPT_KEYS = [{ key: 'saathi_consent_flag_v1', acceptedValue: 'granted' }];
    const CONSENT_SCOPE = Object.freeze({
        store_messages: true,
        store_documents: true,
    });
    const CONSENT_ENDPOINT = '/api/consent';
    const DECLINE_REDIRECT = '/consent-required.html';
    const FOCUSABLE_SELECTORS = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])'
    ].join(', ');

    let modalOpen = false;
    let cleanupFocusTrap = null;
    let previousHtmlOverflow = '';
    let previousBodyOverflow = '';

    function safeGet(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (error) {
            console.warn('Consent storage read failed', error);
            return null;
        }
    }

    function safeSet(key, value) {
        try {
            window.localStorage.setItem(key, value);
            return true;
        } catch (error) {
            console.warn('Consent storage write failed', error);
            return false;
        }
    }

    function migrateLegacyFlags() {
        LEGACY_ACCEPT_KEYS.forEach(({ key, acceptedValue }) => {
            const stored = safeGet(key);
            if (stored && (!acceptedValue || stored === acceptedValue)) {
                safeSet(CONSENT_KEY, 'yes');
            }
        });
    }

    function ensureAnonId() {
        if (globalThis.saathiAnon && typeof globalThis.saathiAnon.ensure === 'function') {
            return globalThis.saathiAnon.ensure();
        }
        const existing = safeGet(ANON_ID_KEY);
        if (existing) {
            return existing;
        }
        const generated = (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function')
            ? globalThis.crypto.randomUUID()
            : `anon_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
        safeSet(ANON_ID_KEY, generated);
        return generated;
    }

    function lockPage() {
        if (!document.body) {
            return;
        }
        previousHtmlOverflow = document.documentElement.style.overflow;
        previousBodyOverflow = document.body.style.overflow;
        document.documentElement.style.overflow = 'hidden';
        document.body.style.overflow = 'hidden';
    }

    function unlockPage() {
        if (!document.body) {
            return;
        }
        document.documentElement.style.overflow = previousHtmlOverflow;
        document.body.style.overflow = previousBodyOverflow;
    }

    function redirectToInfoPage() {
        window.location.replace(DECLINE_REDIRECT);
    }

    function trapFocus(container) {
        if (!container) {
            return () => {};
        }
        const focusable = Array.from(container.querySelectorAll(FOCUSABLE_SELECTORS));
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        function handleKeydown(event) {
            if (event.key === 'Tab') {
                if (!focusable.length) {
                    event.preventDefault();
                    return;
                }
                if (event.shiftKey && document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                    return;
                }
                if (!event.shiftKey && document.activeElement === last) {
                    event.preventDefault();
                    first.focus();
                }
            } else if (event.key === 'Escape') {
                event.preventDefault();
            }
        }

        container.addEventListener('keydown', handleKeydown);
        if (first) {
            first.focus();
        }

        return () => container.removeEventListener('keydown', handleKeydown);
    }

    function removeModal() {
        const overlay = document.getElementById('saathi-consent-overlay');
        if (overlay && overlay.parentElement) {
            overlay.parentElement.removeChild(overlay);
        }
        if (cleanupFocusTrap) {
            cleanupFocusTrap();
            cleanupFocusTrap = null;
        }
        unlockPage();
        modalOpen = false;
    }

    function getUserIdHint() {
        const body = document.body;
        if (body && body.dataset && body.dataset.saathiUserId) {
            return body.dataset.saathiUserId;
        }
        if (typeof globalThis.SAATHI_USER_ID === 'string' && globalThis.SAATHI_USER_ID.trim().length > 0) {
            return globalThis.SAATHI_USER_ID.trim();
        }
        return null;
    }

    async function submitConsent(statusElement, acceptButton, declineButton) {
        if (!statusElement || !acceptButton || !declineButton) {
            return;
        }
        acceptButton.disabled = true;
        declineButton.disabled = true;
        statusElement.textContent = 'Saving your preference...';

        const payload = {
            anon_id: ensureAnonId(),
            user_id: getUserIdHint(),
            scope: CONSENT_SCOPE,
        };

        try {
            const response = await fetch(CONSENT_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`Consent API rejected with status ${response.status}`);
            }

            if (!safeSet(CONSENT_KEY, 'yes')) {
                statusElement.textContent = 'We recorded your consent, but your browser blocked local storage. Please enable storage and try again.';
                acceptButton.disabled = false;
                declineButton.disabled = false;
                return;
            }

            statusElement.textContent = 'Thanks! Your experience is unlocked.';
            setTimeout(removeModal, 600);
        } catch (error) {
            console.error('Consent submission failed:', error);
            statusElement.textContent = 'We could not reach Saathi servers. Check your connection and retry.';
            acceptButton.disabled = false;
            declineButton.disabled = false;
        }
    }

    function handleDecline(statusElement, acceptButton, declineButton) {
        if (!statusElement || !acceptButton || !declineButton) {
            return;
        }
        acceptButton.disabled = true;
        declineButton.disabled = true;

        if (!safeSet(CONSENT_KEY, 'declined')) {
            statusElement.textContent = 'We need to remember your choice locally. Please enable storage or close this tab.';
            acceptButton.disabled = false;
            declineButton.disabled = false;
            return;
        }

        statusElement.textContent = 'Redirecting you to learn why consent is needed...';
        setTimeout(redirectToInfoPage, 500);
    }

    function buildModalMarkup() {
        return `
            <div class="saathi-consent-modal" role="dialog" aria-modal="true" aria-labelledby="saathi-consent-title" aria-describedby="saathi-consent-details">
                <h2 id="saathi-consent-title">We Respect Your Consent</h2>
                <p>Saathi securely processes limited data so we can provide reliable legal guidance.</p>
                <ul id="saathi-consent-details">
                    <li>We store chat inputs and generated documents to provide and improve the service.</li>
                    <li>We do NOT sell or share data with third parties.</li>
                    <li>You can request deletion anytime via privacy@saathilegal.in.</li>
                </ul>
                <p class="saathi-consent-meta">Your choice stays saved on this device. Withdraw consent anytime from Settings or by emailing us.</p>
                <div class="saathi-consent-actions">
                    <button type="button" class="saathi-consent-accept" data-consent-action="accept">Accept & Continue</button>
                    <button type="button" class="saathi-consent-decline" data-consent-action="decline">Decline</button>
                </div>
                <div class="saathi-consent-status" aria-live="polite"></div>
            </div>
        `;
    }

    function showModal() {
        if (modalOpen || !document.body) {
            return;
        }
        modalOpen = true;
        lockPage();

        const overlay = document.createElement('div');
        overlay.id = 'saathi-consent-overlay';
        overlay.className = 'saathi-consent-overlay';
        overlay.innerHTML = buildModalMarkup();
        document.body.appendChild(overlay);

        const modal = overlay.querySelector('.saathi-consent-modal');
        const acceptButton = overlay.querySelector('[data-consent-action="accept"]');
        const declineButton = overlay.querySelector('[data-consent-action="decline"]');
        const statusElement = overlay.querySelector('.saathi-consent-status');

        cleanupFocusTrap = trapFocus(modal);

        if (acceptButton) {
            acceptButton.addEventListener('click', () => submitConsent(statusElement, acceptButton, declineButton));
        }
        if (declineButton) {
            declineButton.addEventListener('click', () => handleDecline(statusElement, acceptButton, declineButton));
        }
    }

    function initConsentFlow() {
        migrateLegacyFlags();

        const body = document.body;
        if (!body) {
            return;
        }

        if (body.getAttribute('data-skip-consent-modal') === 'true') {
            return;
        }

        const currentFlag = safeGet(CONSENT_KEY);
        if (currentFlag === 'yes') {
            return;
        }
        if (currentFlag === 'declined') {
            redirectToInfoPage();
            return;
        }

        showModal();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConsentFlow, { once: true });
    } else {
        initConsentFlow();
    }
})();
