import type {
  Profile,
  ProfileInput,
  JobListItem,
  Job,
  SearchResponse,
  AnalysisRunResponse,
  ProcessingResponse,
  HealthResponse,
  SettingsStatus,
} from '../types';

const API_BASE = '';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = error?.detail;
    const message = typeof detail === 'string' ? detail : detail?.message || `HTTP ${response.status}`;
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  profile: {
    get: () => request<Profile>('/profile'),
    upsert: (data: ProfileInput) =>
      request<Profile>('/profile', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },

  jobs: {
    list: (params?: { passed_prefilter?: boolean; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.passed_prefilter !== undefined) searchParams.set('passed_prefilter', String(params.passed_prefilter));
      if (params?.limit) searchParams.set('limit', String(params.limit));
      if (params?.offset) searchParams.set('offset', String(params.offset));
      const query = searchParams.toString();
      return request<JobListItem[]>(`/jobs${query ? `?${query}` : ''}`);
    },
    get: (id: number) => request<Job>(`/jobs/${id}`),
  },

  search: {
    run: () => request<SearchResponse>('/jobs/search', { method: 'POST' }),
  },

  analysis: {
    run: (params?: { only_passed?: boolean; limit?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.only_passed !== undefined) searchParams.set('only_passed', String(params.only_passed));
      if (params?.limit) searchParams.set('limit', String(params.limit));
      const query = searchParams.toString();
      return request<AnalysisRunResponse>(`/analysis/run${query ? `?${query}` : ''}`, { method: 'POST' });
    },
    getJobInput: (jobId: number) => request<{ job: unknown; profile: unknown }>(`/analysis/job/${jobId}`),
  },

  processing: {
    run: (params?: { only_passed?: boolean; limit?: number; skip_existing?: boolean }) =>
      request<ProcessingResponse>('/processing/run', {
        method: 'POST',
        body: JSON.stringify({
          only_passed: params?.only_passed ?? true,
          limit: params?.limit ?? 50,
          skip_existing: params?.skip_existing ?? true,
        }),
      }),
  },

  settings: {
    getStatus: () => request<SettingsStatus>('/settings/status'),
  },
};
