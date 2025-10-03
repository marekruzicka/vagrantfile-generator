(function () {
    async function loadRuntimeConfig() {
        try {
            const response = await fetch('/config.json', { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const config = await response.json();
            window.APP_CONFIG = config;
            window.dispatchEvent(new CustomEvent('app:configLoaded', { detail: config }));
            console.log('Runtime config loaded', config);
            return config;
        } catch (error) {
            console.warn('Runtime config unavailable, using defaults', error);
            if (!window.APP_CONFIG) {
                window.APP_CONFIG = {};
            }
            window.dispatchEvent(new CustomEvent('app:configLoaded', { detail: window.APP_CONFIG }));
            return window.APP_CONFIG;
        }
    }

    window.__loadRuntimeConfig = loadRuntimeConfig;

    // Kick off the load immediately so configuration is ready as early as possible
    loadRuntimeConfig();
})();
