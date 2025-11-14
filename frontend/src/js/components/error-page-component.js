/**
 * Error Page Component
 * Alpine.js component for displaying user-friendly error pages
 */

window.errorPageComponent = function() {
    return {
        // State
        error: null,
        isVisible: false,
        isRetrying: false,
        retryCount: 0,
        maxRetries: 3,

        // Initialize component
        init() {
            // Listen for error events
            window.addEventListener('show-error-page', (event) => {
                this.showError(event.detail);
            });

            // Auto-hide after timeout (optional)
            // this.autoHideTimeout = null;
        },

        // Show error
        showError(errorDetail) {
            this.error = errorDetail;
            this.isVisible = true;
            this.retryCount = errorDetail.retryCount || 0;

            // Focus on error title for accessibility
            this.$nextTick(() => {
                const focusElement = this.$el.querySelector('[data-error-focus]');
                if (focusElement) {
                    focusElement.focus();
                }
            });
        },

        // Hide error
        hideError() {
            this.isVisible = false;
            this.$nextTick(() => {
                this.error = null;
                this.isRetrying = false;
                this.retryCount = 0;
            });
        },

        // Get error icon type
        getErrorIcon() {
            if (!this.error) return 'generic';

            switch (this.error.type) {
                case 'network':
                    return 'network';
                case 'not-found':
                case '404':
                    return 'not-found';
                case 'server':
                case '500':
                    return 'server';
                case 'timeout':
                    return 'timeout';
                case 'forbidden':
                case '403':
                    return 'forbidden';
                default:
                    return 'generic';
            }
        },

        // Get error classes
        getErrorClasses() {
            const classes = ['error-page'];
            if (this.error?.severity === 'critical') {
                classes.push('error-page--critical');
            }
            return classes.join(' ');
        },

        // Can retry?
        canRetry() {
            if (!this.error) return false;
            if (this.error.config?.allowRetry === false) return false;
            return this.retryCount < this.maxRetries;
        },

        // Retries exhausted?
        retriesExhausted() {
            return this.retryCount >= this.maxRetries;
        },

        // Get retry button text
        getRetryButtonText() {
            if (this.isRetrying) return 'Retrying...';
            return this.retryCount > 0 ? 'Try Again' : 'Retry';
        },

        // Get error timestamp
        getErrorTimestamp() {
            if (!this.error?.timestamp) return new Date().toLocaleString();
            return new Date(this.error.timestamp).toLocaleString();
        },

        // Retry operation
        async retryOperation() {
            if (!this.canRetry()) return;

            this.isRetrying = true;
            this.retryCount++;

            try {
                // If error has a retry callback, use it
                if (this.error?.config?.retryCallback) {
                    await this.error.config.retryCallback();
                    this.hideError();
                } else {
                    // Default: refresh page
                    this.refreshPage();
                }
            } catch (err) {
                console.error('Retry failed:', err);
                this.isRetrying = false;
                
                // Update error with new retry count
                if (this.error) {
                    this.error.retryCount = this.retryCount;
                }
            }
        },

        // Go to home
        goHome() {
            window.location.href = '/';
        },

        // Refresh page
        refreshPage() {
            window.location.reload();
        },

        // Report error
        async reportError() {
            if (!this.error) return;

            const errorReport = {
                type: this.error.type,
                message: this.error.message,
                timestamp: this.getErrorTimestamp(),
                retryCount: this.retryCount,
                userAgent: navigator.userAgent,
                url: window.location.href,
                originalError: this.error.originalError
            };

            try {
                // Copy to clipboard
                await navigator.clipboard.writeText(JSON.stringify(errorReport, null, 2));
                
                // Show success notification
                window.dispatchEvent(new CustomEvent('show-notification', {
                    detail: {
                        message: 'Error details copied to clipboard',
                        type: 'success',
                        duration: 3000
                    }
                }));
            } catch (err) {
                console.error('Failed to copy error report:', err);
                
                // Fallback: show error details in console
                console.log('Error Report:', errorReport);
                alert('Error details logged to console (F12 to view)');
            }
        }
    };
};
