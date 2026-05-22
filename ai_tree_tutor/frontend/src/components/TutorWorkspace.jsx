import React, { useEffect, useState, useRef } from 'react';
import useTutorStore from '../store/useTutorStore';
import useConceptStore from '../store/useConceptStore';

// Lightweight Markdown-to-HTML parser for dynamic theories
function parseMarkdown(text) {
  if (!text) return '';
  let html = text;
  
  // Replace HTML special characters to prevent XSS
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
    
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4 style="margin-top: 16px; margin-bottom: 8px; color: var(--text-primary); font-size: 0.95rem; font-weight: 600;">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="margin-top: 20px; margin-bottom: 10px; color: var(--text-primary); font-size: 1.05rem; font-weight: 700; border-bottom: 1px solid var(--border-glass); padding-bottom: 4px;">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 style="margin-top: 24px; margin-bottom: 12px; color: var(--text-primary); font-size: 1.2rem; font-weight: 800;">$1</h2>');
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-primary); font-weight: 700;">$1</strong>');
  
  // Unordered list items
  html = html.replace(/^\s*[\*\-]\s+(.*$)/gim, '<li style="margin-left: 16px; margin-bottom: 4px; list-style-type: disc; color: var(--text-secondary);">$1</li>');
  
  // Newlines to paragraphs
  html = html.split('\n\n').map(para => {
    if (para.trim().startsWith('<li') || para.trim().startsWith('<h')) {
      return para;
    }
    return `<p style="margin-bottom: 12px; line-height: 1.5; color: var(--text-secondary); font-size: 0.88rem;">${para}</p>`;
  }).join('\n');
  
  return html;
}

