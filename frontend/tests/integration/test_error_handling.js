/**
 * Integration Test: Error Handling
 * 
 * Tests that the footer component handles various error conditions gracefully
 * This test covers Scenario 4 from quickstart.md
 */

describe('Footer Error Handling Integration', () => {
    let originalFetch;
    let originalConsoleError;
    let consoleErrors;

    beforeEach(() => {
        originalFetch = global.fetch;
        originalConsoleError = console.error;
        
        consoleErrors = [];
        console.error = jest.fn((...args) => {
            consoleErrors.push(args);
        });
        
        global.fetch = jest.fn();
        document.body.innerHTML = '';
    });

    afterEach(() => {
        global.fetch = originalFetch;
        console.error = originalConsoleError;
        document.body.innerHTML = '';
    });

    test('should handle API server unavailable gracefully', async () => {
        // Mock network error (server down)
        global.fetch.mockRejectedValue(new Error('Failed to fetch'));

        document.body.innerHTML = `
            <div id="app">
                <main id="main-content">
                    <h1>Main Content</h1>
                    <p>This should remain visible even when footer API fails</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        // This test MUST FAIL initially - components don't exist yet
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        // Should not throw when API fails
        await expect(FooterComponent.initialize()).resolves.not.toThrow();
        
        await new Promise(resolve => setTimeout(resolve, 200));

        // Main content should remain accessible
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();
        expect(mainContent.textContent).toContain('This should remain visible');

        // Footer should show default content or graceful fallback
        const footerContainer = document.querySelector('#footer-container');
        expect(footerContainer).toBeTruthy();

        // Should either show default footer or be empty (not crash)
        const footerElement = document.querySelector('[data-testid="footer"]');
        if (footerElement) {
            // If footer renders, it should show default copyright
            expect(footerElement.textContent).toContain('© 2025 Vagrantfile Generator.');
        }

        // Error should be logged but not thrown
        expect(consoleErrors.length).toBeGreaterThan(0);
    });

    test('should handle malformed API responses', async () => {
        // Mock malformed JSON response
        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => {
                throw new Error('Invalid JSON');
            }
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        await expect(FooterComponent.initialize()).resolves.not.toThrow();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Should handle gracefully - either show default or empty
        const footerContainer = document.querySelector('#footer-container');
        expect(footerContainer).toBeTruthy();

        // Should not crash the page
        expect(document.body).toBeTruthy();
        expect(consoleErrors.length).toBeGreaterThan(0);
    });

    test('should handle API returning error status', async () => {
        // Mock API error response (500, 404, etc.)
        global.fetch.mockResolvedValue({
            ok: false,
            status: 500,
            json: async () => ({
                status: 'error',
                message: 'Internal server error',
                code: 'INTERNAL_ERROR'
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        await expect(FooterComponent.initialize()).resolves.not.toThrow();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Should display default content when API returns error
        const footerContainer = document.querySelector('#footer-container');
        expect(footerContainer).toBeTruthy();

        // Should show default copyright text
        const footerElement = document.querySelector('[data-testid="footer"]');
        if (footerElement) {
            expect(footerElement.textContent).toContain('© 2025 Vagrantfile Generator.');
        }
    });

    test('should handle corrupted markdown files', async () => {
        // Mock successful discovery
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'corrupted.md', isValid: false }],
                excluded: [],
                errors: ['File corrupted.md has invalid content']
            })
        });

        // Mock corrupted file content
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'corrupted.md',
                    title: null,
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '\x00\x01\x02invalid binary content',
                    isValid: false
                },
                warnings: ['Invalid UTF-8 content', 'No heading found']
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Should handle corrupted files gracefully
        const corruptedLink = document.querySelector('[data-page="corrupted"]');
        
        if (corruptedLink) {
            // Link should either be disabled or show error state
            const isDisabled = corruptedLink.hasAttribute('disabled') ||
                             corruptedLink.classList.contains('error') ||
                             corruptedLink.classList.contains('disabled') ||
                             corruptedLink.getAttribute('aria-disabled') === 'true';

            expect(isDisabled).toBeTruthy();
            
            // Should have visual indication of error
            expect(
                corruptedLink.textContent.includes('Error') ||
                corruptedLink.classList.contains('error') ||
                corruptedLink.querySelector('.error-icon')
            ).toBeTruthy();
        }
    });

    test('should handle navigation to non-existent pages', async () => {
        // Mock initial setup
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'valid-page.md', isValid: true }],
                excluded: [],
                errors: []
            })
        });

        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Valid Page',
                    isExternal: false,
                    renderedContent: '<h1>Valid Page</h1>'
                }
            })
        });

        document.body.innerHTML = `
            <div id="app">
                <main id="main-content"><h1>Home</h1></main>
                <div id="footer-container"></div>
            </div>
        `;

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        const StaticPageRouter = require('../../../src/js/router/StaticPageRouter.js');
        
        await FooterComponent.initialize();
        StaticPageRouter.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Simulate direct navigation to non-existent page
        const currentUrl = window.location.href;
        
        // Mock 404 response for non-existent page
        global.fetch.mockRejectedValueOnce(new Error('404 Not Found'));
        
        // Try to navigate to non-existent page programmatically
        if (StaticPageRouter.navigateToPage) {
            await StaticPageRouter.navigateToPage('non-existent-page');
        }
        
        await new Promise(resolve => setTimeout(resolve, 100));

        // Should show error page or remain on current page
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();

        const hasErrorContent = mainContent.innerHTML.includes('404') ||
                               mainContent.innerHTML.includes('Not Found') ||
                               mainContent.innerHTML.includes('Error') ||
                               mainContent.innerHTML.includes('Home'); // Stayed on home

        expect(hasErrorContent).toBeTruthy();

        // Footer should remain functional
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();
    });

    test('should handle slow API responses without blocking UI', async () => {
        // Mock very slow API response
        let resolveSlowRequest;
        const slowPromise = new Promise(resolve => {
            resolveSlowRequest = resolve;
        });

        global.fetch.mockImplementation(() => slowPromise);

        document.body.innerHTML = `
            <div id="app">
                <main id="main-content">
                    <h1>Immediate Content</h1>
                    <p>This should be visible immediately</p>
                    <button id="test-button">Click me</button>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        const startTime = Date.now();

        // Start footer initialization but don't await
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        FooterComponent.initialize(); // Don't await

        // UI should be responsive immediately
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();
        expect(mainContent.textContent).toContain('Immediate Content');

        // Button should be clickable
        const button = document.querySelector('#test-button');
        expect(button).toBeTruthy();
        
        let buttonClicked = false;
        button.addEventListener('click', () => {
            buttonClicked = true;
        });
        
        button.click();
        expect(buttonClicked).toBeTruthy();

        // Should not have taken long to get here
        const elapsedTime = Date.now() - startTime;
        expect(elapsedTime).toBeLessThan(100);

        // Now resolve the slow request
        resolveSlowRequest({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [],
                excluded: [],
                errors: []
            })
        });

        await new Promise(resolve => setTimeout(resolve, 100));

        // UI should still be responsive
        expect(document.querySelector('#main-content')).toBeTruthy();
    });

    test('should handle multiple concurrent API failures', async () => {
        // Mock multiple API endpoints failing
        global.fetch.mockImplementation((url) => {
            if (url.includes('/api/footer/files')) {
                return Promise.reject(new Error('Files API down'));
            } else if (url.includes('/api/footer/content')) {
                return Promise.reject(new Error('Content API down'));
            }
            return Promise.reject(new Error('General API failure'));
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        // Should handle multiple failures gracefully
        await expect(FooterComponent.initialize()).resolves.not.toThrow();
        await new Promise(resolve => setTimeout(resolve, 200));

        // Should not crash or leave page in broken state
        expect(document.querySelector('#footer-container')).toBeTruthy();
        expect(document.body).toBeTruthy();
        
        // Should have logged multiple errors
        expect(consoleErrors.length).toBeGreaterThan(0);
    });

    test('should recover from temporary API failures', async () => {
        let apiCallCount = 0;
        
        // First call fails, second succeeds
        global.fetch.mockImplementation(() => {
            apiCallCount++;
            if (apiCallCount === 1) {
                return Promise.reject(new Error('Temporary failure'));
            }
            return Promise.resolve({
                ok: true,
                status: 200,
                json: async () => ({
                    status: 'success',
                    files: [{ filename: 'recovery-test.md', isValid: true }],
                    excluded: [],
                    errors: []
                })
            });
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        // First attempt should fail gracefully
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // If component supports retry mechanism, test it
        if (FooterComponent.retry) {
            await FooterComponent.retry();
            await new Promise(resolve => setTimeout(resolve, 100));

            // Should now show content from successful API call
            const footerElement = document.querySelector('[data-testid="footer"]');
            if (footerElement) {
                const recoveryLink = document.querySelector('[data-page="recovery-test"]');
                expect(recoveryLink).toBeTruthy();
            }
        }

        // Should have made multiple API calls
        expect(apiCallCount).toBeGreaterThan(1);
    });

    test('should handle DOM manipulation errors gracefully', async () => {
        // Mock successful API but broken DOM
        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [],
                excluded: [],
                errors: []
            })
        });

        // Create footer container but make it non-functional
        document.body.innerHTML = '<div id="footer-container"></div>';
        
        // Mock querySelector to return null (simulate DOM issues)
        const originalQuerySelector = document.querySelector;
        document.querySelector = jest.fn().mockReturnValue(null);

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        // Should not throw when DOM manipulation fails
        await expect(FooterComponent.initialize()).resolves.not.toThrow();

        // Restore querySelector
        document.querySelector = originalQuerySelector;
        
        // Should have logged errors
        expect(consoleErrors.length).toBeGreaterThan(0);
    });
});