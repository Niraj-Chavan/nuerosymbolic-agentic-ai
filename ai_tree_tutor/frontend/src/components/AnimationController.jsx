/**
 * AnimationController Component
 * ===============================
 * Step-by-step animation controls for tree operations.
 * Shows play/pause, step forward/back, speed control,
 * and a detailed description with WHY for each step.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

const STEP_COLORS = {
  compare: '#6366f1',
  insert: '#10b981',
  rotate: '#f59e0b',
  recolor: '#ec4899',
  split: '#8b5cf6',
  sift: '#06b6d4',
  delete: '#ef4444',
  merge: '#f97316',
  promote: '#a855f7',
  result: '#10b981',
  info: '#94a3b8',
};

const STEP_ICONS = {
  compare: '🔍',
  insert: '➕',
  rotate: '🔄',
  recolor: '🎨',
  split: '✂️',
  sift: '↕️',
  delete: '🗑️',
  merge: '🔗',
  promote: '⬆️',
  result: '✅',
  info: 'ℹ️',
};

export default function AnimationController({
  steps,
  currentStep,
  onStepChange,
  onTreeSnapshot,
  onHighlight,
  isActive,
  onClose,
}) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1200); // ms per step
  const timerRef = useRef(null);

  const total = steps?.length || 0;
  const step = steps?.[currentStep] || null;
  const progress = total > 0 ? ((currentStep + 1) / total) * 100 : 0;

  // Auto-play
  useEffect(() => {
    if (playing && currentStep < total - 1) {
      timerRef.current = setTimeout(() => {
        goNext();
      }, speed);
    } else if (currentStep >= total - 1) {
      setPlaying(false);
    }
    return () => clearTimeout(timerRef.current);
  }, [playing, currentStep, speed, total]);

  // Update tree snapshot and highlights when step changes
  useEffect(() => {
    if (step) {
      if (step.tree && onTreeSnapshot) onTreeSnapshot(step.tree);
      if (onHighlight) onHighlight(step.highlighted_nodes || []);
    }
  }, [currentStep, step]);

  const goNext = useCallback(() => {
    if (currentStep < total - 1) onStepChange(currentStep + 1);
  }, [currentStep, total, onStepChange]);

  const goPrev = useCallback(() => {
    if (currentStep > 0) onStepChange(currentStep - 1);
  }, [currentStep, onStepChange]);

  const goFirst = useCallback(() => {
    onStepChange(0);
    setPlaying(false);
  }, [onStepChange]);

  const goLast = useCallback(() => {
    onStepChange(total - 1);
    setPlaying(false);
  }, [total, onStepChange]);

  const togglePlay = useCallback(() => {
    if (currentStep >= total - 1) {
      onStepChange(0);
      setPlaying(true);
    } else {
      setPlaying(p => !p);
    }
  }, [currentStep, total, onStepChange]);

  if (!isActive || !steps || steps.length === 0) return null;

  const stepColor = STEP_COLORS[step?.step_type] || '#94a3b8';
  const stepIcon = STEP_ICONS[step?.step_type] || 'ℹ️';

  return (
    <div className="glass-card fade-in" style={{
      marginBottom: 16,
      border: `1px solid ${stepColor}33`,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 12,
      }}>
        <h2 style={{ fontSize: '1rem', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          🎬 Step-by-Step Animation
        </h2>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#ef4444', borderRadius: 6, padding: '4px 12px', cursor: 'pointer',
            fontSize: '0.75rem', fontWeight: 600,
          }}
        >✕ Close</button>
      </div>

      {/* Progress Bar */}
      <div style={{
        height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2,
        marginBottom: 12, overflow: 'hidden',
      }}>
        <div style={{
          width: `${progress}%`, height: '100%',
          background: `linear-gradient(90deg, ${stepColor}, ${stepColor}88)`,
          borderRadius: 2, transition: 'width 0.3s ease',
        }} />
      </div>

      {/* Step Counter */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 10,
      }}>
        <span style={{
          fontSize: '0.75rem', fontWeight: 600, color: stepColor,
          background: `${stepColor}15`, padding: '3px 10px', borderRadius: 12,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          {stepIcon} Step {currentStep + 1} / {total}
        </span>
        <span style={{
          fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}>
          {step?.step_type || 'info'}
        </span>
      </div>

      {/* Description */}
      <div style={{
        padding: '12px 14px', borderRadius: 'var(--radius-sm)',
        background: `${stepColor}08`, border: `1px solid ${stepColor}20`,
        marginBottom: 10,
      }}>
        <p style={{
          margin: 0, fontSize: '0.88rem', fontWeight: 500,
          color: 'var(--text-primary)', lineHeight: 1.5,
        }}>
          {step?.description || 'No description'}
        </p>
      </div>

      {/* WHY */}
      {step?.why && (
        <div style={{
          padding: '10px 14px', borderRadius: 'var(--radius-sm)',
          background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.15)',
          marginBottom: 10,
        }}>
          <span style={{
            fontSize: '0.7rem', fontWeight: 600, color: '#8b5cf6',
            display: 'block', marginBottom: 3,
          }}>WHY?</span>
          <p style={{
            margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5,
          }}>
            {step.why}
          </p>
        </div>
      )}

      {/* Highlighted Nodes */}
      {step?.highlighted_nodes?.length > 0 && (
        <div style={{ marginBottom: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Highlighted:</span>
          {step.highlighted_nodes.map((n, i) => (
            <span key={i} style={{
              background: `${stepColor}20`, color: stepColor,
              padding: '2px 8px', borderRadius: 10, fontSize: '0.75rem',
              fontWeight: 600, fontFamily: 'var(--font-mono)',
            }}>{n}</span>
          ))}
        </div>
      )}

      {/* Controls */}
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        gap: 6, marginBottom: 10,
      }}>
        <button onClick={goFirst} disabled={currentStep === 0}
          style={controlBtn(currentStep === 0)} title="First step">⏮</button>
        <button onClick={goPrev} disabled={currentStep === 0}
          style={controlBtn(currentStep === 0)} title="Previous step">◀</button>
        <button onClick={togglePlay}
          style={{
            ...controlBtn(false),
            padding: '8px 20px', fontSize: '1rem',
            background: playing ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)',
            borderColor: playing ? 'rgba(239,68,68,0.3)' : 'rgba(99,102,241,0.3)',
            color: playing ? '#ef4444' : '#6366f1',
          }}
          title={playing ? 'Pause' : 'Play'}
        >
          {playing ? '⏸' : '▶'}
        </button>
        <button onClick={goNext} disabled={currentStep >= total - 1}
          style={controlBtn(currentStep >= total - 1)} title="Next step">▶</button>
        <button onClick={goLast} disabled={currentStep >= total - 1}
          style={controlBtn(currentStep >= total - 1)} title="Last step">⏭</button>
      </div>

      {/* Speed Control */}
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        gap: 10, marginTop: 4,
      }}>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Speed:</span>
        {[
          { label: '0.5×', ms: 2400 },
          { label: '1×', ms: 1200 },
          { label: '2×', ms: 600 },
          { label: '3×', ms: 350 },
        ].map(s => (
          <button key={s.label} onClick={() => setSpeed(s.ms)}
            style={{
              background: speed === s.ms ? 'rgba(99,102,241,0.2)' : 'transparent',
              border: `1px solid ${speed === s.ms ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.08)'}`,
              color: speed === s.ms ? '#6366f1' : '#94a3b8',
              borderRadius: 6, padding: '3px 10px', cursor: 'pointer',
              fontSize: '0.72rem', fontWeight: 600,
            }}
          >{s.label}</button>
        ))}
      </div>

      {/* Step Timeline */}
      <div style={{
        display: 'flex', gap: 3, marginTop: 12, flexWrap: 'wrap',
        justifyContent: 'center',
      }}>
        {steps.map((s, i) => {
          const c = STEP_COLORS[s.step_type] || '#94a3b8';
          return (
            <button key={i} onClick={() => { setPlaying(false); onStepChange(i); }}
              title={`Step ${i+1}: ${s.description?.substring(0,60) || ''}`}
              style={{
                width: i === currentStep ? 20 : 10,
                height: 10,
                borderRadius: 5,
                border: 'none',
                background: i === currentStep ? c : i < currentStep ? `${c}60` : 'rgba(255,255,255,0.08)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

function controlBtn(disabled) {
  return {
    background: disabled ? 'transparent' : 'rgba(255,255,255,0.05)',
    border: `1px solid ${disabled ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.12)'}`,
    color: disabled ? '#334155' : '#e2e8f0',
    borderRadius: 8,
    padding: '6px 12px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: '0.85rem',
    opacity: disabled ? 0.4 : 1,
  };
}
