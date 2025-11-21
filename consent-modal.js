(function () {
    const CONSENT_KEY = 'saathi_consent_flag_v1';
    const SESSION_KEY = 'saathi_consent_session_v1';
    const CONSENT_SCOPE = 'core-app-access';

    function ensureSessionId() {
        try {
            const storedId = window.localStorage.getItem(SESSION_KEY);
            if (storedId) {
                return storedId;
            }
            const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
            window.localStorage.setItem(SESSION_KEY, newId);
            return newId;
        } catch (error) {
            return `session_${Date.now()}`;
        }
    }

    function hasConsent() {
        try {
            return window.localStorage.getItem(CONSENT_KEY) === 'granted';
        } catch (error) {
            return false;
        }
    }

    function setBodyScroll(lock) {
        document.documentElement.style.overflow = lock ? 'hidden' : '';
        document.body.style.overflow = lock ? 'hidden' : '';
    }

    function createStyleTag() {
        const style = document.createElement('style');
        style.id = 'saathi-consent-style';
        style.textContent = `
            .saathi-consent-overlay {
                position: fixed;
                inset: 0;
                background: rgba(10, 12, 20, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                padding: 20px;
            }
            .saathi-consent-modal {
                max-width: 520px;
                width: 100%;
                background: #101828;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 18px;
                padding: 32px;
                color: #f8f9fc;
                font-family: 'Inter', 'Segoe UI', system-ui, -apple-system;
                box-shadow: 0 30px 90px rgba(0, 0, 0, 0.45);
            }
            .saathi-consent-modal h2 {
                margin-top: 0;
                font-size: 1.75rem;
            }
            .saathi-consent-modal p,
            .saathi-consent-modal li {
                line-height: 1.5;
                color: #e2e8f0;
            }
            .saathi-consent-modal ul {
                padding-left: 18px;
            }
            .saathi-consent-actions {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                margin-top: 24px;
            }
            .saathi-consent-actions button {
                flex: 1;
                min-width: 140px;
                border-radius: 999px;
                border: none;
                padding: 12px 18px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
            }
            .saathi-consent-accept {
                background: linear-gradient(120deg, #f7b733, #fc4a1a);
                color: #0b132b;
            }
            .saathi-consent-decline {
                background: transparent;
                color: #f8f9fc;
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            .saathi-consent-status {
                margin-top: 16px;
                font-size: 0.95rem;
                min-height: 22px;
                color: #f8d7da;
            }
        `;
        document.head.appendChild(style);
    }

    async function recordConsent(statusElement, acceptButton, declineButton) {
        acceptButton.disabled = true;
        declineButton.disabled = true;
        statusElement.textContent = 'Recording your consent...';

        const payload = {
            session_id: ensureSessionId(),
            timestamp: new Date().toISOString(),
            scope: CONSENT_SCOPE,
        };

        try {
            const response = await fetch('/api/consent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Failed to store consent');
            }

            window.localStorage.setItem(CONSENT_KEY, 'granted');
            statusElement.textContent = 'Consent recorded. Loading experience...';
            setTimeout(() => {
                removeModal();
            }, 600);
        } catch (error) {
            statusElement.textContent = 'Unable to save consent. Please try again.';
            acceptButton.disabled = false;
            declineButton.disabled = false;
        }
    }

    function removeModal() {
        setBodyScroll(false);
        const overlay = document.getElementById('saathi-consent-overlay');
        if (overlay) {
            overlay.remove();
        }
        const style = document.getElementById('saathi-consent-style');
        if (style) {
            style.remove();
        }
    }

    function showModal() {
        createStyleTag();
        setBodyScroll(true);

        const overlay = document.createElement('div');
        overlay.id = 'saathi-consent-overlay';
        overlay.className = 'saathi-consent-overlay';
        overlay.innerHTML = `
            <div class="saathi-consent-modal" role="dialog" aria-modal="true" aria-labelledby="saathi-consent-title">
                <h2 id="saathi-consent-title">Your Privacy & Consent</h2>
                <p>To keep Saathi transparent and secure, we need your permission before you continue.</p>
                <ul>
                    <li>User inputs and generated documents may be securely stored to provide and improve the service.</li>
                    <li>Data is never sold or shared with third parties.</li>
                    <li>You can request deletion of your data at any time.</li>
                </ul>
                <div class="saathi-consent-actions">
                    <button class="saathi-consent-accept">Accept & Continue</button>
                    <button class="saathi-consent-decline">Decline</button>
                </div>
                <div class="saathi-consent-status" aria-live="polite"></div>
            </div>
        `;
        document.body.appendChild(overlay);

        const acceptButton = overlay.querySelector('.saathi-consent-accept');
        const declineButton = overlay.querySelector('.saathi-consent-decline');
        const statusElement = overlay.querySelector('.saathi-consent-status');

        if (acceptButton && declineButton) {
            acceptButton.addEventListener('click', () => recordConsent(statusElement, acceptButton, declineButton));
            declineButton.addEventListener('click', () => {
                statusElement.textContent = 'Consent declined. You can close the tab or return anytime.';
                declineButton.disabled = true;
            });
        }
    }

    function initConsentGate() {
        if (hasConsent()) {
            return;
        }
        showModal();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConsentGate);
    } else {
        initConsentGate();
    }
})();
