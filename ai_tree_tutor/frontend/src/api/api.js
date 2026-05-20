/**
 * API Client
 * ===========
 * Axios-based client for the AI Tree Tutor backend.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Execute a tree operation (insert / delete / search).
 * Triggers the full agentic pipeline on the backend.
 */
export async function operateTree(treeType, operation, key, sessionId = 'default', options = {}) {
  const res = await api.post('/tree/operate', {
    tree_type: treeType,
    operation,
    key: Number(key),
    session_id: sessionId,
    options,
  });
  return res.data;
}

/** Reset a tree to empty state. */
export async function resetTree(treeType, sessionId = 'default', options = {}) {
  const res = await api.post('/tree/reset', {
    tree_type: treeType,
    session_id: sessionId,
    options,
  });
  return res.data;
}

/** Get the exported tree state. */
export async function exportTree(treeType, sessionId = 'default') {
  const res = await api.get(`/tree/export/${treeType}`, { params: { session_id: sessionId } });
  return res.data;
}

/** Get the full concept knowledge graph. */
export async function getConcepts() {
  const res = await api.get('/concepts');
  return res.data;
}

/** Get learning progress summary. */
export async function getProgress() {
  const res = await api.get('/concepts/progress');
  return res.data;
}

/** Get weak concepts. */
export async function getWeakConcepts(threshold = 0.4) {
  const res = await api.get('/concepts/weak', { params: { threshold } });
  return res.data;
}

/** Get supported tree types. */
export async function getTrees() {
  const res = await api.get('/trees');
  return res.data;
}

/** Get complexity analysis. */
export async function getComplexity(treeType, operation) {
  const res = await api.get(`/complexity/${treeType}/${operation}`);
  return res.data;
}

/** Generate a quiz. */
export async function generateQuiz(treeType = null, numQuestions = 5, difficulty = 'mixed', focusWeak = true, signal = null) {
  const res = await api.post('/quiz/generate', {
    tree_type: treeType,
    num_questions: numQuestions,
    difficulty,
    focus_weak: focusWeak,
  }, { signal });
  return res.data;
}

/** Submit quiz answers for evaluation. */
export async function submitQuiz(questions, answers) {
  const res = await api.post('/quiz/submit', { questions, answers });
  return res.data;
}

/** Get quiz history. */
export async function getQuizHistory() {
  const res = await api.get('/quiz/history');
  return res.data;
}

/** Get learning report. */
export async function getLearningReport() {
  const res = await api.get('/quiz/report');
  return res.data;
}

/** Get study recommendations. */
export async function getRecommendations() {
  const res = await api.get('/quiz/recommendations');
  return res.data;
}

/** Poll for async task result. */
export async function getTaskResult(taskId) {
  const res = await api.get(`/quiz/task/${taskId}`);
  return res.data;
}

/** Execute a tree operation with step-by-step animation data. */
export async function operateTreeSteps(treeType, operation, key, sessionId = 'default', options = {}) {
  const res = await api.post('/tree/operate-steps', {
    tree_type: treeType,
    operation,
    key: Number(key),
    session_id: sessionId,
    options,
  });
  return res.data;
}

/** Execute a segment tree range query. */
export async function rangeQuery(left, right, sessionId = 'default') {
  const res = await api.post('/tree/segment/range-query', {
    left: Number(left),
    right: Number(right),
    session_id: sessionId,
  });
  return res.data;
}

export default api;
