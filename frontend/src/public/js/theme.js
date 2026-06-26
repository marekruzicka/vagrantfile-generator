(function () {
  const STORAGE_KEY = 'vfg-theme'
  const DARK_THEME_COLOR = '#1e293b'
  const LIGHT_THEME_COLOR = '#3b82f6'
  const mediaQuery = window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

  let currentMode = normalizeMode(readStoredMode())
  let currentIsDark = false

  function normalizeMode(mode) {
    return mode === 'light' || mode === 'dark' || mode === 'auto' ? mode : 'auto'
  }

  function readStoredMode() {
    try {
      return window.localStorage.getItem(STORAGE_KEY)
    } catch (error) {
      return null
    }
  }

  function writeStoredMode(mode) {
    try {
      if (mode === 'auto') {
        window.localStorage.removeItem(STORAGE_KEY)
      } else {
        window.localStorage.setItem(STORAGE_KEY, mode)
      }
    } catch (error) {
      // Ignore storage access errors; theme still applies for this page load.
    }
  }

  function preferredDark() {
    return Boolean(mediaQuery && mediaQuery.matches)
  }

  function resolveIsDark(mode) {
    if (mode === 'dark') return true
    if (mode === 'light') return false
    return preferredDark()
  }

  function updateThemeColor(isDark) {
    let meta = document.querySelector('meta[name="theme-color"]')
    if (!meta) {
      meta = document.createElement('meta')
      meta.setAttribute('name', 'theme-color')
      document.head.appendChild(meta)
    }
    meta.setAttribute('content', isDark ? DARK_THEME_COLOR : LIGHT_THEME_COLOR)
  }

  function dispatchThemeChange(mode, isDark) {
    window.dispatchEvent(
      new CustomEvent('vfg-theme-change', {
        detail: { mode, isDark },
      }),
    )
  }

  function applyTheme(mode, shouldDispatch) {
    currentMode = normalizeMode(mode)
    const isDark = resolveIsDark(currentMode)
    currentIsDark = isDark
    document.documentElement.classList.toggle('dark', isDark)
    updateThemeColor(isDark)

    if (shouldDispatch) {
      dispatchThemeChange(currentMode, isDark)
    }
  }

  function setTheme(mode) {
    const nextMode = normalizeMode(mode)
    writeStoredMode(nextMode)
    applyTheme(nextMode, true)
  }

  function getTheme() {
    return currentMode
  }

  function toggle() {
    setTheme(currentIsDark ? 'light' : 'dark')
  }

  if (mediaQuery) {
    const handlePreferenceChange = function () {
      if (normalizeMode(readStoredMode()) === 'auto') {
        applyTheme('auto', true)
      }
    }

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handlePreferenceChange)
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handlePreferenceChange)
    }
  }

  window.__theme = { getTheme, setTheme, toggle }
  applyTheme(currentMode, false)
})()
