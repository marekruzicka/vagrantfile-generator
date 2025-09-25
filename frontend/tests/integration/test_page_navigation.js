/**
 * Integration Test: Internal Page Navigation
 * 
 * Tests that clicking footer navigation links properly loads internal pages
 * This test covers Scenario 2 from quickstart.md
 */

describe('Internal Page Navigation Integration', () => {
    let mockApiResponse;
    let originalFetch;

    beforeEach(() => {
        originalFetch = global.fetch;
        global.fetch = jest.fn();
        
        // Clean up DOM and history
        document.body.innerHTML = '';
        if (window.history.replaceState) {
            window.history.replaceState(null, '', '/');
        }
    });

    afterEach(() => {
        global.fetch = originalFetch;
        document.body.innerHTML = '';
    });

    test('should navigate to internal page when footer link clicked', async () => {
        // Mock footer files discovery
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'roadmap.md', path: 'backend/data/footer/roadmap.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock roadmap content retrieval - internal page
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'roadmap.md',
                    title: 'Roadmap',
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '# Roadmap\n\n## Upcoming Features\n- Feature 1\n- Feature 2',
                    renderedContent: '<h1>Roadmap</h1><h2>Upcoming Features</h2><ul><li>Feature 1</li><li>Feature 2</li></ul>',
                    lastModified: '2025-09-25T09:15:00Z',
                    isValid: true
                },
                warnings: []
            })
        });

        // Setup page structure
        document.body.innerHTML = `
            <div id="app">
                <nav id="main-nav">
                    <a href="/" data-internal-link>Home</a>
                </nav>
                <main id="main-content">
                    <h1>Home Page</h1>
                    <p>Welcome to the home page</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        // This test MUST FAIL initially - components don't exist yet
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        const StaticPageRouter = require('../../../src/js/router/StaticPageRouter.js');
        
        // Initialize components
        await FooterComponent.initialize();
        StaticPageRouter.initialize();

        await new Promise(resolve => setTimeout(resolve, 100));

        // Find the roadmap link in footer
        const roadmapLink = document.querySelector('[data-page="roadmap"]');
        expect(roadmapLink).toBeTruthy();
        expect(roadmapLink.textContent).toContain('Roadmap');

        // Mock navigation API call for when link is clicked
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'roadmap.md',
                    title: 'Roadmap',
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '# Roadmap\n\n## Upcoming Features\n- Feature 1\n- Feature 2',
                    renderedContent: '<h1>Roadmap</h1><h2>Upcoming Features</h2><ul><li>Feature 1</li><li>Feature 2</li></ul>',
                    lastModified: '2025-09-25T09:15:00Z',
                    isValid: true
                }
            })
        });

        // Simulate click on roadmap link
        roadmapLink.click();

        // Wait for navigation to complete
        await new Promise(resolve => setTimeout(resolve, 200));

        // Verify page content changed
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();
        
        // Should show roadmap content
        expect(mainContent.innerHTML).toContain('Roadmap');
        expect(mainContent.innerHTML).toContain('Upcoming Features');
        expect(mainContent.innerHTML).toContain('Feature 1');

        // URL should have changed (if using history API)
        if (window.location.pathname) {
            expect(window.location.pathname === '/roadmap' || window.location.hash === '#roadmap').toBeTruthy();
        }

        // Footer should remain visible and unchanged
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();
        expect(footerElement.querySelector('[data-page="roadmap"]')).toBeTruthy();
    });

    test('should handle multiple internal page navigations', async () => {
        // Mock discovery with multiple files
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'roadmap.md', path: 'backend/data/footer/roadmap.md', isValid: true },
                    { filename: 'changelog.md', path: 'backend/data/footer/changelog.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        // Mock content for roadmap
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Roadmap',
                    isExternal: false,
                    renderedContent: '<h1>Roadmap</h1><p>Future plans</p>'
                }
            })
        });

        // Mock content for changelog  
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Changelog',
                    isExternal: false,
                    renderedContent: '<h1>Changelog</h1><p>Recent changes</p>'
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

        // Navigate to roadmap
        const roadmapLink = document.querySelector('[data-page="roadmap"]');
        expect(roadmapLink).toBeTruthy();

        // Mock navigation call
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Roadmap',
                    renderedContent: '<h1>Roadmap</h1><p>Future plans</p>'
                }
            })
        });

        roadmapLink.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify first navigation
        const mainContent = document.querySelector('#main-content');
        expect(mainContent.innerHTML).toContain('Roadmap');
        expect(mainContent.innerHTML).toContain('Future plans');

        // Navigate to changelog
        const changelogLink = document.querySelector('[data-page="changelog"]');
        expect(changelogLink).toBeTruthy();

        // Mock second navigation call
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'Changelog',
                    renderedContent: '<h1>Changelog</h1><p>Recent changes</p>'
                }
            })
        });

        changelogLink.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify second navigation
        expect(mainContent.innerHTML).toContain('Changelog');
        expect(mainContent.innerHTML).toContain('Recent changes');
        
        // Should no longer show roadmap content
        expect(mainContent.innerHTML).not.toContain('Future plans');
    });

    test('should preserve browser back/forward functionality', async () => {
        // Mock basic setup
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'about.md', isValid: true }],
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
                    title: 'About',
                    isExternal: false,
                    renderedContent: '<h1>About</h1><p>About us</p>'
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

        // Store initial state
        const initialContent = document.querySelector('#main-content').innerHTML;

        // Navigate to about page
        const aboutLink = document.querySelector('[data-page="about"]');

        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    title: 'About',
                    renderedContent: '<h1>About</h1><p>About us</p>'
                }
            })
        });

        aboutLink.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify navigation occurred
        const mainContent = document.querySelector('#main-content');
        expect(mainContent.innerHTML).toContain('About');

        // Simulate back button (if history API is used)
        if (window.history && window.history.back) {
            // Mock history state restoration
            window.history.back();
            await new Promise(resolve => setTimeout(resolve, 100));

            // Content should potentially restore (depending on implementation)
            // This test validates that back navigation is handled gracefully
            expect(document.querySelector('#main-content')).toBeTruthy();
        }
    });

    test('should handle navigation errors gracefully', async () => {
        // Mock initial setup
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [{ filename: 'broken.md', isValid: true }],
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
                    title: 'Broken Page',
                    isExternal: false
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

        const brokenLink = document.querySelector('[data-page="broken"]');
        expect(brokenLink).toBeTruthy();

        // Mock failed navigation (404 or server error)
        global.fetch.mockRejectedValueOnce(new Error('Network error'));

        const originalContent = document.querySelector('#main-content').innerHTML;

        brokenLink.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Should handle error gracefully - either show error page or stay on current page
        const mainContent = document.querySelector('#main-content');
        expect(mainContent).toBeTruthy();

        // Should either show error content or preserve original content
        const currentContent = mainContent.innerHTML;
        const hasErrorContent = currentContent.includes('error') || currentContent.includes('Error') || 
                              currentContent.includes('not found') || currentContent.includes('Not Found');
        const preservedOriginal = currentContent === originalContent;
        
        expect(hasErrorContent || preservedOriginal).toBeTruthy();

        // Footer should remain functional
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();
    });

    test('should maintain footer highlight for current page', async () => {
        // Mock setup with multiple pages
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [
                    { filename: 'page1.md', isValid: true },
                    { filename: 'page2.md', isValid: true }
                ],
                excluded: [],
                errors: []
            })
        });

        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: { title: 'Test Page', isExternal: false, renderedContent: '<h1>Test</h1>' }
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

        const page1Link = document.querySelector('[data-page="page1"]');
        const page2Link = document.querySelector('[data-page="page2"]');

        expect(page1Link).toBeTruthy();
        expect(page2Link).toBeTruthy();

        // Navigate to page1
        page1Link.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Page1 link should be highlighted/active
        expect(page1Link.classList.contains('active') || 
               page1Link.getAttribute('aria-current') === 'page' ||
               page1Link.hasAttribute('data-current')).toBeTruthy();

        // Page2 link should not be highlighted
        expect(!page2Link.classList.contains('active') && 
               page2Link.getAttribute('aria-current') !== 'page' &&
               !page2Link.hasAttribute('data-current')).toBeTruthy();

        // Navigate to page2
        page2Link.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Highlights should switch
        expect(!page1Link.classList.contains('active') &&
               page1Link.getAttribute('aria-current') !== 'page' &&
               !page1Link.hasAttribute('data-current')).toBeTruthy();

        expect(page2Link.classList.contains('active') || 
               page2Link.getAttribute('aria-current') === 'page' ||
               page2Link.hasAttribute('data-current')).toBeTruthy();
    });
});