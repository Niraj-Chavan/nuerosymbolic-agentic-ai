/**
 * Dashboard Component
 * ====================
 * Displays learning progress, mastery bars, and concept stats.
 */

import React from 'react';
import ConceptGraph from './ConceptGraph';

export default function Dashboard({ progress, conceptData }) {
  if (!progress) {
    return (
      <div className="dashboard-panel glass-card fade-in">
        <h2>Progress Dashboard</h2>
        <div className="explanation-text" style={{ opacity: 0.5 }}>
          Start performing operations to track your progress.
        </div>
      </div>
    );
  }

  const masteryPercent = Math.round((progress.average_mastery || 0) * 100);

  // Build concept mastery list from concept data
  const conceptNodes = conceptData?.nodes || [];
  const activeConcepts = conceptNodes
    .filter((c) => c.attempts > 0)
    .sort((a, b) => a.mastery - b.mastery);

  return (
    <div className="dashboard-panel glass-card fade-in">
      <h2>Progress Dashboard</h2>

      {/* Summary Stats */}
      <div className="progress-grid">
        <div className="stat-card">
          <div className="stat-value">{progress.total_concepts}</div>
          <div className="stat-label">Total Concepts</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress.mastered}</div>
          <div className="stat-label">Mastered</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progress.in_progress}</div>
          <div className="stat-label">In Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{masteryPercent}%</div>
          <div className="stat-label">Avg Mastery</div>
        </div>
      </div>

      {/* Overall mastery bar */}
      <div className="mastery-bar-container">
        <div className="mastery-label">
          <span>Overall Progress</span>
          <span>{masteryPercent}%</span>
        </div>
        <div className="mastery-bar">
          <div
            className={`mastery-fill ${masteryPercent >= 70 ? 'high' : masteryPercent >= 40 ? 'medium' : 'low'}`}
            style={{ width: `${masteryPercent}%` }}
          />
        </div>
      </div>

      {/* Per-concept mastery */}
      {activeConcepts.length > 0 && (
        <>
          <h2 style={{ marginTop: 16 }}>Concept Mastery</h2>
          {activeConcepts.map((concept) => {
            const pct = Math.round(concept.mastery * 100);
            const label = concept.name || concept.id || concept.concept || 'Unknown';
            return (
              <div key={concept.id} className="mastery-bar-container">
                <div className="mastery-label">
                  <span>{label}</span>
                  <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {concept.mistakes > 0 && (
                      <span style={{ color: '#ef4444', fontSize: '0.7rem' }}>
                        {concept.mistakes} mistakes
                      </span>
                    )}
                    {pct}%
                  </span>
                </div>
                <div className="mastery-bar">
                  <div
                    className={`mastery-fill ${pct >= 70 ? 'high' : pct >= 40 ? 'medium' : 'low'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </>
      )}

      {/* D3 concept graph visualization */}
      {conceptData?.nodes?.length > 0 && (
        <ConceptGraph conceptData={conceptData} />
      )}
    </div>
  );
}
