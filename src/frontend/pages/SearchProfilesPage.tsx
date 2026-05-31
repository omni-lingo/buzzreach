/**
 * Search profiles management page (FEAT-004).
 *
 * Displays user's search profiles with controls to create, edit,
 * enable/disable, schedule, copy, and delete profiles.
 */

import React, { useEffect, useState } from "react";

import {
  createProfile,
  deleteProfile,
  fetchProfiles,
  parseKeywords,
  setSchedule,
  updateProfile,
} from "./searchProfilesApi";
import type { SearchProfile } from "./searchProfilesApi";

const FREQUENCIES = ["hourly", "daily", "weekly"] as const;

const SearchProfilesPage: React.FC = () => {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [scheduleId, setScheduleId] = useState<string | null>(null);
  const [formName, setFormName] = useState("");
  const [formKeywords, setFormKeywords] = useState("");
  const [formPlatforms, setFormPlatforms] = useState("");
  const [formLanguages, setFormLanguages] = useState("");
  const [schedTimes, setSchedTimes] = useState("");
  const [schedFreq, setSchedFreq] = useState<string>("daily");

  const loadProfiles = (): void => {
    fetchProfiles()
      .then(setProfiles)
      .catch((e: Error) => setError(e.message));
  };

  useEffect(() => { loadProfiles(); }, []);

  const resetForm = (): void => {
    setFormName("");
    setFormKeywords("");
    setFormPlatforms("");
    setFormLanguages("");
    setShowForm(false);
  };

  const handleCreate = (): void => {
    setError(null);
    const keywords = parseKeywords(formKeywords);
    if (keywords.length === 0) {
      setError("At least one keyword is required");
      return;
    }
    createProfile({
      name: formName,
      keywords,
      platforms: parseKeywords(formPlatforms),
      languages: parseKeywords(formLanguages),
      enabled: true,
    })
      .then(() => { resetForm(); loadProfiles(); })
      .catch((e: Error) => setError(e.message));
  };

  const handleCopy = (profile: SearchProfile): void => {
    setError(null);
    createProfile({
      name: `${profile.name} (copy)`,
      keywords: profile.keywords,
      platforms: profile.platforms,
      languages: profile.languages,
      enabled: true,
      copy_from: profile.id,
    })
      .then(loadProfiles)
      .catch((e: Error) => setError(e.message));
  };

  const handleToggle = (id: string, enabled: boolean): void => {
    updateProfile(id, { enabled: !enabled })
      .then(loadProfiles)
      .catch((e: Error) => setError(e.message));
  };

  const handleDelete = (id: string): void => {
    deleteProfile(id)
      .then(() => { setDeleteConfirm(null); loadProfiles(); })
      .catch((e: Error) => setError(e.message));
  };

  const handleSchedule = (id: string): void => {
    setError(null);
    const times = parseKeywords(schedTimes);
    if (times.length === 0) {
      setError("At least one time is required (HH:MM format)");
      return;
    }
    setSchedule(id, { times, frequency: schedFreq })
      .then(() => { setScheduleId(null); setSchedTimes(""); loadProfiles(); })
      .catch((e: Error) => setError(e.message));
  };

  return (
    <div className="search-profiles-page">
      <h1>Search Profiles</h1>
      <p>Manage your search configurations and schedules.</p>
      {error && <div className="error-banner">{error}</div>}
      <button onClick={() => setShowForm(!showForm)} className="new-profile-btn">
        {showForm ? "Cancel" : "New Profile"}
      </button>
      {showForm && (
        <div className="new-profile-form">
          <h2>Create New Profile</h2>
          <label>
            Name
            <input type="text" value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder='e.g., "IRS Tax" or "Parking Appeals"' />
          </label>
          <label>
            Keywords (one per line)
            <textarea value={formKeywords}
              onChange={(e) => setFormKeywords(e.target.value)}
              placeholder={"tax penalty\nIRS notice\ntax relief"} rows={3} />
          </label>
          <label>
            Platforms (one per line, optional)
            <textarea value={formPlatforms}
              onChange={(e) => setFormPlatforms(e.target.value)}
              placeholder={"reddit\nquora"} rows={2} />
          </label>
          <label>
            Languages (one per line, optional)
            <textarea value={formLanguages}
              onChange={(e) => setFormLanguages(e.target.value)}
              placeholder="en" rows={1} />
          </label>
          <button onClick={handleCreate} className="create-btn">Create Profile</button>
        </div>
      )}
      <ProfileTable
        profiles={profiles} deleteConfirm={deleteConfirm}
        scheduleId={scheduleId} schedTimes={schedTimes} schedFreq={schedFreq}
        onToggle={handleToggle} onCopy={handleCopy}
        onDeleteRequest={(id) => setDeleteConfirm(id)}
        onDeleteConfirm={handleDelete}
        onDeleteCancel={() => setDeleteConfirm(null)}
        onScheduleOpen={(id) => setScheduleId(id)}
        onScheduleSubmit={handleSchedule}
        setSchedTimes={setSchedTimes} setSchedFreq={setSchedFreq}
      />
      {profiles.length === 0 && (
        <p className="empty-state">
          No search profiles yet. Click &quot;New Profile&quot; to create one.
        </p>
      )}
    </div>
  );
};

