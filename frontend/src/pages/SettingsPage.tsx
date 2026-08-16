import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { SettingsStatus } from '../types';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Badge } from '../components/Badge';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export function SettingsPage() {
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useKeyboardShortcuts([
    { key: 'r', ctrlKey: true, action: loadStatus, description: 'Refresh status', global: false },
    { key: 'c', ctrlKey: true, action: checkConnections, description: 'Check connections', global: false },
  ], !loading && !!status);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.settings.getStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }

  async function checkConnections() {
    setChecking(true);
    setError(null);
    try {
      const data = await api.settings.getStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Health check failed');
    } finally {
      setChecking(false);
    }
  }

  if (loading) {
    return <LoadingOverlay message="Loading settings..." />;
  }

  if (!status) {
    return (
      <div className="max-w-2xl mx-auto">
        <ErrorMessage message={error || 'Failed to load settings'} onRetry={loadStatus} />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings & Status</h1>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Service Status
        </h2>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">Adzuna API</h3>
              <Badge variant={status.adzuna_connected ? 'success' : 'error'}>
                {status.adzuna_connected ? 'Connected' : 'Not Configured'}
              </Badge>
            </div>
            <p className="text-sm text-gray-600">
              Job search source. Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in backend .env
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">Ollama (Local AI)</h3>
              <Badge variant={status.ollama_connected ? 'success' : 'error'}>
                {status.ollama_connected ? 'Connected' : 'Unavailable'}
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              Model: <code className="px-1.5 py-0.5 bg-gray-200 rounded text-xs">{status.ollama_model}</code>
            </p>
            <p className="text-sm text-gray-600">
              {status.ollama_model_installed ? 'Model is installed locally' : 'Model not found - run `ollama pull ' + status.ollama_model + '`'}
            </p>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={checkConnections}
            disabled={checking}
            className="btn-secondary"
          >
            {checking ? 'Checking...' : 'Check Connections'}
          </button>
        </div>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          Matching Threshold
        </h2>

        <div className="space-y-4">
          <div>
            <label className="label">Relevance Score Threshold</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="100"
                value={status.relevance_threshold}
                className="flex-1"
                disabled
              />
              <span className="text-lg font-mono text-gray-900 w-16">{status.relevance_threshold}%</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Jobs below this score are hidden by default. Configure in backend settings.
            </p>
          </div>
        </div>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          About
        </h2>

        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-600">Application</dt>
            <dd className="font-medium text-gray-900">ADHD Job Agent</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Version</dt>
            <dd className="font-medium text-gray-900">0.1.0 (MVP)</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Backend</dt>
            <dd className="font-medium text-gray-900">FastAPI + Python 3.12</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Frontend</dt>
            <dd className="font-medium text-gray-900">React 18 + TypeScript + Vite</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Database</dt>
            <dd className="font-medium text-gray-900">SQLite (local file)</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">AI Model</dt>
            <dd className="font-medium text-gray-900">{status.ollama_model}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Job Source</dt>
            <dd className="font-medium text-gray-900">Adzuna API</dd>
          </div>
        </dl>
      </section>

      <section className="card p-6 border-amber-200 bg-amber-50">
        <h2 className="text-lg font-semibold text-amber-900 mb-2 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Important Notes
        </h2>
        <ul className="list-disc list-inside space-y-1 text-amber-800 text-sm">
          <li>This is a local-first application. All data stays on your machine.</li>
          <li>No cloud LLMs are used - only local Ollama for AI analysis.</li>
          <li>No automatic applications - you apply manually on the company site.</li>
          <li>No application tracking - this tool ends at showing you relevant jobs.</li>
          <li>Configure Adzuna API keys in backend/.env for job search to work.</li>
        </ul>
      </section>
    </div>
  );
}