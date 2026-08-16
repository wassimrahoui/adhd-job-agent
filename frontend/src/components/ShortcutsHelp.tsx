import { useEffect, useState } from 'react';
import { formatShortcut, type Shortcut } from '../hooks/useKeyboardShortcuts';

interface ShortcutsHelpProps {
  shortcuts: Shortcut[];
  isOpen: boolean;
  onClose: () => void;
}

export function ShortcutsHelp({ shortcuts, isOpen, onClose }: ShortcutsHelpProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !isOpen) return;
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [mounted, isOpen, onClose]);

  if (!mounted || !isOpen) return null;

  const globalShortcuts = shortcuts.filter(s => s.global);
  const contextualShortcuts = shortcuts.filter(s => !s.global);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-fade-in" role="dialog" aria-modal="true" aria-labelledby="shortcuts-title">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto animate-slide-up">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 id="shortcuts-title" className="text-xl font-semibold text-gray-900">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close shortcuts help"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {globalShortcuts.length > 0 && (
            <section>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Global</h3>
              <div className="space-y-2">
                {globalShortcuts.map((shortcut, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <span className="text-gray-700">{shortcut.description}</span>
                    <kbd className="px-2.5 py-1 bg-gray-100 rounded text-sm font-mono text-gray-600 border border-gray-200">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </section>
          )}

          {contextualShortcuts.length > 0 && (
            <section>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Contextual</h3>
              <div className="space-y-2">
                {contextualShortcuts.map((shortcut, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <span className="text-gray-700">{shortcut.description}</span>
                    <kbd className="px-2.5 py-1 bg-gray-100 rounded text-sm font-mono text-gray-600 border border-gray-200">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <p className="text-sm text-gray-600 text-center">
            Press <kbd className="px-2 py-0.5 bg-white rounded border border-gray-300 font-mono">?</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );
}