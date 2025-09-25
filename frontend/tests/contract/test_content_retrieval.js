/**
 * Contract Test: Footer Content Retrieval API
 * 
 * Tests the GET /api/footer/content/{filename} endpoint contract according to the 
 * specification in contracts/markdown-processing.md
 */

describe('Footer Content Retrieval API Contract', () => {
    const API_BASE_URL = 'http://localhost:8000';
    const FOOTER_CONTENT_ENDPOINT = `${API_BASE_URL}/api/footer/content`;

    describe('GET /api/footer/content/{filename}', () => {
        test('should return success response for existing file', async () => {
            // This test MUST FAIL initially - no implementation exists yet
            // Test with the footer.md file that should exist
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            const data = await response.json();

            // Validate response structure per contract
            expect(response.status).toBe(200);
            expect(data).toHaveProperty('status', 'success');
            expect(data).toHaveProperty('result');
            expect(data).toHaveProperty('warnings');

            // Validate result object structure
            const result = data.result;
            expect(result).toHaveProperty('filename');
            expect(result).toHaveProperty('title');
            expect(result).toHaveProperty('isExternal');
            expect(result).toHaveProperty('externalUrl');
            expect(result).toHaveProperty('rawContent');
            expect(result).toHaveProperty('renderedContent');
            expect(result).toHaveProperty('lastModified');
            expect(result).toHaveProperty('size');
            expect(result).toHaveProperty('isValid');

            // Validate data types
            expect(typeof result.filename).toBe('string');
            expect(typeof result.title).toBe('string');
            expect(typeof result.isExternal).toBe('boolean');
            expect(result.externalUrl === null || typeof result.externalUrl === 'string').toBe(true);
            expect(typeof result.rawContent).toBe('string');
            expect(typeof result.renderedContent).toBe('string');
            expect(typeof result.lastModified).toBe('string');
            expect(typeof result.size).toBe('number');
            expect(typeof result.isValid).toBe('boolean');

            // Validate filename format
            expect(result.filename).toMatch(/\.md$/);
            
            // Validate timestamp format (ISO 8601 with Z)
            expect(result.lastModified).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/);

            // Validate warnings array
            expect(Array.isArray(data.warnings)).toBe(true);
        });

        test('should handle external link in heading', async () => {
            // Test file with external link in heading: # [Text](URL)
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/test-external`);
            
            if (response.status === 200) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const result = data.result;
                    
                    // If this is an external link, validate structure
                    if (result.isExternal) {
                        expect(result.isExternal).toBe(true);
                        expect(result.externalUrl).toBeTruthy();
                        expect(typeof result.externalUrl).toBe('string');
                        expect(result.externalUrl).toMatch(/^https?:\/\//);
                        
                        // Title should be the link text, not including URL
                        expect(result.title).not.toContain('http');
                        expect(result.title.length).toBeGreaterThan(0);
                    }
                }
            } else {
                // File might not exist - that's ok for this test
                expect([404, 200]).toContain(response.status);
            }
        });

        test('should handle internal page without external link', async () => {
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            
            if (response.status === 200) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const result = data.result;
                    
                    // For footer.md, should be internal (no external link)
                    expect(result.isExternal).toBe(false);
                    expect(result.externalUrl).toBeNull();
                    expect(result.title).toBeTruthy();
                    expect(typeof result.title).toBe('string');
                }
            }
        });

        test('should return 404 for non-existent file', async () => {
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/non-existent-file`);
            
            expect(response.status).toBe(404);
            
            const data = await response.json();
            expect(data).toHaveProperty('detail');
            expect(typeof data.detail).toBe('string');
        });

        test('should return 403 for underscore-prefixed files', async () => {
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/_hidden`);
            
            expect(response.status).toBe(403);
            
            const data = await response.json();
            expect(data).toHaveProperty('detail');
            expect(data.detail).toContain('hidden');
        });

        test('should handle filename with .md extension', async () => {
            // API should accept both 'footer' and 'footer.md'
            const response1 = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            const response2 = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer.md`);
            
            // Both should work the same way
            expect(response1.status).toBe(response2.status);
            
            if (response1.status === 200 && response2.status === 200) {
                const data1 = await response1.json();
                const data2 = await response2.json();
                
                expect(data1.status).toBe(data2.status);
                if (data1.status === 'success' && data2.status === 'success') {
                    expect(data1.result.filename).toBe(data2.result.filename);
                    expect(data1.result.rawContent).toBe(data2.result.rawContent);
                }
            }
        });

        test('should prevent path traversal attacks', async () => {
            // Test various path traversal attempts
            const maliciousFilenames = [
                '../../../etc/passwd',
                '..%2F..%2F..%2Fetc%2Fpasswd',
                '....//....//etc/passwd',
                '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts'
            ];

            for (const filename of maliciousFilenames) {
                const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/${encodeURIComponent(filename)}`);
                
                // Should either return 400 (bad request) or 404 (not found)
                // Should NOT return actual system files
                expect([400, 404]).toContain(response.status);
                
                if (response.status === 200) {
                    const data = await response.json();
                    // If somehow it returns 200, make sure it's not system content
                    if (data.result && data.result.rawContent) {
                        expect(data.result.rawContent).not.toContain('root:');
                        expect(data.result.rawContent).not.toContain('localhost');
                    }
                }
            }
        });

        test('should handle large files within limits', async () => {
            // Test should pass once file size validation is implemented
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            
            if (response.status === 200) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const result = data.result;
                    
                    // File size should be reasonable (contract specifies 100KB limit)
                    expect(result.size).toBeLessThanOrEqual(100 * 1024);
                    expect(result.size).toBeGreaterThanOrEqual(0);
                    
                    // Content length should match size approximately
                    const contentBytes = new TextEncoder().encode(result.rawContent).length;
                    expect(Math.abs(contentBytes - result.size)).toBeLessThanOrEqual(10);
                }
            }
        });

        test('should handle UTF-8 content correctly', async () => {
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            
            if (response.status === 200) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const result = data.result;
                    
                    // Content should be valid strings
                    expect(result.rawContent).not.toContain('\uFFFD'); // Replacement character
                    expect(result.renderedContent).not.toContain('\uFFFD');
                    
                    // Should handle common UTF-8 characters if present
                    if (result.rawContent.includes('©')) {
                        expect(result.renderedContent).toContain('©');
                    }
                }
            }
        });

        test('should provide fallback title for files without headings', async () => {
            // This tests the filename fallback behavior mentioned in contracts
            const response = await fetch(`${FOOTER_CONTENT_ENDPOINT}/footer`);
            
            if (response.status === 200) {
                const data = await response.json();
                
                if (data.status === 'success') {
                    const result = data.result;
                    
                    // Title should never be empty
                    expect(result.title).toBeTruthy();
                    expect(result.title.length).toBeGreaterThan(0);
                    
                    // If no heading in content, title should be filename-based
                    if (!result.rawContent.includes('#')) {
                        // Should be a readable version of filename
                        expect(result.title).not.toBe('footer.md');
                        expect(result.title).not.toBe('footer');
                    }
                }
            }
        });
    });
});