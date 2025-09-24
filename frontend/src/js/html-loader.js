/**
 * Simple HTML partial loader for modular architecture
 * Loads HTML partials and replaces placeholder elements
 */

class HTMLLoader {
    constructor() {
        this.cache = new Map();
    }

    async loadPartial(path) {
        if (this.cache.has(path)) {
            return this.cache.get(path);
        }

        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`Failed to load ${path}: ${response.status}`);
            }
            const html = await response.text();
            this.cache.set(path, html);
            return html;
        } catch (error) {
            console.error('Error loading partial:', error);
            return '';
        }
    }

    async loadPartials() {
        // Find all elements with data-include-html attribute
        const includes = document.querySelectorAll('[data-include-html]');
        
        for (const element of includes) {
            const path = element.getAttribute('data-include-html');
            const html = await this.loadPartial(path);
            element.innerHTML = html;
            element.removeAttribute('data-include-html');
        }
    }

    async loadModal(modalId, path) {
        const modalContainer = document.getElementById(modalId);
        if (modalContainer) {
            const html = await this.loadPartial(path);
            modalContainer.innerHTML = html;
        }
    }
}

// Global instance
window.htmlLoader = new HTMLLoader();

// Auto-load partials when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Loading HTML partials...');
    await window.htmlLoader.loadPartials();
    console.log('HTML partials loaded');
});