interface ProfileTableProps {
  profiles: SearchProfile[];
  deleteConfirm: string | null;
  scheduleId: string | null;
  schedTimes: string;
  schedFreq: string;
  onToggle: (id: string, enabled: boolean) => void;
  onCopy: (profile: SearchProfile) => void;
  onDeleteRequest: (id: string) => void;
  onDeleteConfirm: (id: string) => void;
  onDeleteCancel: () => void;
  onScheduleOpen: (id: string) => void;
  onScheduleSubmit: (id: string) => void;
  setSchedTimes: (v: string) => void;
  setSchedFreq: (v: string) => void;
}

const ProfileTable: React.FC<ProfileTableProps> = (props) => (
  <table className="profiles-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Keywords</th>
        <th>Schedule</th>
        <th>Enabled</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {props.profiles.map((p) => (
        <React.Fragment key={p.id}>
          <tr>
            <td>{p.name}</td>
            <td>{p.keywords.join(", ")}</td>
            <td>
              {p.schedule_times.length > 0
                ? `${p.schedule_frequency} @ ${p.schedule_times.join(", ")}`
                : "Not scheduled"}
            </td>
            <td>
              <button onClick={() => props.onToggle(p.id, p.enabled)}
                className={p.enabled ? "toggle-on" : "toggle-off"}>
                {p.enabled ? "On" : "Off"}
              </button>
            </td>
            <td>
              <button onClick={() => props.onScheduleOpen(p.id)}>Schedule</button>
              <button onClick={() => props.onCopy(p)}>Copy</button>
              <button onClick={() => props.onDeleteRequest(p.id)} className="remove-btn">
                Delete
              </button>
            </td>
          </tr>
          {props.deleteConfirm === p.id && (
            <tr className="confirm-row">
              <td colSpan={5}>
                Delete &quot;{p.name}&quot;?{" "}
                <button onClick={() => props.onDeleteConfirm(p.id)}>Yes, delete</button>
                <button onClick={props.onDeleteCancel}>Cancel</button>
              </td>
            </tr>
          )}
          {props.scheduleId === p.id && (
            <tr className="schedule-row">
              <td colSpan={5}>
                <label>
                  Times (HH:MM, one per line)
                  <textarea value={props.schedTimes}
                    onChange={(e) => props.setSchedTimes(e.target.value)}
                    placeholder={"06:00\n14:00"} rows={2} />
                </label>
                <label>
                  Frequency
                  <select value={props.schedFreq}
                    onChange={(e) => props.setSchedFreq(e.target.value)}>
                    {FREQUENCIES.map((f) => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </label>
                <button onClick={() => props.onScheduleSubmit(p.id)}>
                  Save Schedule
                </button>
              </td>
            </tr>
          )}
        </React.Fragment>
      ))}
    </tbody>
  </table>
);

export default SearchProfilesPage;
