/**
 * Filters management page (FEAT-002).
 *
 * Displays the user's filter rules with controls to create, enable/disable,
 * delete, and test rules against sample opportunities.
 */

import React, { useEffect, useState } from "react";

import {
  createRule,
  deleteRule,
  fetchRules,
  parsePatternInput,
  testRule,
  toggleRule,
} from "./filtersApi";
import type { FilterRule, TestResult } from "./filtersApi";

const RULE_TYPES = ["regex", "not", "field", "composite"] as const;

const FiltersPage: React.FC = () => {
  const [rules, setRules] = useState<FilterRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<string>("regex");
  const [newPattern, setNewPattern] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [testResults, setTestResults] = useState<
    Record<string, TestResult>
  >({});

  const loadRules = (): void => {
    fetchRules()
      .then(setRules)
      .catch((e: Error) => setError(e.message));
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleCreate = (): void => {
    setError(null);
    let patterns: Record<string, unknown>;
    try {
      patterns = parsePatternInput(newType, newPattern);
    } catch {
      setError("Invalid pattern format");
      return;
    }
    createRule(newName, newType, patterns, newDesc)
      .then(() => {
        setNewName("");
        setNewPattern("");
        setNewDesc("");
        setShowForm(false);
        loadRules();
      })
      .catch((e: Error) => setError(e.message));
  };

  const handleToggle = (ruleId: string, enabled: boolean): void => {
    setError(null);
    toggleRule(ruleId, !enabled)
      .then(loadRules)
      .catch((e: Error) => setError(e.message));
  };

  const handleDelete = (ruleId: string): void => {
    setError(null);
    deleteRule(ruleId)
      .then(loadRules)
      .catch((e: Error) => setError(e.message));
  };

  const handleTest = (ruleId: string): void => {
    setError(null);
    testRule(ruleId)
      .then((result) => {
        setTestResults((prev) => ({ ...prev, [ruleId]: result }));
      })
      .catch((e: Error) => setError(e.message));
  };

  const patternPlaceholder =
    newType === "regex"
      ? "One regex per line, e.g.:\nreddit\\.com/r/spam\nFREE\\s+MONEY"
      : newType === "not"
        ? "One keyword per line, e.g.:\nhiring\nfreelance"
        : '{"min_score": 0.5, "platforms": ["reddit"]}';

  return (
    <div className="filters-page">
      <h1>Filter Rules</h1>
      <p>
        Create rules to automatically filter out irrelevant
        opportunities.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <button
        onClick={() => setShowForm(!showForm)}
        className="new-rule-btn"
      >
        {showForm ? "Cancel" : "New Rule"}
      </button>

      {showForm && (
        <NewRuleForm
          newName={newName}
          setNewName={setNewName}
          newType={newType}
          setNewType={setNewType}
          newPattern={newPattern}
          setNewPattern={setNewPattern}
          newDesc={newDesc}
          setNewDesc={setNewDesc}
          patternPlaceholder={patternPlaceholder}
          onCreate={handleCreate}
        />
      )}

      <RuleTable
        rules={rules}
        testResults={testResults}
        onToggle={handleToggle}
        onDelete={handleDelete}
        onTest={handleTest}
      />

      {rules.length === 0 && (
        <p className="empty-state">
          No filter rules yet. Click &quot;New Rule&quot; to create one.
        </p>
      )}
    </div>
  );
};

interface NewRuleFormProps {
  newName: string;
  setNewName: (v: string) => void;
  newType: string;
  setNewType: (v: string) => void;
  newPattern: string;
  setNewPattern: (v: string) => void;
  newDesc: string;
  setNewDesc: (v: string) => void;
  patternPlaceholder: string;
  onCreate: () => void;
}

const NewRuleForm: React.FC<NewRuleFormProps> = ({
  newName,
  setNewName,
  newType,
  setNewType,
  newPattern,
  setNewPattern,
  newDesc,
  setNewDesc,
  patternPlaceholder,
  onCreate,
}) => (
  <div className="new-rule-form">
    <h2>Create New Rule</h2>
    <label>
      Name
      <input
        type="text"
        value={newName}
        onChange={(e) => setNewName(e.target.value)}
        placeholder="e.g., Block spam subreddits"
      />
    </label>
    <label>
      Type
      <select
        value={newType}
        onChange={(e) => setNewType(e.target.value)}
      >
        {RULE_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </label>
    <label>
      Pattern
      <textarea
        value={newPattern}
        onChange={(e) => setNewPattern(e.target.value)}
        placeholder={patternPlaceholder}
        rows={4}
      />
    </label>
    <label>
      Description
      <input
        type="text"
        value={newDesc}
        onChange={(e) => setNewDesc(e.target.value)}
        placeholder="Optional description"
      />
    </label>
    <button onClick={onCreate} className="create-btn">
      Create Rule
    </button>
  </div>
);

interface RuleTableProps {
  rules: FilterRule[];
  testResults: Record<string, TestResult>;
  onToggle: (id: string, enabled: boolean) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
}

const RuleTable: React.FC<RuleTableProps> = ({
  rules,
  testResults,
  onToggle,
  onDelete,
  onTest,
}) => (
  <table className="rules-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Enabled</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {rules.map((rule) => (
        <React.Fragment key={rule.id}>
          <tr>
            <td title={rule.description}>{rule.name}</td>
            <td>{rule.rule_type}</td>
            <td>
              <button
                onClick={() => onToggle(rule.id, rule.enabled)}
                className={rule.enabled ? "toggle-on" : "toggle-off"}
              >
                {rule.enabled ? "On" : "Off"}
              </button>
            </td>
            <td>
              <button onClick={() => onTest(rule.id)}>Test</button>
              <button
                onClick={() => onDelete(rule.id)}
                className="remove-btn"
              >
                Delete
              </button>
            </td>
          </tr>
          {testResults[rule.id] && (
            <tr className="test-result-row">
              <td colSpan={4}>
                <div className="test-result">
                  <strong>Test Results:</strong>{" "}
                  {testResults[rule.id].matched} passed,{" "}
                  {testResults[rule.id].rejected} rejected out of{" "}
                  {testResults[rule.id].total}
                  {testResults[rule.id].sample_rejected.length > 0 && (
                    <ul>
                      {testResults[rule.id].sample_rejected.map(
                        (s, i) => (
                          <li key={i}>
                            {s.title} ({s.url})
                          </li>
                        )
                      )}
                    </ul>
                  )}
                </div>
              </td>
            </tr>
          )}
        </React.Fragment>
      ))}
    </tbody>
  </table>
);

export default FiltersPage;
