import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { JobListItem } from '../types';
import { JobCard } from '../components/JobCard';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage, EmptyState } from '../components/ErrorMessage';

export function JobsSearchPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPrefiltered, setShowPrefiltered] = useState(false);
  const [profileExists, setProfileExists] = useState(false);

  useEffect(() => {
    loadProfileAndJobs();
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    if (!profileExists) return;
    setSearching(true);
    setError(null);
    try {
      await api.search.run({});
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  }

  async function handleAnalyze() {
    if (!profileExists) return;
    setSearching(true);
    setError(null);
    try {
      await api.analysis.run({});
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setSearching(false);
    }
  }

  if (loading) {
    return <LoadingOverlay message="Loading jobs..." />;
  }

  if (!profileExists) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Welcome to ADHD Job Agent</h1>
          <p className="text-gray-600 mb-8">
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

  const displayedJobs = jobs.filter(job => showPrefiltered || job.passed_prefilter !== false);
  const prefilteredCount = jobs.filter(job => job.passed_prefilter === false).length;
  const analyzedCount = jobs.filter(job => job.ai_score !== undefined).length;

  return (
    <div>
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
            <p className="text-gray-600 mt-1">
              {jobs.length} jobs found • {analyzedCount} analyzed • {prefilteredCount} pre-filtered out
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleSearch}
              disabled={searching}
              className="btn-primary"
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
            <span className="text-sm text-gray-700">Show pre-filtered out jobs ({prefilteredCount})</span>
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
        <div className="space-y-4">
          {displayedJobs.map(job => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}