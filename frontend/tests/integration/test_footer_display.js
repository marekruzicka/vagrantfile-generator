/**
 * Integration Test: Basic Footer Display
 * 
 * Tests that the footer component renders correctly with content from the backend
 * This test covers Scenario 1 from quickstart.md
 */

describe('Footer Display Integration', () => {
    let mockApiResponse;
    let originalFetch;

    beforeEach(() => {
        // Mock fetch for API calls
        originalFetch = global.fetch;
        mockApiResponse = {
            files: [
                {
                    filename: 'footer.md',
                    path: 'backend/data/footer/footer.md',
                    lastModified: '2025-09-25T10:30:00Z',
                    size: 35,
                    isValid: true
                }
            ],
            excluded: [],
            errors: []
        };

        global.fetch = jest.fn();
    });

    afterEach(() => {
        global.fetch = originalFetch;
        // Clean up DOM
        document.body.innerHTML = '';
    });

    test('should render footer with default content', async () => {
        // Mock the file discovery API
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                ...mockApiResponse
            })
        });

        // Mock the content retrieval API  
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'footer.md',
                    title: 'Footer',
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '© 2025 Vagrantfile Generator.',
                    renderedContent: '© 2025 Vagrantfile Generator.',
                    lastModified: '2025-09-25T10:30:00Z',
                    size: 35,
                    isValid: true
                },
                warnings: []
            })
        });

        // Create minimal HTML structure for testing
        document.body.innerHTML = `
            <div id="app">
                <main>
                    <h1>Test Page</h1>
                    <p>Main content</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        // Load and initialize the footer component
        // This test MUST FAIL initially - no implementation exists
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();

        // Wait for async operations
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify footer is rendered
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();
        expect(footerElement.textContent).toContain('© 2025 Vagrantfile Generator.');

        // Verify footer positioning
        const computedStyle = window.getComputedStyle(footerElement);
        expect(['sticky', 'fixed', 'static']).toContain(computedStyle.position);

        // Verify footer doesn't interfere with main content
        const mainElement = document.querySelector('main');
        expect(mainElement).toBeTruthy();
        
        // Footer should not overlap main content
        const footerRect = footerElement.getBoundingClientRect();
        const mainRect = mainElement.getBoundingClientRect();
        expect(footerRect.top).toBeGreaterThanOrEqual(mainRect.bottom);
    });

    test('should render footer with navigation links', async () => {
        // Mock API with multiple files
        const multiFileResponse = {
            files: [
                {
                    filename: 'footer.md',
                    path: 'backend/data/footer/footer.md',
                    lastModified: '2025-09-25T10:30:00Z',
                    size: 35,
                    isValid: true
                },
                {
                    filename: 'roadmap.md',
                    path: 'backend/data/footer/roadmap.md',
                    lastModified: '2025-09-25T09:15:00Z',
                    size: 150,
                    isValid: true
                }
            ],
            excluded: [],
            errors: []
        };

        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                ...multiFileResponse
            })
        });

        // Mock content retrieval for footer.md
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                result: {
                    filename: 'footer.md',
                    title: 'Footer',
                    isExternal: false,
                    externalUrl: null,
                    rawContent: '© 2025 Vagrantfile Generator.',
                    renderedContent: '© 2025 Vagrantfile Generator.',
                    lastModified: '2025-09-25T10:30:00Z',
                    size: 35,
                    isValid: true
                },
                warnings: []
            })
        });

        // Mock content retrieval for roadmap.md
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
                    rawContent: '# Roadmap\n\nUpcoming features...',
                    renderedContent: '<h1>Roadmap</h1><p>Upcoming features...</p>',
                    lastModified: '2025-09-25T09:15:00Z',
                    size: 150,
                    isValid: true
                },
                warnings: []
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();

        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify footer with navigation links
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();

        // Should contain copyright text
        expect(footerElement.textContent).toContain('© 2025 Vagrantfile Generator.');

        // Should contain navigation link to roadmap
        const roadmapLink = footerElement.querySelector('[data-page="roadmap"]');
        expect(roadmapLink).toBeTruthy();
        expect(roadmapLink.textContent).toContain('Roadmap');

        // Link should have proper attributes
        expect(roadmapLink.tagName).toBe('A');
        expect(roadmapLink.getAttribute('href')).toBeTruthy();
    });

    test('should maintain responsive layout on different screen sizes', async () => {
        // Mock basic API responses
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [],
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
                    rawContent: '© 2025 Vagrantfile Generator.',
                    renderedContent: '© 2025 Vagrantfile Generator.',
                    title: 'Footer',
                    isExternal: false,
                    externalUrl: null
                }
            })
        });

        document.body.innerHTML = `
            <div id="app" style="width: 100vw;">
                <div id="footer-container"></div>
            </div>
        `;

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();

        await new Promise(resolve => setTimeout(resolve, 100));

        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();

        // Test mobile viewport
        Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: 375,
        });
        window.dispatchEvent(new Event('resize'));

        await new Promise(resolve => setTimeout(resolve, 50));

        const mobileStyle = window.getComputedStyle(footerElement);
        expect(footerElement.offsetWidth).toBeLessThanOrEqual(375);

        // Test desktop viewport
        Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: 1200,
        });
        window.dispatchEvent(new Event('resize'));

        await new Promise(resolve => setTimeout(resolve, 50));

        const desktopStyle = window.getComputedStyle(footerElement);
        expect(footerElement.offsetWidth).toBeLessThanOrEqual(1200);
    });

    test('should handle empty footer content gracefully', async () => {
        // Mock API with no files
        global.fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                status: 'success',
                files: [],
                excluded: [],
                errors: []
            })
        });

        document.body.innerHTML = '<div id="footer-container"></div>';

        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        await FooterComponent.initialize();

        await new Promise(resolve => setTimeout(resolve, 100));

        // Footer should still render with default content
        const footerElement = document.querySelector('[data-testid="footer"]');
        expect(footerElement).toBeTruthy();
        
        // Should show default copyright when no footer.md
        expect(footerElement.textContent).toContain('© 2025 Vagrantfile Generator.');
    });

    test('should not block page rendering when API is slow', async () => {
        // Mock slow API response
        global.fetch.mockImplementation(() => 
            new Promise(resolve => 
                setTimeout(() => resolve({
                    ok: true,
                    status: 200,
                    json: async () => ({
                        status: 'success',
                        files: [],
                        excluded: [],
                        errors: []
                    })
                }), 2000)
            )
        );

        document.body.innerHTML = `
            <div id="app">
                <main>
                    <h1>Test Page</h1>
                    <p>This content should be visible immediately</p>
                </main>
                <div id="footer-container"></div>
            </div>
        `;

        // Start footer initialization
        const FooterComponent = require('../../../src/js/components/FooterComponent.js');
        FooterComponent.initialize(); // Don't await

        // Main content should be immediately visible
        const mainElement = document.querySelector('main');
        expect(mainElement).toBeTruthy();
        expect(mainElement.textContent).toContain('This content should be visible immediately');

        // Page should be interactive
        expect(document.readyState).toBe('complete');
    });
});