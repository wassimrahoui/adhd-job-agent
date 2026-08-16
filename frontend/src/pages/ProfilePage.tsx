import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api/client';
import type { Profile, ProfileInput } from '../types';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Tag } from '../components/Badge';
import { useToast } from '../components/Toast';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

const EMPTY_FORM: ProfileInput = {
  work_experience: '',
  technical_skills: [],
  networking_experience: '',
  education: '',
  certifications: [],
  languages: [],
  desired_roles: [],
  location_preferences: [],
  salary_min: undefined,
  salary_max: undefined,
  salary_currency: 'EUR',
  remote_preference: 'any',
  experience_level: 'any',
  excluded_keywords: [],
  relevance_threshold: 50,
  resume_text: '',
  resume_file_path: '',
};

type ListField =
  | 'technical_skills'
  | 'certifications'
  | 'languages'
  | 'desired_roles'
  | 'location_preferences'
  | 'excluded_keywords';

export function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [formData, setFormData] = useState<ProfileInput>(EMPTY_FORM);
  const [newInputs, setNewInputs] = useState<Record<ListField, string>>({
    technical_skills: '',
    certifications: '',
    languages: '',
    desired_roles: '',
    location_preferences: '',
    excluded_keywords: '',
  });

  const { showToast } = useToast();

  useKeyboardShortcuts([
    { key: 's', ctrlKey: true, action: () => { if (editMode && !saving) document.querySelector('form')?.requestSubmit(); }, description: 'Save profile', global: false },
    { key: 'Escape', action: () => { if (editMode) setEditMode(false); }, description: 'Cancel edit mode', global: false },
    { key: 'e', ctrlKey: true, action: () => { if (profile) setEditMode(true); }, description: 'Enter edit mode', global: false },
  ], editMode);

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.profile.get();
      setProfile(data);
      setFormData({
        work_experience: data.work_experience || '',
        technical_skills: [...data.technical_skills],
        networking_experience: data.networking_experience || '',
        education: data.education || '',
        certifications: [...data.certifications],
        languages: [...data.languages],
        desired_roles: [...data.desired_roles],
        location_preferences: [...data.location_preferences],
        salary_min: data.salary_min,
        salary_max: data.salary_max,
        salary_currency: data.salary_currency,
        remote_preference: data.remote_preference,
        experience_level: data.experience_level,
        excluded_keywords: [...data.excluded_keywords],
        relevance_threshold: data.relevance_threshold,
        resume_text: data.resume_text || '',
        resume_file_path: data.resume_file_path || '',
      });
      setEditMode(false);
    } catch {
      setProfile(null);
      setFormData(EMPTY_FORM);
      setEditMode(true);
    } finally {
      setLoading(false);
    }
  }

  function handleChange<K extends keyof ProfileInput>(field: K, value: ProfileInput[K]) {
    setFormData(prev => ({ ...prev, [field]: value }));
  }

  function addToArray(field: ListField, value: string) {
    if (!value.trim()) return;
    const current = formData[field] as string[];
    if (current.includes(value.trim())) return;
    setFormData(prev => ({ ...prev, [field]: [...current, value.trim()] }));
    setNewInputs(prev => ({ ...prev, [field]: '' }));
  }

  function removeFromArray(field: ListField, value: string) {
    const current = formData[field] as string[];
    setFormData(prev => ({ ...prev, [field]: current.filter(v => v !== value) }));
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.profile.upsert(formData);
      showToast('success', 'Profile saved successfully!');
      await loadProfile();
      setEditMode(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save profile';
      setError(message);
      showToast('error', message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <LoadingOverlay message="Loading profile..." />;
  }

  function renderListField(field: ListField, label: string, placeholder: string, variant?: 'error') {
    return (
      <section className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{label}</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {(formData[field] as string[]).map((value, i) => (
            <Tag key={i} removable={editMode} onRemove={() => removeFromArray(field, value)} variant={variant}>
              {value}
            </Tag>
          ))}
        </div>
        {editMode && (
          <div className="flex gap-2">
            <input
              type="text"
              value={newInputs[field]}
              onChange={e => setNewInputs(prev => ({ ...prev, [field]: e.target.value }))}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addToArray(field, newInputs[field]);
                }
              }}
              className="input flex-1"
              placeholder={placeholder}
            />
            <button type="button" onClick={() => addToArray(field, newInputs[field])} className="btn-secondary">
              Add
            </button>
          </div>
        )}
      </section>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Profile & Preferences</h1>
        {profile && (
          <button
            onClick={() => setEditMode(!editMode)}
            className={editMode ? 'btn-secondary' : 'btn-primary'}
          >
            {editMode ? 'Cancel' : 'Edit Profile'}
          </button>
        )}
      </div>

      {!profile && (
        <p className="text-gray-600 mb-4">No profile yet — fill this in to start searching for jobs.</p>
      )}

      {error && <ErrorMessage message={error} onRetry={loadProfile} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Background</h2>
          <div className="space-y-4">
            <div>
              <label className="label">Work Experience Summary</label>
              <textarea
                value={formData.work_experience}
                onChange={e => handleChange('work_experience', e.target.value)}
                className="input"
                rows={4}
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Networking / Cybersecurity / Sysadmin Experience</label>
              <textarea
                value={formData.networking_experience}
                onChange={e => handleChange('networking_experience', e.target.value)}
                className="input"
                rows={3}
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Education</label>
              <textarea
                value={formData.education}
                onChange={e => handleChange('education', e.target.value)}
                className="input"
                rows={2}
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Resume Text</label>
              <textarea
                value={formData.resume_text}
                onChange={e => handleChange('resume_text', e.target.value)}
                className="input"
                rows={6}
                disabled={!editMode}
                placeholder="Paste your resume text here for AI analysis"
              />
            </div>
          </div>
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Work Preferences</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Remote Preference</label>
              <select
                value={formData.remote_preference}
                onChange={e => handleChange('remote_preference', e.target.value as ProfileInput['remote_preference'])}
                className="input"
                disabled={!editMode}
              >
                <option value="any">Any</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="on_site">On-site</option>
              </select>
            </div>
            <div>
              <label className="label">Experience Level</label>
              <select
                value={formData.experience_level}
                onChange={e => handleChange('experience_level', e.target.value as ProfileInput['experience_level'])}
                className="input"
                disabled={!editMode}
              >
                <option value="any">Any</option>
                <option value="entry">Entry</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="principal">Principal</option>
              </select>
            </div>
            <div>
              <label className="label">Min Salary</label>
              <input
                type="number"
                value={formData.salary_min ?? ''}
                onChange={e => handleChange('salary_min', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Max Salary</label>
              <input
                type="number"
                value={formData.salary_max ?? ''}
                onChange={e => handleChange('salary_max', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Currency</label>
              <input
                type="text"
                value={formData.salary_currency}
                onChange={e => handleChange('salary_currency', e.target.value)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Relevance Threshold ({formData.relevance_threshold}%)</label>
              <input
                type="range"
                min={0}
                max={100}
                value={formData.relevance_threshold}
                onChange={e => handleChange('relevance_threshold', parseInt(e.target.value))}
                className="w-full"
                disabled={!editMode}
              />
            </div>
          </div>
        </section>

        {renderListField('desired_roles', 'Desired Roles', 'Add role (e.g., Security Engineer)')}
        {renderListField('technical_skills', 'Technical Skills', 'Add skill (e.g., Python, AWS, Kubernetes)')}
        {renderListField('certifications', 'Certifications', 'Add certification (e.g., CompTIA Security+)')}
        {renderListField('languages', 'Languages', 'Add language (e.g., German, English)')}
        {renderListField('location_preferences', 'Preferred Locations', 'Add location (e.g., Munich, Remote Germany)')}
        {renderListField('excluded_keywords', 'Excluded Keywords', 'Add keyword (e.g., intern, student, senior)', 'error')}

        {editMode && (
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            {profile && (
              <button type="button" onClick={() => setEditMode(false)} className="btn-secondary">
                Cancel
              </button>
            )}
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
