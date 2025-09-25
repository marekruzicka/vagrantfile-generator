/**
 * Integration Test: External Link Handling
 * 
 * Tests that external links in footer navigation open in new tabs/windows
 * This test covers Scenario 3 from quickstart.md
 */

describe('External Link Handling Integration', () => {
    let originalFetch;
    let originalWindowOpen;

    beforeEach(() => {
        originalFetch = global.fetch;
        originalWindowOpen = window.open;
        
        global.fetch = jest.fn();
        window.open = jest.fn();
        
        // Clean up DOM
        document.body.innerHTML = '';
    });

    afterEach(() => {
        global.fetch = originalFetch;
        window.open = originalWindowOpen;
        document.body.innerHTML = '';
    });

    test('should open external links in new tab when clicked', async () => {
        // Mock footer files discovery with external link
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'github.md', path: 'backend/data/footer/github.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock github.md content retrieval - external link
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'github.md',
                    title: 'GitHub Repository',
                    isExternal: true,
                    externalUrl: 'https://github.com/marekruzicka/vagrantfile-generator',
                    rawContent: '# [GitHub Repository](https://github.com/marekruzicka/vagrantfile-generator)\n\nVisit our GitHub repository...',
                    renderedContent: '<h1><a href="https://github.com/marekruzicka/vagrantfile-generator">GitHub Repository</a></h1><p>Visit our GitHub repository...</p>',
                    lastModified: '2025-09-25T09:15:00Z',
                    isValid: true
                },
                warnings: []
            })
        });

        document.body.innerHTML = `
            <div id="app">
                <main id="main-content">
                    <h1>Main Page</h1>
                    <p>This should remain when external link is clicked</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        // This test MUST FAIL initially - components don't exist yet
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Find the GitHub link in footer
        const githubLink = document.querySelector('[data-page="github"]');
        expect(githubLink).toBeTruthy();
        expect(githubLink.textContent).toContain('GitHub Repository');

        // External link should have proper attributes
        expect(githubLink.hasAttribute('target')).toBeTruthy();
        expect(githubLink.getAttribute('target')).toBe('_blank');
        expect(githubLink.hasAttribute('rel')).toBeTruthy();
        expect(githubLink.getAttribute('rel')).toContain('noopener');

        // Simulate click on external link
        githubLink.click();

        // Wait for click handling
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify window.open was called with correct URL
        expect(window.open).toHaveBeenCalledWith(
            'https://github.com/marekruzicka/vagrantfile-generator',
            '_blank',
            expect.stringContaining('noopener')
        );

        // Main page content should remain unchanged
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();
        expect(mainContent.innerHTML).toContain('This should remain when external link is clicked');

        // URL should not have changed
        expect(window.location.pathname).toBe('/');
    });

    test('should handle external links with security attributes', async () => {
        // Mock external link discovery
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'external-docs.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock external docs content
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'external-docs.md',
                    title: 'Documentation',
                    isExternal: true,
                    externalUrl: 'https://docs.example.com',
                    rawContent: '# [Documentation](https://docs.example.com)\n\nExternal documentation...',
                    isValid: true
                }
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        const externalLink = document.querySelector('[data-page="external-docs"]');
        expect(externalLink).toBeTruthy();

        // Verify security attributes
        expect(externalLink.getAttribute('target')).toBe('_blank');
        expect(externalLink.getAttribute('rel')).toContain('noopener');
        expect(externalLink.getAttribute('rel')).toContain('noreferrer');

        // Link should have external indicator
        expect(
            externalLink.innerHTML.includes('external') ||
            externalLink.getAttribute('aria-label')?.includes('external') ||
            externalLink.classList.contains('external-link') ||
            externalLink.querySelector('.external-icon')
        ).toBeTruthy();
    });

    test('should distinguish external links visually from internal links', async () => {
        // Mock mixed internal/external links
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'internal-page.md', isValid: true },
                    { filename: 'external-site.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock internal page content
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Internal Page',
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '# Internal Page\n\nThis is internal content'
                }
            })
        });

        // Mock external site content
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'External Site',
                    isExternal: true,
                    externalUrl: 'https://external.example.com',
                    rawContent: '# [External Site](https://external.example.com)\n\nExternal content'
                }
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        const internalLink = document.querySelector('[data-page="internal-page"]');
        const externalLink = document.querySelector('[data-page="external-site"]');

        expect(internalLink).toBeTruthy();
        expect(externalLink).toBeTruthy();

        // Internal link should NOT have external attributes
        expect(internalLink.getAttribute('target')).not.toBe('_blank');
        expect(internalLink.hasAttribute('rel')).toBeFalsy();

        // External link should have external attributes
        expect(externalLink.getAttribute('target')).toBe('_blank');
        expect(externalLink.hasAttribute('rel')).toBeTruthy();

        // Visual distinction should exist
        const internalClasses = Array.from(internalLink.classList);
        const externalClasses = Array.from(externalLink.classList);

        // Either different classes or different content/styling
        const hasDifferentClasses = !internalClasses.every(cls => externalClasses.includes(cls)) ||
                                   !externalClasses.every(cls => internalClasses.includes(cls));
        
        const hasDifferentContent = internalLink.innerHTML !== externalLink.innerHTML;

        expect(hasDifferentClasses || hasDifferentContent).toBeTruthy();
    });

    test('should handle malformed external URLs gracefully', async () => {
        // Mock file with malformed external URL
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'bad-url.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock content with invalid URL
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'bad-url.md',
                    title: 'Bad URL',
                    isExternal: true,
                    externalUrl: 'not-a-valid-url',
                    rawContent: '# [Bad URL](not-a-valid-url)\n\nThis has an invalid URL',
                    isValid: false
                },
                warnings: ['Invalid URL format']
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        const badLink = document.querySelector('[data-page="bad-url"]');
        
        if (badLink) {
            // Link should either be disabled or handle error gracefully
            const isDisabled = badLink.hasAttribute('disabled') ||
                             badLink.getAttribute('aria-disabled') === 'true' ||
                             badLink.classList.contains('disabled');

            if (!isDisabled) {
                // If not disabled, clicking should not cause errors
                expect(() => badLink.click()).not.toThrow();
                
                // Should not call window.open with invalid URL
                expect(window.open).not.toHaveBeenCalledWith('not-a-valid-url', expect.anything(), expect.anything());
            }
        }
    });

    test('should prevent external link clicks from navigating current page', async () => {
        // Mock external link
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'external.md', isValid: true }],
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
                    title: 'External Link',
                    isExternal: true,
                    externalUrl: 'https://example.com'
                }
            })
        });

        document.body.innerHTML = `
            <div id="app">
                <main id="main-content">
                    <h1>Original Content</h1>
                    <p>This should not change when external link is clicked</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Store original content
        const originalContent = document.querySelector('#main-content').innerHTML;

        const externalLink = document.querySelector('[data-page="external"]');
        expect(externalLink).toBeTruthy();

        // Click external link
        externalLink.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Main content should be unchanged
        const currentContent = document.querySelector('#main-content').innerHTML;
        expect(currentContent).toBe(originalContent);

        // URL should be unchanged
        expect(window.location.hash).toBe('');
        expect(window.location.pathname).toBe('/');
    });

    test('should handle external link click event cancellation', async () => {
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'external.md', isValid: true }],
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
                    title: 'External',
                    isExternal: true,
                    externalUrl: 'https://example.com'
                }
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        const externalLink = document.querySelector('[data-page="external"]');
        expect(externalLink).toBeTruthy();

        // Add event listener that cancels the click
        let preventDefaultCalled = false;
        externalLink.addEventListener('click', (e) => {
            e.preventDefault();
            preventDefaultCalled = true;
        }, { capture: true });

        // Click should be prevented
        externalLink.click();
        await new Promise(resolve => setTimeout(resolve, 50));

        // Verify preventDefault was called
        expect(preventDefaultCalled).toBeTruthy();

        // window.open should not have been called if event was cancelled
        expect(window.open).not.toHaveBeenCalled();
    });

    test('should handle popup blocker scenarios gracefully', async () => {
        // Mock window.open failure (popup blocked)
        window.open = jest.fn().mockReturnValue(null);

        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'external.md', isValid: true }],
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
                    title: 'External',
                    isExternal: true,
                    externalUrl: 'https://example.com'
                }
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        const externalLink = document.querySelector('[data-page="external"]');
        expect(externalLink).toBeTruthy();

        // Should not throw error when popup is blocked
        expect(() => externalLink.click()).not.toThrow();

        // window.open should have been attempted
        expect(window.open).toHaveBeenCalledWith('https://example.com', '_blank', expect.anything());
    });
});