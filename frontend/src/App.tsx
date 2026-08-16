import { useLocation } from 'react-router-dom';
import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { JobsSearchPage } from './pages/JobsSearchPage';
import { JobDetailsPage } from './pages/JobDetailsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { ShortcutsHelp } from './components/ShortcutsHelp';
import { useKeyboardShortcuts, type Shortcut } from './hooks/useKeyboardShortcuts';
import { useTheme } from './context/ThemeContext';
import './index.css';

const GLOBAL_SHORTCUTS: Shortcut[] = [
  { key: '?', shiftKey: true, action: () => {}, description: 'Show keyboard shortcuts', global: true },
  { key: 'p', ctrlKey: true, action: () => {}, description: 'Go to Profile', global: true },
  { key: 's', ctrlKey: true, action: () => {}, description: 'Go to Settings', global: true },
  { key: 'j', ctrlKey: true, action: () => {}, description: 'Go to Jobs', global: true },
  { key: '/', action: () => {}, description: 'Focus search (on Jobs page)', global: true },
  { key: 'd', ctrlKey: true, shiftKey: true, action: () => {}, description: 'Toggle dark mode', global: true },
];

function Navigation() {
  const location = useLocation();
  const currentPath = location.pathname;
  const { theme, toggleTheme } = useTheme();
  const [showShortcuts, setShowShortcuts] = useState(false);

  const navItems = [
    { path: '/', label: 'Jobs', icon: '🔍', shortcut: '⌘J' },
    { path: '/profile', label: 'Profile', icon: '👤', shortcut: '⌘P' },
    { path: '/settings', label: 'Settings', icon: '⚙️', shortcut: '⌘S' },
  ];

  const handleGlobalShortcuts = () => {
    if (currentPath === '/') {
      const searchButton = document.querySelector('button[data-search-button]') as HTMLButtonElement;
      if (searchButton && !searchButton.disabled) {
        searchButton.focus();
      }
    }
  };

  useKeyboardShortcuts([
    { key: '?', shiftKey: true, action: () => setShowShortcuts(true), description: 'Show keyboard shortcuts', global: true },
    { key: 'p', ctrlKey: true, action: () => { window.location.href = '/profile'; }, description: 'Go to Profile', global: true },
    { key: 's', ctrlKey: true, action: () => { window.location.href = '/settings'; }, description: 'Go to Settings', global: true },
    { key: 'j', ctrlKey: true, action: () => { window.location.href = '/'; }, description: 'Go to Jobs', global: true },
    { key: '/', action: handleGlobalShortcuts, description: 'Focus search (on Jobs page)', global: true },
    { key: 'd', ctrlKey: true, shiftKey: true, action: toggleTheme, description: 'Toggle dark mode', global: true },
  ]);

  return (
    <>
      <nav className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 text-xl font-semibold text-gray-900 dark:text-gray-100">
              <span>🧠</span>
              <span>ADHD Job Agent</span>
            </Link>
            <div className="flex items-center gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPath === item.path || (item.path !== '/' && currentPath.startsWith(item.path))
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-slate-800'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                  <span className="hidden sm:inline-flex px-1.5 py-0.5 text-xs font-mono text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-slate-800 rounded">
                    {item.shortcut}
                  </span>
                </Link>
              ))}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-800 transition-colors"
                aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {theme === 'dark' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
              <button
                onClick={() => setShowShortcuts(true)}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-800 transition-colors"
                aria-label="Show keyboard shortcuts (Shift+?)"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>
      <ShortcutsHelp shortcuts={GLOBAL_SHORTCUTS} isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Routes>
            <Route path="/" element={<JobsSearchPage />} />
            <Route path="/job/:jobId" element={<JobDetailsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;