import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api/client';
import type { Profile, ProfileCreate, ProfileUpdate } from '../types';
import { LoadingOverlay } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Tag } from '../components/Badge';

export function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [editMode, setEditMode] = useState(false);

  const [formData, setFormData] = useState<ProfileCreate | ProfileUpdate>({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    remote_preference: 'hybrid',
    experience_level: 'mid',
    desired_roles: [],
    skills: [],
    min_salary_eur: undefined,
    max_salary_eur: undefined,
    currency: 'EUR',
    notice_period_weeks: undefined,
    work_authorization: [],
    preferred_industries: [],
    excluded_keywords: [],
    excluded_companies: [],
    search_radius_km: undefined,
  });

  const [newSkill, setNewSkill] = useState('');
  const [newRole, setNewRole] = useState('');
  const [newAuth, setNewAuth] = useState('');
  const [newIndustry, setNewIndustry] = useState('');
  const [newExcludedKeyword, setNewExcludedKeyword] = useState('');
  const [newExcludedCompany, setNewExcludedCompany] = useState('');

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
        full_name: data.full_name,
        email: data.email,
        phone: data.phone || '',
        location: data.location,
        remote_preference: data.remote_preference,
        experience_level: data.experience_level,
        desired_roles: [...data.desired_roles],
        skills: [...data.skills],
        min_salary_eur: data.min_salary_eur,
        max_salary_eur: data.max_salary_eur,
        currency: data.currency,
        notice_period_weeks: data.notice_period_weeks,
        work_authorization: [...data.work_authorization],
        preferred_industries: [...data.preferred_industries],
        excluded_keywords: [...data.excluded_keywords],
        excluded_companies: [...data.excluded_companies],
        search_radius_km: data.search_radius_km,
      });
    } catch {
      // Profile doesn't exist yet
    } finally {
      setLoading(false);
    }
  }

  function handleChange<K extends keyof ProfileCreate>(field: K, value: ProfileCreate[K]) {
    setFormData(prev => ({ ...prev, [field]: value }));
  }

  function addToArray(field: keyof ProfileCreate, value: string) {
    if (!value.trim()) return;
    const current = formData[field] as string[];
    if (current.includes(value.trim())) return;
    setFormData(prev => ({ ...prev, [field]: [...current, value.trim()] }));
  }

  function removeFromArray(field: keyof ProfileCreate, value: string) {
    const current = formData[field] as string[];
    setFormData(prev => ({ ...prev, [field]: current.filter(v => v !== value) }));
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      if (profile) {
        await api.profile.update(formData as ProfileUpdate);
      } else {
        await api.profile.create(formData as ProfileCreate);
      }
      setSuccess(true);
      setEditMode(false);
      await loadProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <LoadingOverlay message="Loading profile..." />;
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Profile & Preferences</h1>
        <button
          onClick={() => setEditMode(!editMode)}
          className={editMode ? 'btn-secondary' : 'btn-primary'}
        >
          {editMode ? 'Cancel' : 'Edit Profile'}
        </button>
      </div>

      {error && <ErrorMessage message={error} onRetry={() => handleSubmit(new Event('submit') as unknown as FormEvent<HTMLFormElement>)} />}
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          Profile saved successfully!
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Full Name</label>
              <input
                type="text"
                value={formData.full_name}
                onChange={e => handleChange('full_name', e.target.value)}
                className="input"
                required
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={e => handleChange('email', e.target.value)}
                className="input"
                required
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={e => handleChange('phone', e.target.value)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={e => handleChange('location', e.target.value)}
                className="input"
                required
                disabled={!editMode}
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
                onChange={e => handleChange('remote_preference', e.target.value as any)}
                className="input"
                disabled={!editMode}
              >
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="on_site">On-site</option>
              </select>
            </div>
            <div>
              <label className="label">Experience Level</label>
              <select
                value={formData.experience_level}
                onChange={e => handleChange('experience_level', e.target.value as any)}
                className="input"
                disabled={!editMode}
              >
                <option value="entry">Entry</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
              </select>
            </div>
            <div>
              <label className="label">Min Salary (EUR)</label>
              <input
                type="number"
                value={formData.min_salary_eur || ''}
                onChange={e => handleChange('min_salary_eur', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Max Salary (EUR)</label>
              <input
                type="number"
                value={formData.max_salary_eur || ''}
                onChange={e => handleChange('max_salary_eur', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Notice Period (weeks)</label>
              <input
                type="number"
                value={formData.notice_period_weeks || ''}
                onChange={e => handleChange('notice_period_weeks', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
            <div>
              <label className="label">Search Radius (km)</label>
              <input
                type="number"
                value={formData.search_radius_km || ''}
                onChange={e => handleChange('search_radius_km', e.target.value ? parseInt(e.target.value) : undefined)}
                className="input"
                disabled={!editMode}
              />
            </div>
          </div>
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Desired Roles</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.desired_roles?.map((role, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('desired_roles', role)}>
                {role}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newRole}
                onChange={e => setNewRole(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('desired_roles', newRole); setNewRole(''); }}}
                className="input flex-1"
                placeholder="Add role (e.g., Security Engineer)"
              />
              <button
                type="button"
                onClick={() => { addToArray('desired_roles', newRole); setNewRole(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Skills</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.skills?.map((skill, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('skills', skill)}>
                {skill}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newSkill}
                onChange={e => setNewSkill(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('skills', newSkill); setNewSkill(''); }}}
                className="input flex-1"
                placeholder="Add skill (e.g., Python, AWS, Kubernetes)"
              />
              <button
                type="button"
                onClick={() => { addToArray('skills', newSkill); setNewSkill(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Work Authorization</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.work_authorization?.map((auth, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('work_authorization', auth)}>
                {auth}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newAuth}
                onChange={e => setNewAuth(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('work_authorization', newAuth); setNewAuth(''); }}}
                className="input flex-1"
                placeholder="Add authorization (e.g., EU Citizen, Blue Card)"
              />
              <button
                type="button"
                onClick={() => { addToArray('work_authorization', newAuth); setNewAuth(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Preferred Industries</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.preferred_industries?.map((ind, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('preferred_industries', ind)}>
                {ind}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newIndustry}
                onChange={e => setNewIndustry(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('preferred_industries', newIndustry); setNewIndustry(''); }}}
                className="input flex-1"
                placeholder="Add industry (e.g., Cybersecurity, Fintech)"
              />
              <button
                type="button"
                onClick={() => { addToArray('preferred_industries', newIndustry); setNewIndustry(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Excluded Keywords</h2>
          <p className="text-sm text-gray-600 mb-3">Jobs containing these keywords in title/description will be filtered out</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.excluded_keywords?.map((kw, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('excluded_keywords', kw)} variant="error">
                {kw}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newExcludedKeyword}
                onChange={e => setNewExcludedKeyword(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('excluded_keywords', newExcludedKeyword); setNewExcludedKeyword(''); }}}
                className="input flex-1"
                placeholder="Add keyword (e.g., intern, student, senior)"
              />
              <button
                type="button"
                onClick={() => { addToArray('excluded_keywords', newExcludedKeyword); setNewExcludedKeyword(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Excluded Companies</h2>
          <div className="flex flex-wrap gap-2 mb-3">
            {formData.excluded_companies?.map((comp, i) => (
              <Tag key={i} removable onRemove={() => removeFromArray('excluded_companies', comp)} variant="error">
                {comp}
              </Tag>
            ))}
          </div>
          {editMode && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newExcludedCompany}
                onChange={e => setNewExcludedCompany(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addToArray('excluded_companies', newExcludedCompany); setNewExcludedCompany(''); }}}
                className="input flex-1"
                placeholder="Add company name"
              />
              <button
                type="button"
                onClick={() => { addToArray('excluded_companies', newExcludedCompany); setNewExcludedCompany(''); }}
                className="btn-secondary"
              >
                Add
              </button>
            </div>
          )}
        </section>

        {editMode && (
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button type="button" onClick={() => setEditMode(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}