export default function TutorWorkspace() {
  const {
    weakConcepts,
    chatHistory,
    currentRemedy,
    activeConceptId,
    loadingWeak,
    loadingChat,
    loadingRemedy,
    loadingVerify,
    selectedOption,
    answered,
    isCorrectAnswer,
    newMastery,
    feedback,
    fetchWeakConcepts,
    sendChatMessage,
    startRemediationSession,
    submitRemediationAnswer,
    resetRemediation,
  } = useTutorStore();

  // Access concept graph for fallback list if weakConcepts is empty
  const { conceptGraph, fetchGraph, fetchProgress } = useConceptStore();

  const [inputMessage, setInputMessage] = useState('');
  const [selectedOptionLocal, setSelectedOptionLocal] = useState(null);
  const chatEndRef = useRef(null);

  // Load weak concepts, progress, and concept graph on mount
  useEffect(() => {
    fetchWeakConcepts();
    fetchGraph();
    fetchProgress();
  }, [fetchWeakConcepts, fetchGraph, fetchProgress]);

  // Scroll to bottom of chat whenever messages or loading state changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, loadingChat]);

  const handleSendMessage = (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || loadingChat) return;
    sendChatMessage(inputMessage);
    setInputMessage('');
  };

  const handleSuggestionClick = (suggestion) => {
    if (loadingChat) return;
    sendChatMessage(suggestion);
  };

  const handleExitSession = () => {
    setSelectedOptionLocal(null);
    resetRemediation();
  };

  const suggestionChips = [
    "Why do AVL trees rotate?",
    "Explain heapify constraints",
    "What makes a B-Tree balanced?",
    "Explain binary heap min/max ordering rule"
  ];

  return (
    <div className="tutor-grid fade-in">
      {/* LEFT PANEL: Socratic Chat Room */}
      <div className="tutor-chat-panel glass-card">
        <h2>💬 Socratic Tutor</h2>
        
        <div className="tutor-chat-messages">
          {chatHistory.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%', alignItems: 'center', color: 'var(--text-muted)', textAlign: 'center', padding: 16 }}>
              <span style={{ fontSize: '2.5rem', marginBottom: 12 }}>🎓</span>
              <p style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                I am your Socratic AI Tutor.
              </p>
              <p style={{ fontSize: '0.85rem', marginTop: 4, maxWidth: 300 }}>
                Ask me any questions about AVL Trees, Red-Black Trees, Binary Heaps, Segment Trees, or B-Trees! I will guide you to find the answers yourself.
              </p>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div key={idx} className="tutor-chat-bubble-container">
                <div className={`tutor-avatar ${msg.role}`}>
                  {msg.role === 'tutor' ? '🎓 Socratic Tutor' : '👤 Student'}
                </div>
                <div className={`tutor-chat-bubble ${msg.role}`}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
          
          {loadingChat && (
            <div className="tutor-chat-bubble-container">
              <div className="tutor-avatar tutor">🎓 Socratic Tutor</div>
              <div className="tutor-chat-bubble tutor" style={{ display: 'flex', padding: '10px 14px' }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Suggestion Chips */}
        {chatHistory.length < 3 && (
          <div className="tutor-suggestions">
            {suggestionChips.map((sug, idx) => (
              <button
                key={idx}
                className="tutor-suggestion-chip"
                onClick={() => handleSuggestionClick(sug)}
                disabled={loadingChat}
              >
                {sug}
              </button>
            ))}
          </div>
        )}

        {/* Chat Input */}
        <form onSubmit={handleSendMessage} className="tutor-chat-input-container">
          <input
            type="text"
            className="tutor-chat-input"
            placeholder={activeConceptId ? "Ask a question about this remediation..." : "Ask the tutor a question..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={loadingChat}
          />
          <button
            type="submit"
            className="tutor-chat-send"
            disabled={!inputMessage.trim() || loadingChat}
          >
            Send
          </button>
        </form>
      </div>

      {/* RIGHT PANEL: Concept Repair Playground */}
      <div className="remediation-panel glass-card" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)', minHeight: 550, overflow: 'hidden' }}>
        {!currentRemedy ? (
          <div style={{ overflowY: 'auto', flex: 1, paddingRight: 4 }}>
            <div className="concept-repair-header">
              <h2>🛠️ Concept Remediation Hub</h2>
            </div>
            
            <p className="explanation-text" style={{ margin: '8px 0 16px 0' }}>
              Concept mastery is updated based on your quiz answers and operations mistakes. If mastery drops below 50%, the concept requires repair.
            </p>

            {loadingWeak || loadingRemedy ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 0', gap: 12 }}>
                <div className="typing-indicator">
                  <div className="typing-dot" style={{ width: 8, height: 8 }}></div>
                  <div className="typing-dot" style={{ width: 8, height: 8 }}></div>
                  <div className="typing-dot" style={{ width: 8, height: 8 }}></div>
                </div>
                <span className="explanation-text" style={{ fontSize: '0.85rem' }}>Analyzing concept graph and starting remediation...</span>
              </div>
            ) : weakConcepts.length > 0 ? (
              <div className="weak-concepts-list">
                {weakConcepts.map((concept) => {
                  const percentage = Math.round(concept.mastery * 100);
                  return (
                    <div key={concept.id} className="weak-concept-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                          {concept.name}
                        </span>
                        <span className="violation-badge error">
                          Mastery: {percentage}%
                        </span>
                      </div>
                      
                      {concept.false_belief && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', borderLeft: '2px solid rgba(239, 68, 68, 0.3)', paddingLeft: 8 }}>
                          Common misconception: {concept.false_belief}
                        </p>
                      )}
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Mistakes: {concept.mistakes || 0}
                        </span>
                        <button
                          className="op-btn insert"
                          style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                          onClick={() => startRemediationSession(concept.id)}
                        >
                          Start Concept Repair
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ padding: 32, border: '1px dashed var(--border-glass)', borderRadius: 'var(--radius-md)', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
                <span style={{ fontSize: '2.5rem' }}>🌟</span>
                <h3 style={{ color: 'var(--accent-success)', fontSize: '1rem', fontWeight: 600 }}>
                  All Concepts Healthy!
                </h3>
                <p className="explanation-text" style={{ fontSize: '0.85rem', maxWidth: 450 }}>
                  You don't have any weak concepts (mastery &lt; 50%) in your Concept Graph right now. Outstanding work!
                </p>
                <p className="explanation-text" style={{ fontSize: '0.8rem', opacity: 0.7, maxWidth: 400 }}>
                  If you want to review or test yourself on other topics, you can select any concept from the concept graph on the Practice / Quiz tabs, or initiate a quiz focused on specific data structures.
                </p>
                {conceptGraph?.nodes && conceptGraph.nodes.length > 0 && (
                  <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, width: '100%', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                      Quick Review (Select to Repair Anyway)
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
                      {conceptGraph.nodes.slice(0, 6).map((node) => (
                        <button
                          key={node.id}
                          className="tutor-suggestion-chip"
                          onClick={() => startRemediationSession(node.id)}
                        >
                          {node.name || node.id}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="remediation-session fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20, height: '100%', overflowY: 'auto', paddingRight: '8px' }}>
            <div className="concept-repair-header" style={{ position: 'sticky', top: 0, background: 'var(--bg-glass)', backdropFilter: 'blur(10px)', padding: '12px 0', borderBottom: '1px solid var(--border-glass)', zIndex: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--accent-primary)', fontWeight: 700, letterSpacing: '0.05em' }}>
                  Active Remediation Session
                </span>
                <h2 className="remedy-concept-title" style={{ fontSize: '1.25rem', margin: 0 }}>
                  {currentRemedy.concept_name}
                </h2>
              </div>
              <button className="op-btn reset" onClick={handleExitSession}>
                Exit Session
              </button>
            </div>

            {/* Premium Dynamic Theory Card */}
            {currentRemedy.theory && (
              <div className="remedy-theory-card fade-in" style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', padding: 20, borderRadius: 'var(--radius-md)' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', fontWeight: 650, color: 'var(--text-primary)', marginBottom: 12, marginTop: 0 }}>
                  <span>📘</span> Concept Theory
                </h3>
                <div 
                  className="theory-content-markdown"
                  style={{ maxWidth: '100%', wordBreak: 'break-word' }}
                  dangerouslySetInnerHTML={{ __html: parseMarkdown(currentRemedy.theory) }}
                />
              </div>
            )}

            {/* Premium Dynamic Video Link Card */}
            {currentRemedy.video_link && (
              <a 
                href={currentRemedy.video_link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="remedy-video-card fade-in"
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 16, 
                  background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)', 
                  border: '1px solid rgba(239, 68, 68, 0.3)', 
                  padding: '16px 20px', 
                  borderRadius: 'var(--radius-md)',
                  textDecoration: 'none',
                  color: 'inherit',
                  transition: 'var(--transition)',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(239, 68, 68, 0.2)';
                  e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                }}
              >
                <div style={{ fontSize: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(239, 68, 68, 0.2)', width: 48, height: 48, borderRadius: '50%', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
                  🎬
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 650, color: 'var(--text-primary)' }}>
                    Video Tutorial: {currentRemedy.concept_name}
                  </h4>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Click to watch a high-quality educational walkthrough video on YouTube.
                  </p>
                </div>
                <div style={{ fontSize: '1.25rem', color: 'var(--text-muted)' }}>
                  ➜
                </div>
              </a>
            )}

            {/* Dynamic Agentic Interactive Widget */}
            {chatHistory[chatHistory.length - 1]?.widget && (
              <div className="remedy-theory-card fade-in" style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', padding: 20, borderRadius: 'var(--radius-md)' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem', fontWeight: 650, color: 'var(--text-primary)', marginBottom: 12, marginTop: 0 }}>
                  <span>🔍</span> Interactive Widget
                </h3>
                {chatHistory[chatHistory.length - 1].widget.type === 'html' ? (
                  <div 
                    className="dynamic-widget-container" 
                    style={{ background: '#1e1e1e', padding: 16, borderRadius: 'var(--radius-md)', color: '#fff', overflow: 'hidden' }}
                    dangerouslySetInnerHTML={{ __html: chatHistory[chatHistory.length - 1].widget.content }}
                  />
                ) : (
                  <pre style={{ background: '#1e1e1e', padding: 16, borderRadius: 'var(--radius-md)', color: '#d4d4d4', overflowX: 'auto', fontSize: '0.85rem' }}>
                    <code>{chatHistory[chatHistory.length - 1].widget.content || JSON.stringify(chatHistory[chatHistory.length - 1].widget, null, 2)}</code>
                  </pre>
                )}
              </div>
            )}

            {!chatHistory[chatHistory.length - 1]?.widget && (
              <div className="remedy-theory-card fade-in" style={{ textAlign: 'center', padding: '32px 20px', background: 'var(--bg-glass)', border: '1px dashed var(--border-glass)', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: 12 }}>💬</span>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 650, margin: '0 0 8px 0' }}>Socratic Discussion Active</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: 350, margin: '0 auto', lineHeight: '1.5' }}>
                  Use the tutor chat panel on the left to discuss and explain. The AI will guide you and automatically verify when the concept is repaired!
                </p>
              </div>
            )}

            {isCorrectAnswer && (
              <div className="remedy-feedback-card success fade-in" style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: 16, borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', marginTop: 8, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                  🎉 Correct! Concept Repaired!
                </div>
                <p style={{ fontSize: '0.85rem', margin: '4px 0 0 0', color: 'var(--text-secondary)' }}>{feedback}</p>
                {newMastery !== null && (
                  <div style={{ marginTop: 8, fontSize: '0.82rem', fontWeight: 600 }}>
                    Updated Mastery Score: <span style={{ color: 'var(--accent-success)' }}>{Math.round(newMastery * 100)}%</span>
                  </div>
                )}
                <button
                  className="op-btn insert"
                  style={{ width: '100%', marginTop: 12, padding: '10px', fontSize: '0.85rem' }}
                  onClick={handleExitSession}
                >
                  Return to Concept Hub
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
