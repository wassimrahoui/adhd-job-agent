const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

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
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  health: () => request<{ status: string; database: string; ollama: string }>('/health'),

  profile: {
    get: () => request<import('../types').Profile>('/profile'),
    create: (data: import('../types').ProfileCreate) =>
      request<import('../types').Profile>('/profile', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (data: import('../types').ProfileUpdate) =>
      request<import('../types').Profile>('/profile', {
        method: 'PATCH',
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
      return request<import('../types').JobListItem[]>(`/jobs${query ? `?${query}` : ''}`);
    },
    get: (id: number) => request<import('../types').Job>(`/jobs/${id}`),
  },

  search: {
    run: (data: import('../types').SearchRequest) =>
      request<import('../types').SearchResponse>('/jobs/search', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  analysis: {
    run: (data: import('../types').AnalysisRunRequest) =>
      request<import('../types').AnalysisRunResponse>('/analysis/run', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getJobInput: (jobId: number) =>
      request<{ job: import('../types').Job; profile: import('../types').Profile }>(`/analysis/job/${jobId}`),
  },

  settings: {
    getStatus: () => request<import('../types').SettingsStatus>('/settings/status'),
  },
};