import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { JobListItem } from '../types';
import { JobCard } from '../components/JobCard';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';
import { useToast } from '../components/Toast';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export function JobsSearchPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPrefiltered, setShowPrefiltered] = useState(false);
  const [profileExists, setProfileExists] = useState(false);
  const searchButtonRef = useRef<HTMLButtonElement>(null);
  const { showToast } = useToast();

  useEffect(() => {
    loadProfileAndJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadProfileAndJobs() {
    try {
      await api.profile.get();
      setProfileExists(true);
      loadJobs();
    } catch {
      setProfileExists(false);
      setLoading(false);
    }
  }

  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.jobs.list({ passed_prefilter: showPrefiltered ? true : undefined });
      setJobs(data);
      showToast('success', `Loaded ${data.length} jobs`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load jobs';
      setError(message);
      showToast('error', message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    if (!profileExists) return;
    setSearching(true);
    setError(null);
    try {
      const result = await api.search.run();
      await loadJobs();
      showToast('success', `Search complete: ${result.jobs_new} new jobs, ${result.jobs_updated} updated`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      showToast('error', message);
    } finally {
      setSearching(false);
    }
  }

  async function handleAnalyze() {
    if (!profileExists) return;
    setSearching(true);
    setError(null);
    try {
      const result = await api.processing.run({ only_passed: true, limit: 50, skip_existing: true });
      await loadJobs();
      const message = result.failed > 0
        ? `Processed ${result.processed} jobs, ${result.failed} failed, ${result.skipped} skipped`
        : `Processed ${result.processed} jobs, ${result.skipped} skipped`;
      showToast(result.failed > 0 ? 'warning' : 'success', message);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      showToast('error', message);
    } finally {
      setSearching(false);
    }
  }

  const displayedJobs = jobs.filter(job => showPrefiltered || job.passed_prefilter !== false);
  const prefilteredCount = jobs.filter(job => job.passed_prefilter === false).length;
  const analyzedCount = jobs.filter(job => job.score !== undefined && job.score !== null).length;

  // Keyboard shortcuts for job navigation
  useKeyboardShortcuts([
    { key: 'ArrowDown', action: () => focusNextJob(), description: 'Focus next job card', global: false },
    { key: 'ArrowUp', action: () => focusPreviousJob(), description: 'Focus previous job card', global: false },
    { key: 'Enter', action: () => openFocusedJob(), description: 'Open focused job details', global: false },
    { key: 'n', ctrlKey: true, action: handleSearch, description: 'Search jobs', global: false },
    { key: 'a', ctrlKey: true, action: handleAnalyze, description: 'Analyze all jobs', global: false },
  ], displayedJobs.length > 0);

  function focusNextJob() {
    const cards = document.querySelectorAll('[data-job-card]');
    const focused = document.activeElement;
    let nextIndex = 0;
    cards.forEach((card, i) => {
      if (card === focused || card.contains(focused as Node)) {
        nextIndex = Math.min(i + 1, cards.length - 1);
      }
    });
    (cards[nextIndex] as HTMLElement)?.focus();
  }

  function focusPreviousJob() {
    const cards = document.querySelectorAll('[data-job-card]');
    const focused = document.activeElement;
    let prevIndex = cards.length - 1;
    cards.forEach((card, i) => {
      if (card === focused || card.contains(focused as Node)) {
        prevIndex = Math.max(i - 1, 0);
      }
    });
    (cards[prevIndex] as HTMLElement)?.focus();
  }

  function openFocusedJob() {
    const focused = document.activeElement;
    const card = focused?.closest('[data-job-card]');
    const link = card?.querySelector('a[href^="/job/"]') as HTMLAnchorElement;
    link?.click();
  }

  if (loading) {
    return <LoadingOverlay message="Loading jobs..." />;
  }

  if (!profileExists) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">Welcome to ADHD Job Agent</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            To get started, create your profile with your skills, preferences, and experience.
            Then search for jobs that match your profile.
          </p>
          <Link to="/profile" className="btn-primary text-lg px-8 py-3">
            Create Profile →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Job Search</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {jobs.length} jobs found • {analyzedCount} analyzed • {prefilteredCount} pre-filtered out
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              ref={searchButtonRef}
              onClick={handleSearch}
              disabled={searching}
              className="btn-primary"
              data-search-button
            >
              {searching ? 'Searching...' : '🔍 Search Jobs'}
            </button>
            <button
              onClick={handleAnalyze}
              disabled={searching || analyzedCount === jobs.length}
              className="btn-secondary"
            >
              Analyze All
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showPrefiltered}
              onChange={e => setShowPrefiltered(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Show pre-filtered out jobs ({prefilteredCount})</span>
          </label>
        </div>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} onRetry={loadJobs} />
        </div>
      )}

      {displayedJobs.length === 0 ? (
        <EmptyState
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          title={showPrefiltered ? 'No jobs found' : 'No matching jobs'}
          description={showPrefiltered
            ? 'No jobs in the database yet. Click "Search Jobs" to find new opportunities.'
            : 'All remaining jobs were pre-filtered out. Adjust your profile preferences or enable "Show pre-filtered out jobs".'}
          action={<button onClick={handleSearch} className="btn-primary" disabled={searching}>
            {searching ? 'Searching...' : 'Search Jobs'}
          </button>}
        />
      ) : (
        <div className="space-y-4" role="list" aria-label="Job results">
          {displayedJobs.map((job, index) => (
            <JobCard key={job.id} job={job} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}