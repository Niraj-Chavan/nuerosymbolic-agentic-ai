/**
 * QuizPanel Component
 * =====================
 * Adaptive quiz interface powered by the Quiz Agent.
 * Generates questions, evaluates answers, shows results,
 * weak points, AI feedback, and study recommendations.
 */

import React, { useState, useRef, useEffect } from 'react';
import { generateQuiz, submitQuiz } from '../api/api.js';

const TREE_OPTIONS = [
  { value: '', label: '🎯 All topics (Adaptive)' },
  { value: 'avl', label: '⚖️ AVL Tree' },
  { value: 'red_black', label: '🔴 Red-Black Tree' },
  { value: 'heap', label: '🏔️ Binary Heap' },
  { value: 'segment_tree', label: '📐 Segment Tree' },
  { value: 'btree', label: '🌳 B-Tree' },
  { value: 'bplus_tree', label: '🌲 B+ Tree' },
];

export default function QuizPanel({ onConceptUpdate }) {
  // Quiz config
  const [quizTopic, setQuizTopic] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState('mixed');
  const [focusWeak, setFocusWeak] = useState(true);

  // Quiz state
  const [phase, setPhase] = useState('setup'); // setup | taking | results
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  // --------------------------------------------------------- Generate Quiz
  const handleGenerate = async () => {
    setErrorMsg(null);
    setLoading(true);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    try {
      const quiz = await generateQuiz(
        quizTopic || null,
        numQuestions,
        difficulty,
        focusWeak,
        controller.signal,
      );
      clearTimeout(timeoutId);
      if (controller.signal.aborted) return;
      const qs = quiz.questions || [];
      if (qs.length === 0) {
        throw new Error('No questions available. Try a different topic or difficulty.');
      }
      setQuestions(qs);
      setAnswers(new Array(qs.length).fill(-1));
      setCurrentQ(0);
      setResults(null);
      setPhase('taking');
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        setErrorMsg('Request timed out. The quiz engine may be busy — try again.');
      } else {
        setErrorMsg(err.message || 'Failed to generate quiz');
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  // --------------------------------------------------------- Select Answer
  const handleAnswer = (optionIndex) => {
    const newAnswers = [...answers];
    newAnswers[currentQ] = optionIndex;
    setAnswers(newAnswers);
  };

  // --------------------------------------------------------- Submit Quiz
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const report = await submitQuiz(questions, answers);
      setResults(report);
      setPhase('results');
      if (onConceptUpdate && report.progress) {
        onConceptUpdate(report.progress);
      }
    } catch (err) {
      console.error('Failed to submit quiz:', err);
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------------- Reset
  const handleRetake = () => {
    setPhase('setup');
    setQuestions([]);
    setAnswers([]);
    setResults(null);
    setCurrentQ(0);
    setErrorMsg(null);
  };

  // ============================================================ SETUP PHASE
  if (phase === 'setup') {
    return (
      <div className="glass-card fade-in" id="quiz-panel">
        <h2>📝 Adaptive Quiz</h2>
        <p className="explanation-text" style={{ marginBottom: 16 }}>
          Test your understanding. The AI targets your weak concepts.
        </p>

        {errorMsg && (
          <div style={{ padding: 10, marginBottom: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 'var(--radius-sm)', color: '#fca5a5', fontSize: '0.85rem' }}>
            ⚠️ {errorMsg}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Topic</label>
            <select
              id="quiz-topic"
              value={quizTopic}
              onChange={(e) => setQuizTopic(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px',
                background: 'var(--bg-glass)', border: '1px solid var(--border-glass)',
                borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', fontSize: '0.9rem', outline: 'none',
              }}
            >
              {TREE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Questions</label>
              <input
                id="quiz-count"
                type="number"
                min={1}
                max={20}
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="key-input"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Difficulty</label>
              <select
                id="quiz-difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px',
                  background: 'var(--bg-glass)', border: '1px solid var(--border-glass)',
                  borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
                  fontFamily: 'var(--font-sans)', fontSize: '0.9rem', outline: 'none',
                }}
              >
                <option value="mixed">Mixed</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={focusWeak}
              onChange={(e) => setFocusWeak(e.target.checked)}
              style={{ accentColor: 'var(--accent-primary)' }}
            />
            🎯 Focus on my weak concepts
          </label>

          {loading && (
            <div style={{ padding: 8, marginBottom: 4, fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              ⟳ Generating quiz questions...
            </div>
          )}
          <button
            id="btn-start-quiz"
            className="op-btn insert"
            onClick={handleGenerate}
            disabled={loading}
            style={{ width: '100%', marginTop: 8, padding: '12px' }}
          >
            {loading ? '⟳ Generating...' : '🚀 Start Quiz'}
          </button>
        </div>
      </div>
    );
  }

  // ============================================================ TAKING PHASE
  if (phase === 'taking' && questions.length > 0) {
    const q = questions[currentQ];
    const isLast = currentQ === questions.length - 1;
    const allAnswered = answers.every((a) => a !== -1);

    return (
      <div className="glass-card fade-in" id="quiz-active">
        <h2>📝 Quiz — Question {currentQ + 1}/{questions.length}</h2>

        {/* Progress bar */}
        <div style={{ marginBottom: 16 }}>
          <div className="mastery-bar" style={{ height: 4 }}>
            <div
              className="mastery-fill high"
              style={{ width: `${((currentQ + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Difficulty badge */}
        {q.difficulty && (
          <span style={{
            fontSize: '0.7rem', fontWeight: 600, padding: '3px 8px',
            borderRadius: 12, marginBottom: 12, display: 'inline-block',
            background: q.difficulty === 'easy' ? 'rgba(16,185,129,0.15)' : q.difficulty === 'hard' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
            color: q.difficulty === 'easy' ? 'var(--accent-success)' : q.difficulty === 'hard' ? 'var(--accent-danger)' : 'var(--accent-warning)',
          }}>
            {q.difficulty.toUpperCase()}
          </span>
        )}

        {/* Question */}
        <p style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 16, lineHeight: 1.6 }}>
          {q.question}
        </p>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(q.options || []).map((option, idx) => (
            <button
              key={idx}
              id={`quiz-option-${idx}`}
              onClick={() => handleAnswer(idx)}
              style={{
                padding: '12px 16px',
                background: answers[currentQ] === idx ? 'rgba(99,102,241,0.2)' : 'var(--bg-glass)',
                border: answers[currentQ] === idx ? '2px solid var(--accent-primary)' : '1px solid var(--border-glass)',
                borderRadius: 'var(--radius-sm)',
                color: answers[currentQ] === idx ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'var(--transition)',
              }}
            >
              <span style={{ fontWeight: 700, marginRight: 8, color: 'var(--accent-primary)' }}>
                {String.fromCharCode(65 + idx)}.
              </span>
              {option}
            </button>
          ))}
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20, gap: 8 }}>
          <button
            className="op-btn search"
            onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
            disabled={currentQ === 0}
            style={{ flex: 1 }}
          >
            ← Previous
          </button>

          {isLast ? (
            <button
              id="btn-submit-quiz"
              className="op-btn insert"
              onClick={handleSubmit}
              disabled={!allAnswered || loading}
              style={{ flex: 1 }}
            >
              {loading ? '⟳ Evaluating...' : '✓ Submit Quiz'}
            </button>
          ) : (
            <button
              className="op-btn search"
              onClick={() => setCurrentQ(Math.min(questions.length - 1, currentQ + 1))}
              style={{ flex: 1 }}
            >
              Next →
            </button>
          )}
        </div>

        {/* Question dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 12 }}>
          {questions.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentQ(i)}
              style={{
                width: 10, height: 10, borderRadius: '50%', border: 'none', cursor: 'pointer',
                background: i === currentQ ? 'var(--accent-primary)' : answers[i] !== -1 ? 'var(--accent-success)' : 'var(--border-glass)',
                transition: 'var(--transition)',
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  // ============================================================ RESULTS PHASE
  if (phase === 'results' && results) {
    const {
      percentage = 0, grade = 'N/A', score = 0, total = 0,
      results: questionResults = [],
      weak_points = [], recommendations = [],
    } = results;
    const incorrect = total - score;

    return (
      <div className="glass-card fade-in" id="quiz-results" style={{ maxHeight: '80vh', overflowY: 'auto' }}>
        <h2>📊 Quiz Results</h2>

        {/* Score header */}
        <div style={{ textAlign: 'center', marginBottom: 20, padding: 20, background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)' }}>
          <div style={{
            fontSize: '3rem', fontWeight: 800,
            background: percentage >= 70 ? 'linear-gradient(135deg, #10b981, #06b6d4)' : percentage >= 50 ? 'linear-gradient(135deg, #f59e0b, #ef4444)' : 'linear-gradient(135deg, #ef4444, #dc2626)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>
            {percentage}%
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
            Grade: {grade}
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: 4 }}>
            {score}/{total} correct
          </p>
        </div>

        {/* Weak Points */}
        {weak_points && weak_points.length > 0 && (
          <div className="explanation-section">
            <h3>⚠️ Weak Points</h3>
            {weak_points.map((concept, i) => (
              <div key={i} className="mastery-bar-container">
                <div className="mastery-label">
                  <span>{typeof concept === 'string' ? concept : concept.concept}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Question-by-question review */}
        <div className="explanation-section">
          <h3>📋 Question Review</h3>
          {questionResults && questionResults.map((r, i) => (
            <div key={i} style={{
              padding: 12, marginBottom: 8,
              background: r.correct ? 'rgba(16,185,129,0.05)' : 'rgba(239,68,68,0.05)',
              border: `1px solid ${r.correct ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
              borderRadius: 'var(--radius-sm)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: '0.8rem', color: r.correct ? 'var(--accent-success)' : 'var(--accent-danger)' }}>
                  {r.correct ? '✓' : '✗'} Q{i + 1}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{r.question_type}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                {r.question}
              </p>
              {!r.correct && r.explanation && (
                <p style={{ fontSize: '0.8rem', color: 'var(--accent-tertiary)', marginTop: 6, fontStyle: 'italic' }}>
                  💡 {r.explanation}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div className="explanation-section">
            <h3>📚 Recommendations</h3>
            {recommendations.map((rec, i) => (
              <div key={i} className="key-rule" style={{ marginBottom: 8 }}>
                <strong>{rec.concept}</strong>: {rec.suggestion || rec.action}
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button id="btn-retake-quiz" className="op-btn insert" onClick={handleRetake} style={{ flex: 1, padding: 12 }}>
            🔄 New Quiz
          </button>
        </div>
      </div>
    );
  }

  return null;
}
