/**
 * Login page Alpine.js component.
 * 
 * Handles email OTP authentication flow.
 */

function loginApp() {
    return {
        email: '',
        otpCode: '',
        otpSent: false,
        loading: false,
        error: '',
        expiresInMinutes: 15,
        timeRemaining: 0,
        timerInterval: null,
        mailgunConfigured: true,

        async init() {
            // Check if Mailgun is configured
            await this.checkMailgunConfig();
            
            // Check if already authenticated
            const token = localStorage.getItem('auth_token');
            if (token) {
                // Verify token is still valid
                const isValid = await this.verifyToken(token);
                if (isValid) {
                    // Redirect to main app
                    window.location.href = '/';
                }
            }
        },

        async checkMailgunConfig() {
            // For now, assume configured
            // Will be caught during OTP request if not configured
            this.mailgunConfigured = true;
        },

        async requestOTP() {
            this.loading = true;
            this.error = '';

            try {
                const response = await fetch('/api/auth/otp/request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: this.email
                    })
                });

                if (!response.ok) {
                    const data = await response.json();
                    
                    if (response.status === 503) {
                        // Mailgun not configured
                        this.mailgunConfigured = false;
                        this.error = data.detail || 'Email service is not configured';
                    } else if (response.status === 429) {
                        // Rate limited
                        this.error = data.detail || 'Too many requests. Please try again later.';
                    } else {
                        this.error = data.detail || 'Failed to send OTP';
                    }
                    return;
                }

                const data = await response.json();
                this.expiresInMinutes = data.expires_in_minutes || 15;
                this.otpSent = true;
                
                // Start countdown timer
                this.startCountdown(this.expiresInMinutes * 60);

                // Auto-focus the OTP code input
                this.$nextTick(() => {
                    const input = this.$refs.otpInput;
                    if (input) input.focus();
                });

                console.log('OTP sent successfully');
            } catch (err) {
                console.error('Error requesting OTP:', err);
                this.error = 'Network error. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        async verifyOTP() {
            this.loading = true;
            this.error = '';

            try {
                const response = await fetch('/api/auth/otp/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: this.email,
                        code: this.otpCode
                    })
                });

                if (!response.ok) {
                    const data = await response.json();
                    this.error = data.detail || 'Invalid or expired code';
                    return;
                }

                const data = await response.json();
                
                // Store token and user info
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_profile', JSON.stringify(data.user));

                console.log('Login successful');

                // Redirect to main app
                window.location.href = '/';
            } catch (err) {
                console.error('Error verifying OTP:', err);
                this.error = 'Network error. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        async verifyToken(token) {
            try {
                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                return response.ok;
            } catch (err) {
                console.error('Error verifying token:', err);
                return false;
            }
        },

        startCountdown(seconds) {
            this.timeRemaining = seconds;
            
            // Clear existing timer if any
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }

            this.timerInterval = setInterval(() => {
                this.timeRemaining--;
                
                if (this.timeRemaining <= 0) {
                    clearInterval(this.timerInterval);
                    this.error = 'Code has expired. Please request a new one.';
                }
            }, 1000);
        },

        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        },

        resetForm() {
            this.otpSent = false;
            this.otpCode = '';
            this.error = '';
            this.timeRemaining = 0;
            
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }
        },

        loginWithOIDC(provider) {
            // Redirect to OIDC endpoint
            window.location.href = `/api/auth/oidc/${provider}`;
        }
    };
}

