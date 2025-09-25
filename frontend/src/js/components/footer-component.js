/**
 * Footer Component (Non-module version)
 * 
 * Alpine.js component for the configurable footer.
 * This version works with the legacy script loading system.
 */

// Global footer component function for Alpine.js
function footerComponent() {
    return {
        // State properties
        loading: false,
        error: false,
        errorMessage: '',
        canRetry: true,
        copyrightText: '© 2025 Vagrantfile Generator. Built with ❤️ for sysadmins',
        navigationLinks: [],
        currentPage: null,
        screenReaderAnnouncement: '',
        lastApiCall: null,
        errorCount: 0,
        
        // Modal state for internal content
        showContentModal: false,
        modalTitle: '',
        modalContent: '',

        // Internal state
        _footerConfig: null,
        _staticPages: [],
        _retryCount: 0,
        _maxRetries: 3,

        /**
         * Initialize the footer component
         */
        async initializeFooter() {
            try {
                this.loading = true;
                this.error = false;
                this.errorMessage = '';
                this._retryCount = 0;

                // Load footer data
                await this.loadFooterData();
                
            } catch (error) {
                console.error('FooterComponent: Initialization failed:', error);
                this.handleError(error);
            } finally {
                this.loading = false;
            }
        },

        /**
         * Load footer configuration and static pages
         */
        async loadFooterData() {
            this.lastApiCall = new Date().toISOString();
            
            try {
                // Load footer configuration
                const configResponse = await fetch('/api/footer/content/footer');
                if (!configResponse.ok) {
                    throw new Error(`HTTP ${configResponse.status}: ${configResponse.statusText}`);
                }
                const configData = await configResponse.json();

                // Load static pages for navigation
                const pagesResponse = await fetch('/api/footer/files');
                if (!pagesResponse.ok) {
                    throw new Error(`HTTP ${pagesResponse.status}: ${pagesResponse.statusText}`);
                }
                const pagesData = await pagesResponse.json();

                // Process footer configuration
                this.copyrightText = this.extractCopyrightText(configData.result.renderedContent);

                // Process static pages for navigation (now async)
                this.navigationLinks = await this.createNavigationLinks(pagesData.files);

            } catch (error) {
                console.error('FooterComponent: Failed to load footer data:', error);
                
                // Use default configuration
                this.copyrightText = '© 2025 Vagrantfile Generator.';
                this.navigationLinks = [];
                
                throw error;
            }
        },

        /**
         * Extract copyright text from footer content
         */
        extractCopyrightText(content) {
            if (!content) {
                return '© 2025 Vagrantfile Generator.';
            }
            
            // Since footer.md now contains just the copyright text, use it directly
            const cleanContent = content.trim();
            
            if (cleanContent) {
                return cleanContent;
            }
            
            // Fallback to default if somehow empty
            return '© 2025 Vagrantfile Generator.';
        },

        /**
         * Create navigation links from static pages
         */
        async createNavigationLinks(files) {
            if (!files || !Array.isArray(files)) {
                return [];
            }

            const links = [];
            
            for (const file of files.filter(f => f.filename !== 'footer.md')) {
                try {
                    // Fetch the content of each file to determine if it's external
                    const response = await fetch(`/api/footer/content/${file.filename.replace('.md', '')}`);
                    if (response.ok) {
                        const data = await response.json();
                        const content = data.result.renderedContent || data.result.rawContent || '';
                        
                        // Extract display name from content or use filename
                        const displayName = this.extractDisplayName(content, file.filename);
                        
                        // Check if the TOP-LEVEL HEADING contains a markdown link [text](url)
                        // This is the only way a file should be treated as external per spec
                        const firstLine = content.split('\n')[0];
                        const headingLinkMatch = firstLine.match(/^#\s+\[([^\]]+)\]\(([^)]+)\)/);
                        
                        if (headingLinkMatch) {
                            // Top-level heading has markdown link syntax - treat as external
                            const linkText = headingLinkMatch[1];
                            const linkUrl = headingLinkMatch[2];
                            
                            // Determine if it's an external link
                            const isExternal = linkUrl.startsWith('http://') || linkUrl.startsWith('https://') || linkUrl.startsWith('//');
                            
                            links.push({
                                text: linkText,
                                href: linkUrl,
                                isExternal: isExternal,
                                pageId: file.filename.replace('.md', ''),
                                title: isExternal ? `Open ${linkText} in new tab` : `Navigate to ${linkText}`
                            });
                        } else {
                            // No external link in heading - treat as internal content
                            links.push({
                                text: displayName,
                                href: `#${file.filename.replace('.md', '')}`,
                                isExternal: false,
                                pageId: file.filename.replace('.md', ''),
                                title: `View ${displayName}`,
                                content: this.renderMarkdownContent(content), // Render markdown for modal
                                rawContent: content // Keep raw for debugging
                            });
                        }
                    }
                } catch (error) {
                    console.error(`FooterComponent: Failed to process ${file.filename}:`, error);
                    // Fallback to internal link using filename
                    const displayName = file.filename.replace('.md', '').charAt(0).toUpperCase() + 
                                      file.filename.replace('.md', '').slice(1);
                    links.push({
                        text: displayName,
                        href: `#${file.filename.replace('.md', '')}`,
                        isExternal: false,
                        pageId: file.filename.replace('.md', ''),
                        title: `Navigate to ${displayName}`,
                        content: '<p>Content could not be loaded.</p>',
                        rawContent: ''
                    });
                }
            }
            
            return links.sort((a, b) => a.text.localeCompare(b.text));
        },

        /**
         * Extract display name from markdown content or use filename as fallback
         */
        extractDisplayName(content, filename) {
            // Look for top-level heading (# Title)
            const headingMatch = content.match(/^#\s+([^[\r\n]+)/m);
            if (headingMatch) {
                // Check if heading contains a markdown link [text](url)
                const linkMatch = headingMatch[1].match(/\[([^\]]+)\]/);
                if (linkMatch) {
                    return linkMatch[1]; // Return link text only
                }
                return headingMatch[1].trim(); // Return heading text
            }
            
            // Fallback to filename (capitalize first letter)
            const name = filename.replace('.md', '');
            return name.charAt(0).toUpperCase() + name.slice(1);
        },

        /**
         * Extract top-level header from markdown content
         * Returns { title: string, content: string }
         */
        extractTopLevelHeader(content) {
            if (!content) return { title: null, content: content };
            
            const lines = content.split('\n');
            const firstLine = lines[0]?.trim();
            
            // Check if first line is a top-level header (# Title)
            const headerMatch = firstLine?.match(/^# (.+)$/);
            
            if (headerMatch) {
                const extractedTitle = headerMatch[1].trim();
                // Remove the first line and any immediately following empty lines
                let contentStartIndex = 1;
                while (contentStartIndex < lines.length && lines[contentStartIndex].trim() === '') {
                    contentStartIndex++;
                }
                const remainingContent = lines.slice(contentStartIndex).join('\n').trim();
                
                return {
                    title: extractedTitle,
                    content: remainingContent
                };
            }
            
            return { title: null, content: content };
        },

        /**
         * Render markdown content to HTML for modal display
         * Now optionally skips top-level headers if they were extracted
         */
        renderMarkdownContent(content) {
            if (!content) return '<p class="text-gray-600">No content available.</p>';
            
            // Simple markdown to HTML conversion with app styling
            let html = content;
            
            // Convert headings with neutral styling aligned with design system
            html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-gray-800 mb-3 pb-2 border-b border-gray-100">$1</h3>');
            html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-gray-900 mb-4 pb-3 border-b-2 border-gray-200">$1</h2>');
            html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gray-900 mb-6 pb-4 border-b-2 border-gray-300">$1</h1>');
            
            // Convert bold and italic with better styling
            html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
            html = html.replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>');
            
            // Convert inline code with proper styling
            html = html.replace(/`([^`]+)`/g, '<code class="inline-block px-2 py-1 text-sm font-mono bg-gray-100 text-gray-800 border border-gray-200 rounded-md">$1</code>');
            
            // Convert links with neutral design system styling
            html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-gray-700 hover:text-gray-900 font-medium underline decoration-gray-400 hover:decoration-gray-600 transition-colors duration-200">$1<svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>');
            
            // Convert lists with enhanced styling
            const lines = html.split('\n');
            let inList = false;
            const processedLines = [];
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                
                if (line.match(/^- /)) {
                    if (!inList) {
                        processedLines.push('<ul class="list-none space-y-2 mb-6 pl-0">');
                        inList = true;
                    }
                    const listContent = line.substring(2);
                    processedLines.push(`<li class="flex items-start gap-3"><span class="flex-shrink-0 w-2 h-2 bg-gray-400 rounded-full mt-2"></span><span class="text-gray-700 leading-relaxed">${listContent}</span></li>`);
                } else {
                    if (inList) {
                        processedLines.push('</ul>');
                        inList = false;
                    }
                    
                    if (line.trim() === '') {
                        processedLines.push(''); // Preserve blank lines
                    } else if (!line.match(/^<h[1-6]/)) {
                        // Only wrap in paragraph if not already a heading
                        const trimmedLine = line.trim();
                        if (trimmedLine) {
                            processedLines.push(`<p class="text-gray-700 leading-relaxed mb-4">${line}</p>`);
                        }
                    } else {
                        processedLines.push(line);
                    }
                }
            }
            
            if (inList) {
                processedLines.push('</ul>');
            }
            
            return processedLines.join('\n');
        },

        /**
         * Handle internal link clicks
         */
        handleInternalLink(event, link) {
            try {
                // Prevent default navigation
                event.preventDefault();
                
                // Update URL hash
                window.location.hash = link.pageId;
                
                this.announceToScreenReader(`Navigated to ${link.text}`);
                
            } catch (error) {
                console.error('FooterComponent: Failed to handle internal link:', error);
                this.handleError(error, 'Navigation failed');
            }
        },

        /**
         * Handle external link clicks
         */
        handleExternalLink(event, link) {
            // Let the default browser behavior handle external links
            this.announceToScreenReader(`Opening external link: ${link.text}`);
        },

        /**
         * Handle link clicks (external vs internal)
         */
        async handleLinkClick(event, link) {
            if (link.url) {
                // External link - let default behavior handle it
                return true;
            } else {
                // Internal content - show in modal with raw content for proper header extraction
                event.preventDefault();
                const contentToShow = link.rawContent || link.content; // Prefer raw content for header extraction
                this.showInternalContent(link.text, contentToShow);
                return false;
            }
        },
        
        /**
         * Show internal content in modal
         * Now handles top-level header extraction from markdown
         */
        showInternalContent(fallbackTitle, rawContent) {
            // Extract top-level header if present
            const { title, content } = this.extractTopLevelHeader(rawContent);
            
            // Use extracted title or fallback to link text
            this.modalTitle = title || fallbackTitle;
            
            // Render the content (now without the top-level header if it was extracted)
            this.modalContent = this.renderMarkdownContent(content);
            this.showContentModal = true;
            
            // Set focus on modal for accessibility
            this.$nextTick(() => {
                const modal = this.$refs.contentModal;
                if (modal) modal.focus();
            });
        },
        
        /**
         * Close content modal
         */
        closeContentModal() {
            this.showContentModal = false;
            this.modalTitle = '';
            this.modalContent = '';
        },

        /**
         * Handle errors
         */
        handleError(error, customMessage = null) {
            this.error = true;
            this.errorMessage = customMessage || error.message || 'An unexpected error occurred';
            this.errorCount++;
            
            // Determine if retry is possible
            this.canRetry = this._retryCount < this._maxRetries;
            
            console.error('FooterComponent: Error handled:', {
                message: this.errorMessage,
                canRetry: this.canRetry,
                retryCount: this._retryCount,
                errorCount: this.errorCount
            });
        },

        /**
         * Retry loading footer data
         */
        async retryLoad() {
            if (!this.canRetry) {
                return;
            }

            this._retryCount++;
            await this.initializeFooter();
        },

        /**
         * Announce messages to screen readers
         */
        announceToScreenReader(message) {
            this.screenReaderAnnouncement = message;
            
            // Clear the announcement after a short delay
            setTimeout(() => {
                this.screenReaderAnnouncement = '';
            }, 1000);
        }
    };
}

// Make the function globally available
window.footerComponent = footerComponent;

// Register with Alpine.js when it becomes available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Alpine !== 'undefined' && Alpine.data) {
        Alpine.data('footerComponent', footerComponent);
        console.log('FooterComponent: Registered with Alpine.js');
    }
});