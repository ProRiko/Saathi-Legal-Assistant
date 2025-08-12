// Onboarding Wizard Functionality
class OnboardingWizard {
    constructor() {
        this.currentStep = 0;
        this.steps = [
            {
                title: "Legal Question Assistant",
                description: "Get AI-powered answers to your legal questions using Google's Gemini AI. Just type your question and receive instant insights.",
                action: "Ask Legal Questions Now →"
            },
            {
                title: "Document Generator",
                description: "Generate professional legal documents including contracts, agreements, and legal notices with AI assistance.",
                action: "Generate Legal Documents →"
            },
            {
                title: "Fee Calculator",
                description: "Calculate legal fees for various services and get transparent cost estimates for your legal needs.",
                action: "Calculate Legal Fees →"
            }
        ];
        this.init();
    }

    init() {
        this.createWizard();
        this.attachEventListeners();
        this.showWizard();
    }

    createWizard() {
        const wizard = document.createElement('div');
        wizard.className = 'onboarding-wizard';
        wizard.id = 'onboarding-wizard';
        wizard.style.display = 'none';
        
        wizard.innerHTML = `
            <div class="wizard-overlay" onclick="onboardingWizard.skipWizard()"></div>
            <div class="wizard-content">
                <h2>Welcome to Saathi Legal Assistant! 🏛️</h2>
                <p style="color: rgba(244, 241, 232, 0.8); margin-bottom: 30px;">
                    Let us show you around in 3 simple steps
                </p>
                
                <div class="wizard-steps" id="wizard-steps">
                    ${this.steps.map((step, index) => `
                        <div class="step-card ${index === 0 ? 'active' : ''}" data-step="${index}">
                            <div class="step-number">${index + 1}</div>
                            <h3>${step.title}</h3>
                            <p>${step.description}</p>
                        </div>
                    `).join('')}
                </div>
                
                <div class="wizard-actions">
                    <button class="wizard-btn secondary" onclick="onboardingWizard.previousStep()" id="prev-btn" style="display: none;">
                        ← Previous
                    </button>
                    <button class="wizard-btn secondary" onclick="onboardingWizard.skipWizard()">
                        Skip Tour
                    </button>
                    <button class="wizard-btn primary" onclick="onboardingWizard.nextStep()" id="next-btn">
                        Next Step →
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(wizard);
    }

    attachEventListeners() {
        // Click on step cards to navigate
        document.addEventListener('click', (e) => {
            if (e.target.closest('.step-card')) {
                const stepIndex = parseInt(e.target.closest('.step-card').dataset.step);
                this.goToStep(stepIndex);
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (document.getElementById('onboarding-wizard').style.display !== 'none') {
                switch(e.key) {
                    case 'ArrowRight':
                    case 'ArrowDown':
                        e.preventDefault();
                        this.nextStep();
                        break;
                    case 'ArrowLeft':
                    case 'ArrowUp':
                        e.preventDefault();
                        this.previousStep();
                        break;
                    case 'Escape':
                        e.preventDefault();
                        this.skipWizard();
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (this.currentStep === this.steps.length - 1) {
                            this.completeWizard();
                        } else {
                            this.nextStep();
                        }
                        break;
                }
            }
        });
    }

    showWizard() {
        // Check if user has seen the wizard before
        if (localStorage.getItem('saathi_onboarding_completed') === 'true') {
            return;
        }
        
        // Show wizard after page loads
        setTimeout(() => {
            document.getElementById('onboarding-wizard').style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }, 1000);
    }

    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.steps.length) {
            this.currentStep = stepIndex;
            this.updateUI();
        }
    }

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.updateUI();
        } else {
            this.completeWizard();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.updateUI();
        }
    }

    updateUI() {
        // Update step cards
        const stepCards = document.querySelectorAll('.step-card');
        stepCards.forEach((card, index) => {
            card.classList.toggle('active', index === this.currentStep);
        });

        // Update buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        
        prevBtn.style.display = this.currentStep === 0 ? 'none' : 'inline-block';
        nextBtn.textContent = this.currentStep === this.steps.length - 1 ? 'Get Started! 🚀' : 'Next Step →';

        // Add animation
        const wizardSteps = document.getElementById('wizard-steps');
        wizardSteps.style.transform = 'translateX(-10px)';
        wizardSteps.style.opacity = '0.7';
        
        setTimeout(() => {
            wizardSteps.style.transform = 'translateX(0)';
            wizardSteps.style.opacity = '1';
        }, 150);
    }

    completeWizard() {
        // Mark as completed
        localStorage.setItem('saathi_onboarding_completed', 'true');
        
        // Hide wizard with animation
        const wizard = document.getElementById('onboarding-wizard');
        wizard.style.animation = 'fadeOut 0.5s ease-out forwards';
        
        setTimeout(() => {
            wizard.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 500);

        // Show welcome message
        this.showWelcomeMessage();
    }

    skipWizard() {
        localStorage.setItem('saathi_onboarding_completed', 'true');
        
        const wizard = document.getElementById('onboarding-wizard');
        wizard.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    showWelcomeMessage() {
        // Create temporary welcome message
        const message = document.createElement('div');
        message.className = 'welcome-message';
        message.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #2c5530, #3d7341);
                color: #f4f1e8;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(44, 85, 48, 0.3);
                z-index: 1000;
                max-width: 300px;
                animation: slideInRight 0.5s ease-out;
            ">
                <h4 style="margin: 0 0 10px 0;">Welcome aboard! 🎉</h4>
                <p style="margin: 0; font-size: 0.9em; opacity: 0.9;">
                    You're all set to explore Saathi Legal Assistant. Start with any feature that interests you!
                </p>
            </div>
        `;
        
        document.body.appendChild(message);
        
        // Remove message after 5 seconds
        setTimeout(() => {
            message.style.animation = 'slideOutRight 0.5s ease-out forwards';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 500);
        }, 5000);
    }

    // Method to reset onboarding (for testing)
    resetOnboarding() {
        localStorage.removeItem('saathi_onboarding_completed');
        location.reload();
    }
}

// CSS animations for wizard
const wizardStyles = `
@keyframes fadeOut {
    to {
        opacity: 0;
        transform: scale(0.95);
    }
}

@keyframes slideInRight {
    from {
        transform: translateX(300px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(300px);
        opacity: 0;
    }
}

.wizard-content {
    animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
    from {
        transform: translateY(50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
`;

// Add styles to page
const styleSheet = document.createElement('style');
styleSheet.textContent = wizardStyles;
document.head.appendChild(styleSheet);

// Initialize wizard when DOM is ready
let onboardingWizard;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        onboardingWizard = new OnboardingWizard();
    });
} else {
    onboardingWizard = new OnboardingWizard();
}

// Global function for console testing
window.resetOnboarding = () => {
    if (onboardingWizard) {
        onboardingWizard.resetOnboarding();
    }
};
