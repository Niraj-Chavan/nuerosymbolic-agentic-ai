/**
 * ExplanationPanel Component
 * ============================
 * Displays validation results, misconception diagnosis,
 * teaching explanations, and complexity analysis.
 */

import React from 'react';

export default function ExplanationPanel({ validation, diagnosis, teaching, complexity }) {
  const violations = validation?.violations || [];
  const isValid = validation?.valid !== false;

  return (
    <div className="explanation-panel glass-card fade-in">
      <h2>Analysis & Explanation</h2>

      {/* Validation Status */}
      <div className="explanation-section">
        <h3>Validation Status</h3>
        {isValid ? (
          <span className="violation-badge success">✓ Tree is valid</span>
        ) : (
          <div>
            <span className="violation-badge error">✗ {violations.length} violation(s)</span>
            <ul style={{ marginTop: 8, paddingLeft: 0, listStyle: 'none' }}>
              {violations.map((v, i) => (
                <li key={i} className="log-item" style={{ borderColor: 'rgba(239,68,68,0.2)' }}>
                  <span className="log-action" style={{ color: '#ef4444' }}>{v.type}</span>
                  <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{v.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Misconception Diagnosis */}
      {diagnosis && diagnosis.misconceptions && diagnosis.misconceptions.length > 0 && (
        <div className="explanation-section">
          <h3>🧠 Misconception Diagnosis</h3>
          {diagnosis.misconceptions.map((m, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <p className="explanation-text">
                <strong>Misconception:</strong> {m.misconception || 'Unknown'}
              </p>
              {m.root_cause && (
                <p className="explanation-text" style={{ fontSize: '0.85rem' }}>
                  <strong>Root cause:</strong> {m.root_cause}
                </p>
              )}
              {m.concept_area && (
                <p style={{ fontSize: '0.8rem', color: '#8b5cf6', marginTop: 4 }}>
                  📚 Concept area: {m.concept_area}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Teaching */}
      {teaching && teaching.length > 0 && (
        <div className="explanation-section">
          <h3>📖 Teaching Explanation</h3>
          {teaching.map((t, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              {t.explanation && (
                <p className="explanation-text">{t.explanation}</p>
              )}
              {t.step_by_step && t.step_by_step.length > 0 && (
                <ol className="step-list">
                  {t.step_by_step.map((step, j) => (
                    <li key={j}>{step}</li>
                  ))}
                </ol>
              )}
              {t.example && (
                <div style={{ marginTop: 8 }}>
                  <p className="explanation-text" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', background: 'var(--bg-glass)', padding: 10, borderRadius: 8 }}>
                    💡 {t.example}
                  </p>
                </div>
              )}
              {t.guiding_question && (
                <div className="guiding-question" style={{ marginTop: 10 }}>
                  🤔 {t.guiding_question}
                </div>
              )}
              {t.key_rule && (
                <div className="key-rule" style={{ marginTop: 8 }}>
                  📌 {t.key_rule}
                </div>
              )}
              {(t.detailed_example || t.example) && (
                <div style={{ marginTop: 10 }}>
                  <h3 style={{ fontSize: '0.75rem', color: 'var(--accent-tertiary)', marginBottom: 4 }}>💡 Worked Example</h3>
                  <pre style={{
                    fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-secondary)',
                    background: 'var(--bg-glass)', padding: 12, borderRadius: 8,
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.6,
                    border: '1px solid rgba(6,182,212,0.15)',
                  }}>
                    {t.detailed_example || t.example}
                  </pre>
                </div>
              )}
              {t.why_this_matters && (
                <div style={{
                  marginTop: 10, padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                  background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)',
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#8b5cf6', display: 'block', marginBottom: 4 }}>🎯 Why This Matters</span>
                  <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>{t.why_this_matters}</p>
                </div>
              )}
              {t.visual_trace && (
                <div style={{ marginTop: 8 }}>
                  <pre style={{
                    fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--accent-success)',
                    background: 'rgba(16,185,129,0.06)', padding: 10, borderRadius: 6,
                    whiteSpace: 'pre-wrap', border: '1px solid rgba(16,185,129,0.15)',
                  }}>
                    {t.visual_trace}
                  </pre>
                </div>
              )}
              {t.common_mistake && (
                <div style={{
                  marginTop: 8, padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                  background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)',
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#ef4444', display: 'block', marginBottom: 4 }}>⚠️ Common Mistake</span>
                  <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', margin: 0 }}>{t.common_mistake}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Complexity */}
      {complexity && !complexity.fallback && !complexity.error && (
        <div className="explanation-section">
          <h3>⏱️ Complexity Analysis</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            {complexity.time_complexity && (
              <>
                <div className="stat-card">
                  <div className="stat-value" style={{ fontSize: '0.95rem' }}>{complexity.time_complexity.best_case}</div>
                  <div className="stat-label">Best</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ fontSize: '0.95rem' }}>{complexity.time_complexity.average_case}</div>
                  <div className="stat-label">Average</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ fontSize: '0.95rem' }}>{complexity.time_complexity.worst_case}</div>
                  <div className="stat-label">Worst</div>
                </div>
              </>
            )}
          </div>
          {complexity.explanation && (
            <p className="explanation-text" style={{ marginTop: 8, fontSize: '0.83rem' }}>
              {complexity.explanation}
            </p>
          )}
        </div>
      )}

      {/* Default empty state */}
      {isValid && !teaching && !diagnosis && (
        <div className="explanation-text" style={{ opacity: 0.5, marginTop: 8 }}>
          Perform an operation to see analysis and explanations.
        </div>
      )}
    </div>
  );
}
