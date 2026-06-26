from pathlib import Path
import re

base = Path('/home/marek/projects/local/vagrant/Vagrantfile-generator/frontend/src')
files = [
    base/'index.html', base/'landing.html', base/'views/login/login.html',
    base/'views/header.html', base/'views/projects-list.html', base/'views/project-detail.html',
    base/'components/notifications.html', base/'components/footer.html', base/'components/error-page.html',
]
files += sorted((base/'modals').glob('*.html'))

repls = {
    'bg-white/50': 'bg-white/50 dark:bg-gray-800/50',
    'bg-white': 'bg-white dark:bg-gray-800',
    'bg-gray-50': 'bg-gray-50 dark:bg-gray-900',
    'bg-gray-100': 'bg-gray-100 dark:bg-gray-700',
    'bg-gray-200': 'bg-gray-200 dark:bg-gray-600',
    'bg-slate-50': 'bg-slate-50 dark:bg-gray-800',
    'from-slate-50': 'from-slate-50 dark:from-gray-900',
    'to-blue-50': 'to-blue-50 dark:to-gray-800',
    'text-gray-900': 'text-gray-900 dark:text-gray-100',
    'text-gray-800': 'text-gray-800 dark:text-gray-200',
    'text-gray-700': 'text-gray-700 dark:text-gray-300',
    'text-gray-600': 'text-gray-600 dark:text-gray-400',
    'text-gray-500': 'text-gray-500 dark:text-gray-400',
    'text-gray-400': 'text-gray-400 dark:text-gray-500',
    'text-slate-600': 'text-slate-600 dark:text-gray-300',
    'border-gray-200': 'border-gray-200 dark:border-gray-700',
    'border-gray-100': 'border-gray-100 dark:border-gray-700',
    'border-gray-300': 'border-gray-300 dark:border-gray-600',
    'border-slate-200': 'border-slate-200 dark:border-gray-700',
    'hover:bg-gray-100': 'hover:bg-gray-100 dark:hover:bg-gray-700',
    'hover:bg-gray-50': 'hover:bg-gray-50 dark:hover:bg-gray-700',
    'hover:text-gray-700': 'hover:text-gray-700 dark:hover:text-gray-200',
    'hover:text-gray-600': 'hover:text-gray-600 dark:hover:text-gray-300',
    'disabled:bg-gray-100': 'disabled:bg-gray-100 dark:disabled:bg-gray-700',
    'focus:ring-offset-2': 'focus:ring-offset-2 dark:focus:ring-offset-gray-800',
    'bg-blue-100': 'bg-blue-100 dark:bg-blue-900/40',
    'text-blue-800': 'text-blue-800 dark:text-blue-300',
    'bg-green-100': 'bg-green-100 dark:bg-green-900/40',
    'text-green-800': 'text-green-800 dark:text-green-300',
    'bg-red-100': 'bg-red-100 dark:bg-red-900/40',
    'text-red-800': 'text-red-800 dark:text-red-300',
    'bg-yellow-100': 'bg-yellow-100 dark:bg-yellow-900/40',
    'text-yellow-800': 'text-yellow-800 dark:text-yellow-300',
    'bg-orange-100': 'bg-orange-100 dark:bg-orange-900/40',
    'text-orange-800': 'text-orange-800 dark:text-orange-300',
    'bg-purple-100': 'bg-purple-100 dark:bg-purple-900/40',
    'text-purple-800': 'text-purple-800 dark:text-purple-300',
    'bg-amber-100': 'bg-amber-100 dark:bg-amber-900/40',
    'text-amber-800': 'text-amber-800 dark:text-amber-300',
    'bg-blue-50': 'bg-blue-50 dark:bg-blue-900/20',
    'bg-yellow-50': 'bg-yellow-50 dark:bg-yellow-900/20',
    'bg-red-50': 'bg-red-50 dark:bg-red-900/20',
    'bg-green-50': 'bg-green-50 dark:bg-green-900/20',
    'bg-amber-50/20': 'bg-amber-50/20 dark:bg-amber-900/20',
    'text-yellow-700': 'text-yellow-700 dark:text-yellow-300',
    'text-red-700': 'text-red-700 dark:text-red-300',
    'text-green-700': 'text-green-700 dark:text-green-300',
    'text-blue-700': 'text-blue-700 dark:text-blue-300',
    'border-yellow-200': 'border-yellow-200 dark:border-yellow-800',
    'border-red-200': 'border-red-200 dark:border-red-800',
    'border-green-200': 'border-green-200 dark:border-green-800',
    'border-blue-100': 'border-blue-100 dark:border-gray-700',
    'border-blue-200': 'border-blue-200 dark:border-blue-800',
    'border-amber-200': 'border-amber-200 dark:border-amber-700',
}

# Longest first to avoid partial token issues.
items = sorted(repls.items(), key=lambda kv: len(kv[0]), reverse=True)
for path in files:
    text = path.read_text()
    original = text
    for token, replacement in items:
        dark_part = replacement.split(' ', 1)[1]
        pattern = re.compile(r'(?<![^\s"\'`])' + re.escape(token) + r'(?![^\s"\'`])')
        def sub(m):
            # Skip if exact replacement is already present at this position.
            end = m.end()
            if text[end:end + 1 + len(dark_part)] == ' ' + dark_part:
                return token
            return replacement
        text = pattern.sub(sub, text)
    if text != original:
        path.write_text(text)
        print(path)
