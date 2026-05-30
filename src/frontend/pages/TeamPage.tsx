/**
 * Team management page (ADMIN-001).
 *
 * Displays current team members, roles, and provides controls for
 * inviting new members, changing roles, and removing members.
 * Owner/admin-only actions are gated by the user's role.
 */

import React, { useEffect, useState } from "react";

interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: string;
  invited_at: string | null;
  joined_at: string | null;
}

interface TeamPageProps {
  teamId: string;
  currentUserId: string;
  currentUserRole: string;
}

const API_BASE = "/api/v1";

async function fetchMembers(teamId: string): Promise<TeamMember[]> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/members`);
  if (!res.ok) {
    throw new Error("Failed to fetch members");
  }
  const data: { members: TeamMember[] } = await res.json();
  return data.members;
}

async function sendInvite(
  teamId: string,
  email: string,
  role: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/invitations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, role }),
  });
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
}

async function changeRole(
  teamId: string,
  userId: string,
  role: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/teams/${teamId}/members/${userId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    }
  );
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
}

async function removeMember(
  teamId: string,
  userId: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/teams/${teamId}/members/${userId}`,
    { method: "DELETE" }
  );
  if (!res.ok) {
    throw new Error("Failed to remove member");
  }
}

function canManageMembers(role: string): boolean {
  return role === "owner" || role === "admin";
}

const TeamPage: React.FC<TeamPageProps> = ({
  teamId,
  currentUserId,
  currentUserRole,
}) => {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [error, setError] = useState<string | null>(null);

  const loadMembers = (): void => {
    fetchMembers(teamId)
      .then(setMembers)
      .catch((e: Error) => setError(e.message));
  };

  useEffect(() => {
    loadMembers();
  }, [teamId]);

  const handleInvite = (): void => {
    if (!inviteEmail.trim()) return;
    setError(null);
    sendInvite(teamId, inviteEmail, inviteRole)
      .then(() => {
        setInviteEmail("");
        loadMembers();
      })
      .catch((e: Error) => setError(e.message));
  };

  const handleRoleChange = (userId: string, newRole: string): void => {
    setError(null);
    changeRole(teamId, userId, newRole)
      .then(loadMembers)
      .catch((e: Error) => setError(e.message));
  };

  const handleRemove = (userId: string): void => {
    setError(null);
    removeMember(teamId, userId)
      .then(loadMembers)
      .catch((e: Error) => setError(e.message));
  };

  const isManager = canManageMembers(currentUserRole);

  return (
    <div className="team-page">
      <h1>Team Members</h1>

      {error && <div className="error-banner">{error}</div>}

      <table className="members-table">
        <thead>
          <tr>
            <th>User ID</th>
            <th>Role</th>
            <th>Joined</th>
            {isManager && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {members.map((m) => (
            <tr key={m.id}>
              <td>{m.user_id}</td>
              <td>{m.role}</td>
              <td>{m.joined_at ?? "Pending"}</td>
              {isManager && (
                <td>
                  {m.role !== "owner" && (
                    <>
                      <select
                        value={m.role}
                        onChange={(e) =>
                          handleRoleChange(m.user_id, e.target.value)
                        }
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                      </select>
                      <button
                        onClick={() => handleRemove(m.user_id)}
                        className="remove-btn"
                      >
                        Remove
                      </button>
                    </>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {isManager && (
        <div className="invite-form">
          <h2>Invite Member</h2>
          <input
            type="email"
            placeholder="Email address"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <button onClick={handleInvite}>Send Invite</button>
        </div>
      )}
    </div>
  );
};

export default TeamPage;
