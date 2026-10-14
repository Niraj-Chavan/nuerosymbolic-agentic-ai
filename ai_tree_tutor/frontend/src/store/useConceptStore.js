import { create } from 'zustand';
import { getConcepts, getProgress, getWeakConcepts } from '../api/api';

const useConceptStore = create((set) => ({
  conceptGraph: null,
  progress: null,
  weakConcepts: [],
  loading: false,
  error: null,

  fetchGraph: async () => {
    set({ loading: true, error: null });
    try {
      const res = await getConcepts();
      set({ conceptGraph: res, loading: false });
    } catch (err) {
      set({ loading: false, error: err.message });
    }
  },

  fetchProgress: async () => {
    try {
      const res = await getProgress();
      set({ progress: res });
    } catch {
      /* silent */
    }
  },

  fetchWeakConcepts: async (threshold = 0.4) => {
    try {
      const res = await getWeakConcepts(threshold);
      set({ weakConcepts: res });
    } catch {
      /* silent */
    }
  },
}));

export default useConceptStore;
