// Simple cookie/consent banner for Vagrantfile Generator
// - Informational only: all storage used is functional/essential
// - Dismiss choice is stored in localStorage to avoid showing repeatedly

;(function () {
  const BANNER_KEY = 'vfg_cookie_banner_dismissed'

  function createBanner() {
    const container = document.createElement('div')
    container.id = 'vfg-cookie-banner'
    container.style.position = 'fixed'
    container.style.left = '0'
    container.style.right = '0'
    container.style.bottom = '0'
    container.style.zIndex = '9999'
    container.style.background = '#111827'
    container.style.color = '#f9fafb'
    container.style.padding = '12px 16px'
    container.style.display = 'flex'
    container.style.flexWrap = 'wrap'
    container.style.justifyContent = 'space-between'
    container.style.alignItems = 'center'

    const text = document.createElement('div')
    text.style.flex = '1 1 60%'
    text.style.fontSize = '14px'
    text.innerHTML = `We only use essential browser storage (login session and preferences). No tracking or advertising cookies are used. <a href="/resources/footer/privacy.md" style="color:#60a5fa; text-decoration:underline;">Privacy details</a>`

    const actions = document.createElement('div')
    actions.style.display = 'flex'
    actions.style.gap = '8px'

    const dismiss = document.createElement('button')
    dismiss.textContent = 'Dismiss'
    dismiss.style.background = '#10b981'
    dismiss.style.border = 'none'
    dismiss.style.color = '#fff'
    dismiss.style.padding = '8px 12px'
    dismiss.style.borderRadius = '6px'
    dismiss.style.cursor = 'pointer'
    dismiss.onclick = () => {
      localStorage.setItem(BANNER_KEY, '1')
      hideBanner()
    }

    const clear = document.createElement('button')
    clear.textContent = 'Clear storage'
    clear.style.background = 'transparent'
    clear.style.border = '1px solid rgba(255,255,255,0.12)'
    clear.style.color = '#fff'
    clear.style.padding = '8px 12px'
    clear.style.borderRadius = '6px'
    clear.style.cursor = 'pointer'
    clear.onclick = () => {
      // Remove known keys used by the app
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_profile')
      localStorage.removeItem('vagrantfile-generator-config')
      // Dismiss banner after clearing
      localStorage.setItem(BANNER_KEY, '1')
      hideBanner()
      alert('Local storage cleared. You will need to sign in again.')
    }

    actions.appendChild(clear)
    actions.appendChild(dismiss)

    container.appendChild(text)
    container.appendChild(actions)

    document.body.appendChild(container)
  }

  function hideBanner() {
    const banner = document.getElementById('vfg-cookie-banner')
    if (banner) banner.remove()
  }

  function init() {
    try {
      if (localStorage.getItem(BANNER_KEY) === '1') return
      // Wait for DOM ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createBanner)
      } else {
        createBanner()
      }
    } catch (e) {
      // If localStorage is not available, still show nothing harmful
      console.warn('cookie-consent init error', e)
    }
  }

  // Expose for manual use
  window.VFGCookieConsent = { init }

  // Auto-init
  init()
})()
