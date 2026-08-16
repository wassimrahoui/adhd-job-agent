import { Link } from 'react-router-dom';
import type { JobListItem } from '../types';
import { formatSalary, getRecommendationBadge, getPriorityBadge } from '../types';

interface JobCardProps {
  job: JobListItem;
  index?: number;
}

export function JobCard({ job, index: _index }: JobCardProps) {
  const recBadge = getRecommendationBadge(job.recommendation_category);
  const priorityBadge = getPriorityBadge(job.recommendation_priority);
  const hasAnalysis = job.score !== undefined && job.score !== null;

  return (
    <article
      data-job-card
      tabIndex={0}
      className="card p-5 hover:shadow-md transition-shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
      role="listitem"
      aria-label={job.title}
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1 min-w-0">
          <Link
            to={`/job/${job.id}`}
            className="block hover:text-blue-600 transition-colors"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">{job.title}</h3>
          </Link>
          <p className="text-gray-600 dark:text-gray-400 mt-1">{job.company} • {job.location}</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">{formatSalary(job.salary_min, job.salary_max, job.salary_currency, job.salary_is_predicted)}</p>

          {job.recommendation_primary_reason && (
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{job.recommendation_primary_reason}</p>
          )}
        </div>

        <div className="flex flex-col items-end gap-2 sm:flex-row sm:items-center shrink-0">
          <div className="flex items-center gap-2">
            {hasAnalysis && (
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{Math.round(job.score!)}%</span>
            )}
            <div className="flex flex-col gap-1">
              <span className={`${recBadge.className}`}>{recBadge.label}</span>
              <span className={`${priorityBadge.className}`}>{priorityBadge.label}</span>
            </div>
          </div>

          {job.redirect_url && (
            <a
              href={job.redirect_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-sm whitespace-nowrap"
            >
              Apply →
            </a>
          )}
        </div>
      </div>

      {job.passed_prefilter === false && (
        <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Pre-filtered out</strong> — did not match your profile preferences.
          </p>
        </div>
      )}
    </article>
  );
}