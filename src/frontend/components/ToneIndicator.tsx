/**
 * Tone quality indicator with metric gauges and warnings (FEAT-005).
 *
 * Displays reading level, marketing score, AI likelihood, and
 * authenticity score as progress bars. Shows warning icons with
 * actionable suggestions when metrics exceed thresholds.
 *
 * Integrated into the draft editor (FEAT-001) for real-time feedback.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";

interface ToneWarning {
  code: string;
  message: string;
  suggestion: string;
}

interface ToneMetrics {
  reading_level: number;
  marketing_score: number;
  ai_likelihood: number;
  authenticity_score: number;
  warnings: ToneWarning[];
}

interface ToneIndicatorProps {
  draftText: string;
  debounceMs?: number;
}

const API_BASE = "/api/v1";

async function fetchToneAnalysis(text: string): Promise<ToneMetrics> {
  const res = await fetch(`${API_BASE}/tone/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err: { detail: { message: string } } = await res.json();
    throw new Error(err.detail.message);
  }
  return res.json();
}

const ToneIndicator: React.FC<ToneIndicatorProps> = ({
  draftText,
  debounceMs = 300,
}) => {
  const [metrics, setMetrics] = useState<ToneMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const analyze = useCallback((text: string): void => {
    if (!text.trim()) {
      setMetrics(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchToneAnalysis(text)
      .then(setMetrics)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => analyze(draftText), debounceMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [draftText, debounceMs, analyze]);

  if (!metrics && !loading && !error) return null;

  return (
    <div className="tone-indicator">
      <h4 className="tone-title">Tone Analysis</h4>
      {loading && <span className="tone-loading">Analyzing...</span>}
      {error && <span className="tone-error">{error}</span>}
      {metrics && (
        <>
          <div className="tone-gauges">
            <MetricGauge
              label="Reading Level"
              value={metrics.reading_level}
              max={20}
              format={formatGrade}
              warn={metrics.reading_level > 12}
            />
            <MetricGauge
              label="Marketing"
              value={metrics.marketing_score}
              max={1}
              format={formatPercent}
              warn={metrics.marketing_score > 0.7}
            />
            <MetricGauge
              label="AI Likelihood"
              value={metrics.ai_likelihood}
              max={1}
              format={formatPercent}
              warn={metrics.ai_likelihood > 0.8}
            />
            <MetricGauge
              label="Authenticity"
              value={metrics.authenticity_score}
              max={1}
              format={formatPercent}
              warn={false}
            />
          </div>
          <WarningList warnings={metrics.warnings} />
        </>
      )}
    </div>
  );
};

interface MetricGaugeProps {
  label: string;
  value: number;
  max: number;
  format: (v: number) => string;
  warn: boolean;
}

const MetricGauge: React.FC<MetricGaugeProps> = ({
  label,
  value,
  max,
  format,
  warn,
}) => {
  const pct = Math.min((value / max) * 100, 100);
  const barClass = warn ? "gauge-bar gauge-bar--warn" : "gauge-bar";

  return (
    <div className="tone-gauge">
      <div className="gauge-header">
        <span className="gauge-label">
          {warn && <span className="warn-icon" aria-label="Warning">&#9888;</span>}
          {label}
        </span>
        <span className="gauge-value">{format(value)}</span>
      </div>
      <div className="gauge-track">
        <div className={barClass} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

interface WarningListProps {
  warnings: ToneWarning[];
}

const WarningList: React.FC<WarningListProps> = ({ warnings }) => {
  if (warnings.length === 0) return null;

  return (
    <div className="tone-warnings">
      <h5>Suggestions to Improve Tone</h5>
      <ul>
        {warnings.map((w) => (
          <li key={w.code} className="tone-warning-item">
            <span className="warn-icon" aria-label="Warning">&#9888;</span>
            <div>
              <strong>{w.message}</strong>
              <p className="warn-suggestion">{w.suggestion}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

function formatGrade(v: number): string {
  return `Grade ${v.toFixed(1)}`;
}

function formatPercent(v: number): string {
  return `${(v * 100).toFixed(0)}%`;
}

export default ToneIndicator;
