export interface Profile {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  location: string;
  remote_preference: 'remote' | 'hybrid' | 'on_site';
  experience_level: 'entry' | 'mid' | 'senior' | 'lead';
  desired_roles: string[];
  skills: string[];
  min_salary_eur?: number;
  max_salary_eur?: number;
  currency: string;
  notice_period_weeks?: number;
  work_authorization: string[];
  preferred_industries: string[];
  excluded_keywords: string[];
  excluded_companies: string[];
  search_radius_km?: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreate {
  full_name: string;
  email: string;
  phone?: string;
  location: string;
  remote_preference: 'remote' | 'hybrid' | 'on_site';
  experience_level: 'entry' | 'mid' | 'senior' | 'lead';
  desired_roles: string[];
  skills: string[];
  min_salary_eur?: number;
  max_salary_eur?: number;
  currency?: string;
  notice_period_weeks?: number;
  work_authorization?: string[];
  preferred_industries?: string[];
  excluded_keywords?: string[];
  excluded_companies?: string[];
  search_radius_km?: number;
}

export interface ProfileUpdate {
  full_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  remote_preference?: 'remote' | 'hybrid' | 'on_site';
  experience_level?: 'entry' | 'mid' | 'senior' | 'lead';
  desired_roles?: string[];
  skills?: string[];
  min_salary_eur?: number;
  max_salary_eur?: number;
  currency?: string;
  notice_period_weeks?: number;
  work_authorization?: string[];
  preferred_industries?: string[];
  excluded_keywords?: string[];
  excluded_companies?: string[];
  search_radius_km?: number;
}

export interface Job {
  id: number;
  adzuna_id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  salary_is_predicted: string;
  contract_type?: string;
  working_hours?: string;
  category?: string;
  redirect_url: string;
  created: string;
  latitude?: number;
  longitude?: number;
  passed_prefilter?: boolean;
  prefilter_reasons?: string[];
  ai_score?: number;
  ai_recommendation?: string;
  ai_confidence?: string;
  ai_explanation?: string;
  ai_evidence?: EvidenceItem[];
  ai_matched_skills?: string[];
  ai_missing_skills?: string[];
  ai_matched_experience?: string[];
  ai_missing_experience?: string[];
  ai_missing_requirements?: RequirementGap[];
  recommendation_category?: 'strong_match' | 'possible_match' | 'weak_match' | 'not_enough_info';
  recommendation_priority?: 'high' | 'medium' | 'low';
  recommendation_primary_reason?: string;
  recommendation_secondary_reasons?: string[];
  recommendation_explanation?: string;
  recommendation_missing_skills?: string[];
  recommendation_strengths?: string[];
  recommendation_concerns?: string[];
  recommendation_action_items?: string[];
  recommended_at?: string;
  recommendation_model?: string;
}

export interface JobListItem {
  id: number;
  adzuna_id: string;
  title: string;
  company: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  salary_is_predicted: string;
  redirect_url: string;
  created: string;
  passed_prefilter?: boolean;
  prefilter_reasons?: string[];
  ai_score?: number;
  ai_recommendation?: string;
  ai_confidence?: string;
  recommendation_category?: 'strong_match' | 'possible_match' | 'weak_match' | 'not_enough_info';
  recommendation_priority?: 'high' | 'medium' | 'low';
  recommendation_primary_reason?: string;
  recommended_at?: string;
}

export interface EvidenceItem {
  type: 'skill_match' | 'experience_match' | 'requirement_gap' | 'location_match' | 'salary_match';
  field: string;
  job_value: string;
  profile_value: string;
  match: boolean;
  confidence: number;
}

export interface RequirementGap {
  requirement: string;
  category: 'skill' | 'experience' | 'certification' | 'education' | 'other';
  severity: 'critical' | 'nice_to_have';
  profile_has: boolean;
  notes?: string;
}

export interface SearchRequest {
  profile_id?: number;
  what?: string;
  where?: string;
  salary_min?: number;
  max_pages?: number;
  results_per_page?: number;
}

export interface SearchResponse {
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  quota_remaining?: number;
  quota_reset?: string;
}

export interface AnalysisRunRequest {
  job_ids?: number[];
  limit?: number;
}

export interface AnalysisRunResponse {
  analyzed: number;
  failed: number;
  errors: string[];
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

export type RecommendationCategory = 'strong_match' | 'possible_match' | 'weak_match' | 'not_enough_info';
export type RecommendationPriority = 'high' | 'medium' | 'low';
export type ConfidenceLevel = 'high' | 'medium' | 'low';

export const RECOMMENDATION_LABELS: Record<RecommendationCategory, { label: string; color: string }> = {
  strong_match: { label: 'Strong Match', color: 'badge-success' },
  possible_match: { label: 'Possible Match', color: 'badge-info' },
  weak_match: { label: 'Weak Match', color: 'badge-warning' },
  not_enough_info: { label: 'Not Enough Info', color: 'badge-gray' },
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

export function formatSalary(min?: number, max?: number, currency = 'EUR', isPredicted = '0'): string {
  const pred = isPredicted === '1' ? ' (est.)' : '';
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

export function getConfidenceBadge(confidence: ConfidenceLevel | undefined): { label: string; className: string } {
  if (!confidence) return { label: '-', className: 'badge-gray' };
  const info = CONFIDENCE_LABELS[confidence];
  return { label: info.label, className: info.color };
}