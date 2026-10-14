import { create } from 'zustand';
import { generateQuiz, submitQuiz } from '../api/api';

const useQuizStore = create((set, get) => ({
  questions: [],
  currentIndex: 0,
  answers: [],
  results: null,
  loading: false,
  error: null,
  phase: 'setup',

  setPhase: (phase) => set({ phase }),

  generateQuiz: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const res = await generateQuiz(
        params.tree_type ?? null,
        params.num_questions ?? 5,
        params.difficulty ?? 'mixed',
        params.focus_weak ?? true,
      );
      set({
        questions: res.questions || [],
        currentIndex: 0,
        answers: [],
        results: null,
        phase: 'taking',
        loading: false,
      });
    } catch (err) {
      set({ loading: false, error: err.message });
    }
  },

  answerQuestion: (answerIndex) => {
    set((state) => {
      const answers = [...state.answers];
      answers[state.currentIndex] = answerIndex;
      return { answers };
    });
  },

  nextQuestion: () => {
    set((state) => ({
      currentIndex: Math.min(state.currentIndex + 1, state.questions.length - 1),
    }));
  },

  prevQuestion: () => {
    set((state) => ({
      currentIndex: Math.max(state.currentIndex - 1, 0),
    }));
  },

  submitQuiz: async () => {
    const { questions, answers } = get();
    set({ loading: true, error: null });
    try {
      const res = await submitQuiz(questions, answers);
      set({ results: res, phase: 'results', loading: false });
      return res;
    } catch (err) {
      set({ loading: false, error: err.message });
    }
  },
}));

export default useQuizStore;
