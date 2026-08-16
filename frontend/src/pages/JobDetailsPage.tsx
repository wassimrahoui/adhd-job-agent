import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Job } from '../types';
import { formatSalary, getRecommendationBadge, getPriorityBadge, getConfidenceBadge } from '../types';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Badge } from '../components/Badge';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export function JobDetailsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadJob = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.jobs.get(parseInt(jobId));
      setJob(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  useKeyboardShortcuts([
    { key: 'ArrowLeft', action: () => window.history.back(), description: 'Go back to jobs list', global: false },
    { key: 'b', ctrlKey: true, action: () => window.history.back(), description: 'Go back to jobs list', global: false },
    { key: 'a', ctrlKey: true, action: () => { if (job?.redirect_url) window.open(job.redirect_url, '_blank'); }, description: 'Open apply link', global: false },
    { key: 'r', ctrlKey: true, action: loadJob, description: 'Reload job details', global: false },
  ], !loading && !!job);

  if (loading) {
    return <LoadingOverlay message="Loading job details..." />;
  }

  if (error || !job) {
    return (
      <div className="max-w-4xl mx-auto">
        <ErrorMessage message={error || 'Job not found'} onRetry={loadJob} />
      </div>
    );
  }

  const analysis = job.analysis;
  const recBadge = getRecommendationBadge(job.recommendation_category);
  const priorityBadge = getPriorityBadge(job.recommendation_priority);
  const confidenceBadge = getConfidenceBadge(analysis?.confidence);

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="btn-ghost text-sm mb-6 inline-flex items-center gap-1">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Jobs
      </Link>

      <div className="space-y-6">
        <article className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
              <p className="text-gray-600 mt-1 text-lg">{job.company}</p>
              <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-gray-500">
                {job.location && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {job.location}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {formatSalary(job.salary_min, job.salary_max, job.salary_currency, job.salary_is_predicted)}
                </span>
                {job.employment_type && (
                  <Badge variant="info">{job.employment_type}</Badge>
                )}
                {job.work_mode && (
                  <Badge variant="gray">{job.work_mode}</Badge>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 sm:flex-row sm:items-center shrink-0">
              <div className="flex flex-col items-end gap-1">
                {analysis?.score !== undefined && analysis?.score !== null && (
                  <div className="text-3xl font-bold text-gray-900">{Math.round(analysis.score)}%</div>
                )}
                <div className="flex flex-col gap-1">
                  <span className={`${recBadge.className} px-3 py-1`}>{recBadge.label}</span>
                  <span className={`${priorityBadge.className} px-3 py-1`}>{priorityBadge.label}</span>
                  {analysis?.confidence && (
                    <span className={`${confidenceBadge.className} px-3 py-1`}>{confidenceBadge.label}</span>
                  )}
                </div>
              </div>
              {job.redirect_url && (
                <a
                  href={job.redirect_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary text-lg px-6 py-3 whitespace-nowrap"
                >
                  Apply on Company Site →
                </a>
              )}
            </div>
          </div>

          {job.recommendation_explanation && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="font-medium text-blue-900 mb-2">Why this match?</h3>
              <p className="text-blue-800">{job.recommendation_explanation}</p>
            </div>
          )}

          {job.recommendation_primary_reason && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg mt-4">
              <h3 className="font-medium text-gray-900 mb-2">Primary Reason</h3>
              <p className="text-gray-700">{job.recommendation_primary_reason}</p>
            </div>
          )}

          {job.recommendation_secondary_reasons.length > 0 && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg mt-4">
              <h3 className="font-medium text-gray-900 mb-2">Additional Reasons</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {job.recommendation_secondary_reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis?.explanation && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg mt-4">
              <h3 className="font-medium text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{analysis.explanation}</p>
            </div>
          )}
        </article>

        <div className="grid gap-6 md:grid-cols-2">
          {((analysis?.matching_skills.length ?? 0) > 0 || job.recommendation_missing_skills.length > 0) && (
            <section className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Skills
              </h2>
              <div className="space-y-4">
                {analysis && analysis.matching_skills.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-green-700 mb-2">Matched ({analysis.matching_skills.length})</h3>
                    <div className="flex flex-wrap gap-2">
                      {analysis.matching_skills.map((item, i) => (
                        <Badge key={i} variant="success">{item.claim}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {job.recommendation_missing_skills.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-red-700 mb-2">Missing ({job.recommendation_missing_skills.length})</h3>
                    <div className="flex flex-wrap gap-2">
                      {job.recommendation_missing_skills.map((skill, i) => (
                        <Badge key={i} variant="error">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {analysis && analysis.matching_experience.length > 0 && (
            <section className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                Matched Experience
              </h2>
              <ul className="space-y-1 text-gray-700">
                {analysis.matching_experience.map((item, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {item.claim}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {analysis && analysis.missing_requirements.length > 0 && (
            <section className="card p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Missing Requirements
              </h2>
              <div className="space-y-3">
                {analysis.missing_requirements.map((req, i) => (
                  <div key={i} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <p className="font-medium text-gray-900">{req.claim}</p>
                    {req.source_excerpt && <p className="text-sm text-gray-600 mt-1">"{req.source_excerpt}"</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {analysis && analysis.unknown_requirements && analysis.unknown_requirements.length > 0 && (
            <section className="card p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Unknown Requirements
              </h2>
              <div className="space-y-3">
                {analysis.unknown_requirements.map((req, i) => (
                  <div key={i} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <p className="font-medium text-gray-900">{req.claim}</p>
                    {req.source_excerpt && <p className="text-sm text-gray-600 mt-1">"{req.source_excerpt}"</p>}
                    <p className="text-xs text-gray-500 mt-1">Not mentioned in your profile — cannot confirm match or gap</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {analysis && analysis.evidence && analysis.evidence.length > 0 && (
            <section className="card p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Evidence
              </h2>
              <div className="space-y-3">
                {analysis.evidence.map((item, i) => (
                  <div key={i} className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <p className="font-medium text-gray-900">{item.claim}</p>
                    {item.source_excerpt && <p className="text-sm text-gray-600 mt-1">"{item.source_excerpt}"</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {job.recommendation_strengths.length > 0 && (
            <section className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Strengths
              </h2>
              <ul className="space-y-2">
                {job.recommendation_strengths.map((strength, i) => (
                  <li key={i} className="flex items-center gap-2 text-gray-700">
                    <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {strength}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {job.recommendation_concerns.length > 0 && (
            <section className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Concerns
              </h2>
              <ul className="space-y-2">
                {job.recommendation_concerns.map((concern, i) => (
                  <li key={i} className="flex items-center gap-2 text-gray-700">
                    <svg className="w-4 h-4 text-yellow-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {concern}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {job.recommendation_action_items.length > 0 && (
            <section className="card p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                Recommended Actions
              </h2>
              <ol className="space-y-2">
                {job.recommendation_action_items.map((action, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-sm font-medium flex items-center justify-center">
                      {i + 1}
                    </span>
                    <p className="text-gray-700 mt-0.5">{action}</p>
                  </li>
                ))}
              </ol>
            </section>
          )}

          <section className="card p-6 md:col-span-2">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Description</h2>
            <div className="prose prose-gray max-w-none whitespace-pre-wrap text-gray-700">
              {job.description}
            </div>
          </section>
        </div>

        {job.redirect_url && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <a
              href={job.redirect_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-lg px-8 py-3 inline-flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Apply on Company Site
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
