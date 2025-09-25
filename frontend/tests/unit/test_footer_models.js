/**
 * Unit Tests for Footer Models
 * 
 * Tests for FooterConfiguration, StaticPage, and FooterNavigationLink models.
 * Validates data model behavior, validation, and serialization.
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import FooterConfiguration from '../../src/js/models/FooterConfiguration.js';
import StaticPage from '../../src/js/models/StaticPage.js';
import FooterNavigationLink from '../../src/js/models/FooterNavigationLink.js';

describe('FooterConfiguration Model', () => {
    let validConfig;

    beforeEach(() => {
        validConfig = {
            copyrightText: '© 2025 Test Company',
            navigationLinks: [
                {
                    title: 'About',
                    pageId: 'about',
                    isExternal: false,
                    url: null,
                    isEnabled: true,
                    order: 1
                }
            ]
        };
    });

    describe('Constructor', () => {
        test('should create instance with valid data', () => {
            const config = new FooterConfiguration(validConfig);
            
            expect(config.copyrightText).toBe('© 2025 Test Company');
            expect(config.navigationLinks).toHaveLength(1);
            expect(config.navigationLinks[0]).toBeInstanceOf(FooterNavigationLink);
        });

        test('should handle empty navigation links', () => {
            const config = new FooterConfiguration({
                copyrightText: 'Test',
                navigationLinks: []
            });
            
            expect(config.navigationLinks).toHaveLength(0);
        });

        test('should throw error for invalid copyright text', () => {
            expect(() => {
                new FooterConfiguration({
                    copyrightText: '',
                    navigationLinks: []
                });
            }).toThrow('Copyright text cannot be empty');
        });

        test('should throw error for null copyright text', () => {
            expect(() => {
                new FooterConfiguration({
                    copyrightText: null,
                    navigationLinks: []
                });
            }).toThrow('Copyright text is required');
        });
    });

    describe('Validation', () => {
        test('should validate successfully with valid data', () => {
            const config = new FooterConfiguration(validConfig);
            expect(() => config.validate()).not.toThrow();
        });

        test('should validate navigation link types', () => {
            expect(() => {
                new FooterConfiguration({
                    copyrightText: 'Test',
                    navigationLinks: ['invalid']
                });
            }).toThrow('All navigation links must be FooterNavigationLink instances');
        });
    });

    describe('Static Methods', () => {
        test('fromApiResponse should create instance from API response', () => {
            const apiResponse = {
                success: true,
                result: validConfig
            };
            
            const config = FooterConfiguration.fromApiResponse(apiResponse);
            expect(config).toBeInstanceOf(FooterConfiguration);
            expect(config.copyrightText).toBe('© 2025 Test Company');
        });

        test('fromApiResponse should handle API errors', () => {
            const apiResponse = {
                success: false,
                error: 'API Error'
            };
            
            expect(() => {
                FooterConfiguration.fromApiResponse(apiResponse);
            }).toThrow('API Error');
        });
    });

    describe('Methods', () => {
        test('getEnabledLinks should return only enabled links', () => {
            const config = new FooterConfiguration({
                copyrightText: 'Test',
                navigationLinks: [
                    {
                        title: 'Enabled',
                        pageId: 'enabled',
                        isExternal: false,
                        url: null,
                        isEnabled: true,
                        order: 1
                    },
                    {
                        title: 'Disabled',
                        pageId: 'disabled',
                        isExternal: false,
                        url: null,
                        isEnabled: false,
                        order: 2
                    }
                ]
            });
            
            const enabledLinks = config.getEnabledLinks();
            expect(enabledLinks).toHaveLength(1);
            expect(enabledLinks[0].title).toBe('Enabled');
        });

        test('getSortedLinks should return links sorted by order', () => {
            const config = new FooterConfiguration({
                copyrightText: 'Test',
                navigationLinks: [
                    {
                        title: 'Second',
                        pageId: 'second',
                        isExternal: false,
                        url: null,
                        isEnabled: true,
                        order: 2
                    },
                    {
                        title: 'First',
                        pageId: 'first',
                        isExternal: false,
                        url: null,
                        isEnabled: true,
                        order: 1
                    }
                ]
            });
            
            const sortedLinks = config.getSortedLinks();
            expect(sortedLinks[0].title).toBe('First');
            expect(sortedLinks[1].title).toBe('Second');
        });

        test('toJSON should serialize correctly', () => {
            const config = new FooterConfiguration(validConfig);
            const json = config.toJSON();
            
            expect(json.copyrightText).toBe('© 2025 Test Company');
            expect(json.navigationLinks).toHaveLength(1);
            expect(json.navigationLinks[0].title).toBe('About');
        });
    });
});

describe('StaticPage Model', () => {
    let validPageData;

    beforeEach(() => {
        validPageData = {
            pageId: 'about',
            title: 'About Us',
            content: '# About Us\n\nThis is our about page.',
            renderedContent: '<h1>About Us</h1><p>This is our about page.</p>',
            isExternal: false,
            externalUrl: null,
            lastModified: '2025-01-15T12:00:00Z'
        };
    });

    describe('Constructor', () => {
        test('should create instance with valid data', () => {
            const page = new StaticPage(validPageData);
            
            expect(page.pageId).toBe('about');
            expect(page.title).toBe('About Us');
            expect(page.content).toBe('# About Us\n\nThis is our about page.');
            expect(page.isExternal).toBe(false);
        });

        test('should handle external pages', () => {
            const externalData = {
                ...validPageData,
                isExternal: true,
                externalUrl: 'https://example.com'
            };
            
            const page = new StaticPage(externalData);
            expect(page.isExternal).toBe(true);
            expect(page.externalUrl).toBe('https://example.com');
        });

        test('should throw error for invalid page ID', () => {
            expect(() => {
                new StaticPage({
                    ...validPageData,
                    pageId: ''
                });
            }).toThrow('Page ID cannot be empty');
        });

        test('should throw error for external page without URL', () => {
            expect(() => {
                new StaticPage({
                    ...validPageData,
                    isExternal: true,
                    externalUrl: null
                });
            }).toThrow('External URL is required for external pages');
        });
    });

    describe('Methods', () => {
        test('getDisplayTitle should return title or fallback', () => {
            const page = new StaticPage(validPageData);
            expect(page.getDisplayTitle()).toBe('About Us');
            
            const pageNoTitle = new StaticPage({
                ...validPageData,
                title: null
            });
            expect(pageNoTitle.getDisplayTitle()).toBe('about');
        });

        test('hasContent should check for content presence', () => {
            const page = new StaticPage(validPageData);
            expect(page.hasContent()).toBe(true);
            
            const emptyPage = new StaticPage({
                ...validPageData,
                content: ''
            });
            expect(emptyPage.hasContent()).toBe(false);
        });

        test('getRenderedContentOrFallback should return rendered or raw content', () => {
            const page = new StaticPage(validPageData);
            expect(page.getRenderedContentOrFallback()).toBe('<h1>About Us</h1><p>This is our about page.</p>');
            
            const pageNoRendered = new StaticPage({
                ...validPageData,
                renderedContent: null
            });
            expect(pageNoRendered.getRenderedContentOrFallback()).toBe('# About Us\n\nThis is our about page.');
        });

        test('getLastModifiedDate should return parsed date', () => {
            const page = new StaticPage(validPageData);
            const lastModified = page.getLastModifiedDate();
            
            expect(lastModified).toBeInstanceOf(Date);
            expect(lastModified.getFullYear()).toBe(2025);
        });

        test('toJSON should serialize correctly', () => {
            const page = new StaticPage(validPageData);
            const json = page.toJSON();
            
            expect(json.pageId).toBe('about');
            expect(json.title).toBe('About Us');
            expect(json.isExternal).toBe(false);
        });
    });

    describe('Static Methods', () => {
        test('fromApiResponse should create instance from API response', () => {
            const apiResponse = {
                success: true,
                result: validPageData
            };
            
            const page = StaticPage.fromApiResponse(apiResponse);
            expect(page).toBeInstanceOf(StaticPage);
            expect(page.pageId).toBe('about');
        });
    });
});

describe('FooterNavigationLink Model', () => {
    let validLinkData;

    beforeEach(() => {
        validLinkData = {
            title: 'About Us',
            pageId: 'about',
            isExternal: false,
            url: null,
            isEnabled: true,
            order: 1
        };
    });

    describe('Constructor', () => {
        test('should create instance with valid internal link data', () => {
            const link = new FooterNavigationLink(validLinkData);
            
            expect(link.title).toBe('About Us');
            expect(link.pageId).toBe('about');
            expect(link.isExternal).toBe(false);
            expect(link.isEnabled).toBe(true);
            expect(link.order).toBe(1);
        });

        test('should create instance with valid external link data', () => {
            const externalData = {
                title: 'GitHub',
                pageId: null,
                isExternal: true,
                url: 'https://github.com',
                isEnabled: true,
                order: 2
            };
            
            const link = new FooterNavigationLink(externalData);
            expect(link.isExternal).toBe(true);
            expect(link.url).toBe('https://github.com');
        });

        test('should throw error for empty title', () => {
            expect(() => {
                new FooterNavigationLink({
                    ...validLinkData,
                    title: ''
                });
            }).toThrow('Link title cannot be empty');
        });

        test('should throw error for internal link without pageId', () => {
            expect(() => {
                new FooterNavigationLink({
                    ...validLinkData,
                    pageId: null
                });
            }).toThrow('Page ID is required for internal links');
        });

        test('should throw error for external link without URL', () => {
            expect(() => {
                new FooterNavigationLink({
                    ...validLinkData,
                    isExternal: true,
                    pageId: null,
                    url: null
                });
            }).toThrow('URL is required for external links');
        });

        test('should throw error for invalid URL format', () => {
            expect(() => {
                new FooterNavigationLink({
                    ...validLinkData,
                    isExternal: true,
                    pageId: null,
                    url: 'invalid-url'
                });
            }).toThrow('Invalid URL format');
        });
    });

    describe('Methods', () => {
        test('getHref should return correct href for internal links', () => {
            const link = new FooterNavigationLink(validLinkData);
            expect(link.getHref()).toBe('#about');
        });

        test('getHref should return URL for external links', () => {
            const externalLink = new FooterNavigationLink({
                title: 'GitHub',
                pageId: null,
                isExternal: true,
                url: 'https://github.com',
                isEnabled: true,
                order: 1
            });
            
            expect(externalLink.getHref()).toBe('https://github.com');
        });

        test('getTarget should return _blank for external links', () => {
            const externalLink = new FooterNavigationLink({
                title: 'GitHub',
                pageId: null,
                isExternal: true,
                url: 'https://github.com',
                isEnabled: true,
                order: 1
            });
            
            expect(externalLink.getTarget()).toBe('_blank');
        });

        test('getTarget should return _self for internal links', () => {
            const link = new FooterNavigationLink(validLinkData);
            expect(link.getTarget()).toBe('_self');
        });

        test('getRel should return noopener noreferrer for external links', () => {
            const externalLink = new FooterNavigationLink({
                title: 'GitHub',
                pageId: null,
                isExternal: true,
                url: 'https://github.com',
                isEnabled: true,
                order: 1
            });
            
            expect(externalLink.getRel()).toBe('noopener noreferrer');
        });

        test('getRel should return null for internal links', () => {
            const link = new FooterNavigationLink(validLinkData);
            expect(link.getRel()).toBeNull();
        });

        test('toJSON should serialize correctly', () => {
            const link = new FooterNavigationLink(validLinkData);
            const json = link.toJSON();
            
            expect(json.title).toBe('About Us');
            expect(json.pageId).toBe('about');
            expect(json.isExternal).toBe(false);
            expect(json.order).toBe(1);
        });
    });

    describe('Comparison', () => {
        test('should compare by order for sorting', () => {
            const link1 = new FooterNavigationLink({
                ...validLinkData,
                order: 2
            });
            
            const link2 = new FooterNavigationLink({
                ...validLinkData,
                title: 'Contact',
                pageId: 'contact',
                order: 1
            });
            
            expect(link1.order > link2.order).toBe(true);
        });
    });
});

// Integration tests between models
describe('Model Integration', () => {
    test('FooterConfiguration should properly contain FooterNavigationLink instances', () => {
        const config = new FooterConfiguration({
            copyrightText: '© 2025 Test',
            navigationLinks: [
                {
                    title: 'About',
                    pageId: 'about',
                    isExternal: false,
                    url: null,
                    isEnabled: true,
                    order: 1
                }
            ]
        });
        
        const enabledLinks = config.getEnabledLinks();
        expect(enabledLinks[0]).toBeInstanceOf(FooterNavigationLink);
        expect(enabledLinks[0].getHref()).toBe('#about');
    });

    test('Models should serialize and deserialize consistently', () => {
        const originalConfig = new FooterConfiguration({
            copyrightText: '© 2025 Test',
            navigationLinks: [
                {
                    title: 'About',
                    pageId: 'about',
                    isExternal: false,
                    url: null,
                    isEnabled: true,
                    order: 1
                }
            ]
        });
        
        const json = originalConfig.toJSON();
        const recreatedConfig = new FooterConfiguration(json);
        
        expect(recreatedConfig.copyrightText).toBe(originalConfig.copyrightText);
        expect(recreatedConfig.navigationLinks[0].title).toBe(originalConfig.navigationLinks[0].title);
    });
});