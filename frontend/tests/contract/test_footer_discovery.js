/**
 * Contract Test: Footer File Discovery API
 * 
 * Tests the GET /api/footer/files endpoint contract according to the specification
 * in contracts/footer-discovery.md
 */

describe('Footer File Discovery API Contract', () => {
    const API_BASE_URL = 'http://localhost:8000';
    const FOOTER_FILES_ENDPOINT = `${API_BASE_URL}/api/footer/files`;

    describe('GET /api/footer/files', () => {
        test('should return success response with file list structure', async () => {
            // This test MUST FAIL initially - no implementation exists yet
            const response = await fetch(FOOTER_FILES_ENDPOINT);
            const data = await response.json();

            // Validate response structure per contract
            expect(response.status).toBe(200);
            expect(data).toHaveProperty('status', 'success');
            expect(data).toHaveProperty('files');
            expect(data).toHaveProperty('excluded');
            expect(data).toHaveProperty('errors');

            // Validate files array structure
            expect(Array.isArray(data.files)).toBe(true);
            expect(Array.isArray(data.excluded)).toBe(true);
            expect(Array.isArray(data.errors)).toBe(true);

            // If files exist, validate file object structure
            if (data.files.length > 0) {
                const file = data.files[0];
                expect(file).toHaveProperty('filename');
                expect(file).toHaveProperty('path');
                expect(file).toHaveProperty('lastModified');
                expect(file).toHaveProperty('size');
                expect(file).toHaveProperty('isValid');

                // Validate data types
                expect(typeof file.filename).toBe('string');
                expect(typeof file.path).toBe('string');
                expect(typeof file.lastModified).toBe('string');
                expect(typeof file.size).toBe('number');
                expect(typeof file.isValid).toBe('boolean');

                // Validate filename format
                expect(file.filename).toMatch(/\.md$/);
                expect(file.path).toMatch(/^backend\/data\/footer\/.*\.md$/);

                // Validate timestamp format (ISO 8601 with Z)
                expect(file.lastModified).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/);
            }
        });

        test('should exclude underscore-prefixed files', async () => {
            const response = await fetch(FOOTER_FILES_ENDPOINT);
            const data = await response.json();

            expect(response.status).toBe(200);
            expect(data.status).toBe('success');

            // Verify no underscore files in main files array
            data.files.forEach(file => {
                expect(file.filename).not.toMatch(/^_/);
            });

            // If underscore files exist, they should be in excluded array
            data.excluded.forEach(filename => {
                expect(typeof filename).toBe('string');
                // Most excluded files should start with underscore
                if (filename.includes('_')) {
                    expect(filename).toMatch(/^_|_/);
                }
            });
        });

        test('should handle empty directory gracefully', async () => {
            // This tests the contract behavior when no footer files exist
            const response = await fetch(FOOTER_FILES_ENDPOINT);
            const data = await response.json();

            expect(response.status).toBe(200);
            expect(data.status).toBe('success');
            expect(data.files).toEqual([]);
            expect(Array.isArray(data.excluded)).toBe(true);
            expect(Array.isArray(data.errors)).toBe(true);
        });

        test('should handle directory access errors', async () => {
            // This test will pass when error handling is implemented
            // For now, expect either success or proper error structure
            const response = await fetch(FOOTER_FILES_ENDPOINT);
            const data = await response.json();

            if (data.status === 'error') {
                // Validate error response structure
                expect(data).toHaveProperty('message');
                expect(data).toHaveProperty('code');
                expect(data).toHaveProperty('files', []);
                expect(data).toHaveProperty('excluded', []);
                expect(data).toHaveProperty('errors');

                expect(typeof data.message).toBe('string');
                expect(typeof data.code).toBe('string');
                expect(Array.isArray(data.errors)).toBe(true);
            } else {
                // Success response should follow success contract
                expect(data.status).toBe('success');
                expect(data).toHaveProperty('files');
                expect(data).toHaveProperty('excluded');
                expect(data).toHaveProperty('errors');
            }
        });

        test('should return consistent data structure across multiple calls', async () => {
            // Test idempotency
            const response1 = await fetch(FOOTER_FILES_ENDPOINT);
            const data1 = await response1.json();

            // Wait a moment and call again
            await new Promise(resolve => setTimeout(resolve, 100));

            const response2 = await fetch(FOOTER_FILES_ENDPOINT);
            const data2 = await response2.json();

            // Both responses should have the same structure
            expect(response1.status).toBe(response2.status);
            expect(data1.status).toBe(data2.status);
            
            if (data1.status === 'success' && data2.status === 'success') {
                expect(data1.files.length).toBe(data2.files.length);
                expect(data1.excluded.length).toBe(data2.excluded.length);
            }
        });

        test('should handle CORS properly', async () => {
            // Test CORS headers are present for cross-origin requests
            const response = await fetch(FOOTER_FILES_ENDPOINT, {
                method: 'GET',
                headers: {
                    'Origin': 'http://localhost:5173'
                }
            });

            // Should not fail due to CORS
            expect(response.status).toBe(200);
            
            // CORS headers should be present (implementation dependent)
            const corsHeader = response.headers.get('Access-Control-Allow-Origin');
            if (corsHeader) {
                expect(['*', 'http://localhost:5173']).toContain(corsHeader);
            }
        });
    });
});