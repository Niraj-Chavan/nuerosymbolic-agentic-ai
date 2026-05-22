import { create } from 'zustand';
import {
  tutorChat,
  startRemediation,
  verifyRemediation,
  getWeakConceptsTutor,
  getLearningPath,
  getExplainableAI,
  getEmotionalAnalytics,
  analyzeDiagram,
} from '../api/api';

const useTutorStore = create((set, get) => ({
  weakConcepts: [],
  chatHistory: [],
  currentRemedy: null,
  activeConceptId: null,
  learningPath: null,
  explainableAI: [],
  emotionalState: {
    sentiment: 'neutral',
    cognitive_load: 'medium',
    engagement_level: 75,
    avg_response_time: 0,
    hints_used: 0,
    retries: 0,
  },
  diagramAnalysis: null,
  
  // Loading states
  loadingWeak: false,
  loadingChat: false,
  loadingRemedy: false,
  loadingVerify: false,
  loadingPath: false,
  loadingExplainable: false,
  loadingEmotion: false,
  loadingDiagram: false,

  // Pedagogical details
  pedagogyStrategy: '',
  pedagogyReason: '',

  // Remediation session state
  selectedOption: null,
  answered: false,
  isCorrectAnswer: null,
  newMastery: null,
  feedback: '',

  // WebSocket reference
  socket: null,

  connectWebSocket: (sessionId = 'default') => {
    // If socket already exists, do not recreate
    if (get().socket) return;

    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    let wsUrl = `${wsProto}//${wsHost}/api/tutor/ws/${sessionId}`;
    
    // Fallback for development servers (Vite/React dev server on 3000, 5173, etc.)
    if (wsHost.includes('3000') || wsHost.includes('5173') || wsHost.includes('5174') || wsHost.includes('5175')) {
      wsUrl = `ws://localhost:8000/api/tutor/ws/${sessionId}`;
    }

    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket Tutor connected successfully');
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'tutor_message') {
          const tutorMsg = {
            role: 'tutor',
            content: data.content,
            strategy: data.pedagogy_strategy,
            reason: data.pedagogy_reason,
          };
          set((state) => ({
            chatHistory: [...state.chatHistory, tutorMsg],
            emotionalState: data.emotional_state || state.emotionalState,
            pedagogyStrategy: data.pedagogy_strategy || '',
            pedagogyReason: data.pedagogy_reason || '',
            loadingChat: false,
          }));
        } else if (data.type === 'tutor_hint') {
          const hintMsg = {
            role: 'tutor',
            content: `💡 Hint: ${data.content}`,
            isHint: true,
          };
          set((state) => ({
            chatHistory: [...state.chatHistory, hintMsg],
            emotionalState: data.emotional_state || state.emotionalState,
            loadingChat: false,
          }));
        }
      };

      socket.onclose = () => {
        console.log('WebSocket Tutor disconnected');
        set({ socket: null });
      };

      socket.onerror = (err) => {
        console.error('WebSocket Tutor error:', err);
      };

      set({ socket });
    } catch (e) {
      console.error('Failed to create WebSocket tutor connection:', e);
    }
  },

  disconnectWebSocket: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({ socket: null });
    }
  },

  sendWebSocketMessage: (message, conceptId = 'general') => {
    const { socket } = get();
    if (!message.trim()) return;

    const userMsg = { role: 'user', content: message };
    set((state) => ({
      chatHistory: [...state.chatHistory, userMsg],
      loadingChat: true,
    }));

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'student_message',
        content: message,
        concept_id: conceptId,
      }));
    } else {
      // Fallback to REST API if WebSocket is offline
      get().sendChatMessage(message);
    }
  },

  requestWebSocketHint: (conceptId = 'general') => {
    const { socket } = get();
    set({ loadingChat: true });

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'hint_request',
        concept_id: conceptId,
      }));
    } else {
      // Offline fallback
      setTimeout(() => {
        set((state) => ({
          chatHistory: [...state.chatHistory, { role: 'tutor', content: 'Try tracing the balance factors at the node you just modified.', isHint: true }],
          loadingChat: false,
        }));
      }, 500);
    }
  },

  fetchWeakConcepts: async () => {
    set({ loadingWeak: true });
    try {
      const res = await getWeakConceptsTutor();
      set({ weakConcepts: res || [], loadingWeak: false });
    } catch (err) {
      set({ loadingWeak: false });
    }
  },

  fetchLearningPath: async (sessionId = 'default') => {
    set({ loadingPath: true });
    try {
      const res = await getLearningPath(sessionId);
      set({ learningPath: res || null, loadingPath: false });
    } catch (err) {
      set({ loadingPath: false });
    }
  },

  fetchExplainableAI: async (sessionId = 'default') => {
    set({ loadingExplainable: true });
    try {
      const res = await getExplainableAI(sessionId);
      set({ explainableAI: res?.decisions || [], loadingExplainable: false });
    } catch (err) {
      set({ loadingExplainable: false });
    }
  },

  fetchEmotionalAnalytics: async (sessionId = 'default') => {
    set({ loadingEmotion: true });
    try {
      const res = await getEmotionalAnalytics(sessionId);
      set({ emotionalState: res || get().emotionalState, loadingEmotion: false });
    } catch (err) {
      set({ loadingEmotion: false });
    }
  },

  submitDiagramUpload: async (conceptId, base64Image, sessionId = 'default') => {
    set({ loadingDiagram: true, diagramAnalysis: null });
    try {
      const res = await analyzeDiagram(conceptId, base64Image, sessionId);
      set({ diagramAnalysis: res, loadingDiagram: false });
      
      // Add result to chat history
      const feedbackMsg = {
        role: 'tutor',
        content: `🔍 Handdrawn Diagram Review:\nCorrect: ${res.is_correct ? 'Yes' : 'No'}\nFeedback: ${res.feedback}\nAnnotations: ${res.annotations || 'None'}`
      };
      set((state) => ({
        chatHistory: [...state.chatHistory, feedbackMsg]
      }));

      // Trigger refreshes
      get().fetchWeakConcepts();
      get().fetchEmotionalAnalytics(sessionId);
      get().fetchExplainableAI(sessionId);
    } catch (err) {
      set({ loadingDiagram: false });
    }
  },

  sendChatMessage: async (message) => {
    if (!message.trim()) return;
    
    const userMsg = { role: 'user', content: message };
    set((state) => ({
      chatHistory: [...state.chatHistory, userMsg],
      loadingChat: true,
    }));

    try {
      const { chatHistory, activeConceptId } = get();
      const historyPayload = chatHistory.slice(0, -1);
      
      const res = await tutorChat(message, historyPayload, activeConceptId);
      const tutorMsg = { 
        role: 'tutor', 
        content: res.response || "Let's think: what is the invariant we are trying to maintain here?",
        widget: res.widget 
      };
      
      set((state) => ({
        chatHistory: [...state.chatHistory, tutorMsg],
        loadingChat: false,
        answered: res.repaired ? true : state.answered,
        isCorrectAnswer: res.repaired ? true : state.isCorrectAnswer,
        newMastery: res.repaired ? 1.0 : state.newMastery,
        feedback: res.repaired ? "Excellent work! You've demonstrated a solid understanding of this concept." : state.feedback
      }));
    } catch (err) {
      const errorMsg = { role: 'tutor', content: "Let's think: what do you think is the main purpose of this tree's properties?" };
      set((state) => ({
        chatHistory: [...state.chatHistory, errorMsg],
        loadingChat: false,
      }));
    }
  },

  startRemediationSession: async (conceptId) => {
    set({
      loadingRemedy: true,
      activeConceptId: conceptId,
      currentRemedy: null,
      selectedOption: null,
      answered: false,
      isCorrectAnswer: null,
      newMastery: null,
      feedback: '',
      diagramAnalysis: null,
    });

    try {
      const res = await startRemediation(conceptId);
      set({
        currentRemedy: res,
        loadingRemedy: false,
        chatHistory: [
          { role: 'tutor', content: res.message || `Hello! Let's work on repairing the concept: ${res.concept_name}. What makes this concept confusing for you?` }
        ]
      });
      // Automatically connect websocket
      get().connectWebSocket();
    } catch (err) {
      set({ loadingRemedy: false });
    }
  },

  submitRemediationAnswer: async (optionIndex) => {
    const { currentRemedy, activeConceptId } = get();
    if (!currentRemedy || optionIndex === null || optionIndex === undefined) return;

    set({ loadingVerify: true });
    const correctIndex = currentRemedy.interactive_question.correct_option_index;
    const isCorrect = Number(optionIndex) === Number(correctIndex);
    const feedbackMsg = isCorrect 
      ? (currentRemedy.interactive_question.explanation || "Excellent! You've grasped the core concept correctly.") 
      : "That's not quite right. Let's read the theory or ask me a question about it. Remember to check the invariants.";

    try {
      const res = await verifyRemediation(activeConceptId, isCorrect);
      set({
        selectedOption: optionIndex,
        answered: true,
        isCorrectAnswer: isCorrect,
        newMastery: res.new_mastery,
        feedback: feedbackMsg,
        loadingVerify: false,
      });
      
      // Update weak list and analytics
      get().fetchWeakConcepts();
      get().fetchEmotionalAnalytics();
      get().fetchExplainableAI();
    } catch (err) {
      set({
        selectedOption: optionIndex,
        answered: true,
        isCorrectAnswer: isCorrect,
        feedback: feedbackMsg,
        loadingVerify: false,
      });
    }
  },

  resetChat: () => {
    set({ chatHistory: [] });
  },

  resetRemediation: () => {
    get().disconnectWebSocket();
    set({
      currentRemedy: null,
      activeConceptId: null,
      selectedOption: null,
      answered: false,
      isCorrectAnswer: null,
      newMastery: null,
      feedback: '',
      pedagogyStrategy: '',
      pedagogyReason: '',
      diagramAnalysis: null,
    });
  }
}));

export default useTutorStore;
