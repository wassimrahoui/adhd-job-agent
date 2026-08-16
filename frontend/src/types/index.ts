export type RemotePreference = 'remote' | 'hybrid' | 'on_site' | 'any';
export type ExperienceLevel = 'entry' | 'junior' | 'mid' | 'senior' | 'lead' | 'principal' | 'any';

export interface Profile {
  id: number;
  work_experience?: string;
  technical_skills: string[];
  networking_experience?: string;
  education?: string;
  certifications: string[];
  languages: string[];
  desired_roles: string[];
  location_preferences: string[];
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  remote_preference: RemotePreference;
  experience_level: ExperienceLevel;
  excluded_keywords: string[];
  relevance_threshold: number;
  resume_text?: string;
  resume_file_path?: string;
  created_at?: string;
  updated_at?: string;
}

export type ProfileInput = Omit<Profile, 'id' | 'created_at' | 'updated_at'>;

export interface AnalysisMatchItem {
  claim: string;
  source_excerpt?: string;
}

export interface RequirementGapItem {
  claim: string;
  source_excerpt: string;
}

export interface EvidenceItem {
  claim: string;
  source_excerpt?: string;
}

export interface AIAnalysis {
  id: number;
  job_id: number;
  model_used: string;
  score?: number;
  recommendation?: string;
  confidence?: 'high' | 'medium' | 'low';
  matching_skills: AnalysisMatchItem[];
  matching_experience: AnalysisMatchItem[];
  missing_requirements: RequirementGapItem[];
  unknown_requirements: RequirementGapItem[];
  explanation?: string;
  evidence: EvidenceItem[];
  status: string;
  created_at: string;
}

export interface JobListItem {
  id: number;
  adzuna_id: string;
  title: string;
  company?: string;
  location?: string;
  work_mode?: string;
  employment_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  salary_is_predicted: boolean;
  redirect_url?: string;
  posted_at?: string;
  discovered_at: string;
  passed_prefilter: boolean;
  score?: number;
  recommendation?: string;
  confidence?: string;
  recommendation_category?: RecommendationCategory;
  recommendation_priority?: RecommendationPriority;
  recommendation_primary_reason?: string;
  recommendation_explanation?: string;
  recommended_at?: string;
  recommendation_model?: string;
}

export interface Job {
  id: number;
  adzuna_id: string;
  title: string;
  company?: string;
  location?: string;
  work_mode?: string;
  employment_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  salary_is_predicted: boolean;
  description?: string;
  requirements?: string;
  skills: string[];
  redirect_url?: string;
  posted_at?: string;
  discovered_at: string;
  raw_evidence: Record<string, unknown>;
  passed_prefilter: boolean;
  analysis?: AIAnalysis;
  recommendation_category?: RecommendationCategory;
  recommendation_priority?: RecommendationPriority;
  recommendation_primary_reason?: string;
  recommendation_secondary_reasons: string[];
  recommendation_explanation?: string;
  recommendation_missing_skills: string[];
  recommendation_strengths: string[];
  recommendation_concerns: string[];
  recommendation_action_items: string[];
  recommended_at?: string;
  recommendation_model?: string;
}

export interface SearchResponse {
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  jobs_duplicate: number;
  quota_exhausted: boolean;
  quota_message?: string;
  search_duration_ms?: number;
}

export interface AnalysisRunResponse {
  jobs_total: number;
  analyzed: number;
  failed: number;
  skipped_existing: number;
}

export type ProcessingJobState =
  | 'pending'
  | 'analyzing'
  | 'scoring'
  | 'recommending'
  | 'completed'
  | 'failed'
  | 'skipped';

export interface JobProcessingResult {
  job_id: number;
  state: ProcessingJobState;
  error?: string;
}

export interface ProcessingResponse {
  jobs_total: number;
  processed: number;
  failed: number;
  skipped: number;
  results: JobProcessingResult[];
}

export interface HealthResponse {
  status: string;
  database: string;
  ollama: string;
}

export interface SettingsStatus {
  adzuna_connected: boolean;
  ollama_connected: boolean;
  ollama_model: string;
  ollama_model_installed: boolean;
  relevance_threshold: number;
}

export type RecommendationCategory = 'strong_match' | 'possible_match' | 'weak_match' | 'not_enough_information';
export type RecommendationPriority = 'high' | 'medium' | 'low';
export type ConfidenceLevel = 'high' | 'medium' | 'low';

export const RECOMMENDATION_LABELS: Record<RecommendationCategory, { label: string; color: string }> = {
  strong_match: { label: 'Strong Match', color: 'badge-success' },
  possible_match: { label: 'Possible Match', color: 'badge-info' },
  weak_match: { label: 'Weak Match', color: 'badge-warning' },
  not_enough_information: { label: 'Not Enough Info', color: 'badge-gray' },
};

export const PRIORITY_LABELS: Record<RecommendationPriority, { label: string; color: string }> = {
  high: { label: 'High Priority', color: 'badge-error' },
  medium: { label: 'Medium Priority', color: 'badge-warning' },
  low: { label: 'Low Priority', color: 'badge-info' },
};

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, { label: string; color: string }> = {
  high: { label: 'High Confidence', color: 'badge-success' },
  medium: { label: 'Medium Confidence', color: 'badge-warning' },
  low: { label: 'Low Confidence', color: 'badge-error' },
};

export function formatSalary(min?: number, max?: number, currency = 'EUR', isPredicted = false): string {
  const pred = isPredicted ? ' (est.)' : '';
  if (min && max) {
    return `${min.toLocaleString()} - ${max.toLocaleString()} ${currency}${pred}`;
  }
  if (min) {
    return `From ${min.toLocaleString()} ${currency}${pred}`;
  }
  if (max) {
    return `Up to ${max.toLocaleString()} ${currency}${pred}`;
  }
  return 'Not specified';
}

export function getRecommendationBadge(category: RecommendationCategory | undefined): { label: string; className: string } {
  if (!category) return { label: 'Not Analyzed', className: 'badge-gray' };
  const info = RECOMMENDATION_LABELS[category];
  return { label: info.label, className: info.color };
}

export function getPriorityBadge(priority: RecommendationPriority | undefined): { label: string; className: string } {
  if (!priority) return { label: '-', className: 'badge-gray' };
  const info = PRIORITY_LABELS[priority];
  return { label: info.label, className: info.color };
}

export function getConfidenceBadge(confidence: ConfidenceLevel | string | undefined): { label: string; className: string } {
  if (!confidence || !(confidence in CONFIDENCE_LABELS)) return { label: '-', className: 'badge-gray' };
  const info = CONFIDENCE_LABELS[confidence as ConfidenceLevel];
  return { label: info.label, className: info.color };
}
