import React, { useState, useEffect, useRef } from 'react';
import ControlPanel from './components/ControlPanel.jsx';
import TreeVisualizer from './components/TreeVisualizer.jsx';
import ExplanationPanel from './components/ExplanationPanel.jsx';
import Dashboard from './components/Dashboard.jsx';
import QuizPanel from './components/QuizPanel.jsx';
import AnimationController from './components/AnimationController.jsx';
import { useOperation, useAnimation } from './hooks';
import useTreeStore from './store/useTreeStore';
import { rangeQuery } from './api/api.js';
import useConceptStore from './store/useConceptStore';
import TutorWorkspace from './components/TutorWorkspace.jsx';

export default function App() {
  const [activeTab, setActiveTab] = useState('practice');
  const [showAnimation, setShowAnimation] = useState(true);

  const {
    operate,
    operateWithSteps,
    reset,
    loading,
  } = useOperation();

  const selectedTree = useTreeStore((s) => s.selectedTree);
  const setSelectedTree = useTreeStore((s) => s.setSelectedTree);
  const keyValue = useTreeStore((s) => s.keyValue);
  const setKeyValue = useTreeStore((s) => s.setKeyValue);
  const treeOrder = useTreeStore((s) => s.treeOrder);
  const setTreeOrder = useTreeStore((s) => s.setTreeOrder);
  const treeData = useTreeStore((s) => s.treeData);
  const operationLog = useTreeStore((s) => s.operationLog);
  const validation = useTreeStore((s) => s.validation);
  const diagnosis = useTreeStore((s) => s.diagnosis);
  const teaching = useTreeStore((s) => s.teaching);
  const complexity = useTreeStore((s) => s.complexity);
  const searchPath = useTreeStore((s) => s.searchPath);
  const highlightedKeys = useTreeStore((s) => s.highlightedKeys);
  const setHighlightedKeys = useTreeStore((s) => s.setHighlightedKeys);
  const lastOperation = useTreeStore((s) => s.lastOperation);
  const lastOperationKey = useTreeStore((s) => s.lastOperationKey);
  const rangeLow = useTreeStore((s) => s.rangeLow);
  const rangeHigh = useTreeStore((s) => s.rangeHigh);
  const rangeResult = useTreeStore((s) => s.rangeResult);
  const setRangeLow = useTreeStore((s) => s.setRangeLow);
  const setRangeHigh = useTreeStore((s) => s.setRangeHigh);
  const performRangeQuery = useTreeStore((s) => s.performRangeQuery);
  const heapType = useTreeStore((s) => s.heapType);
  const setHeapType = useTreeStore((s) => s.setHeapType);
  const searchFound = useTreeStore((s) => s.searchFound);

  const {
    steps,
    currentStep,
    isPlaying,
    play,
    pause,
    stepForward,
    stepBackward,
    goToStep,
    changeSpeed,
    speed,
    getTreeSnapshot,
    isActive,
  } = useAnimation();

  const conceptGraph = useConceptStore((s) => s.conceptGraph);
  const progress = useConceptStore((s) => s.progress);
  const fetchGraph = useConceptStore((s) => s.fetchGraph);
  const fetchProgress = useConceptStore((s) => s.fetchProgress);

  const fetchedRef = useRef(false);
  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    const store = useConceptStore.getState();
    store.fetchGraph();
    store.fetchProgress();
  }, []);

  useEffect(() => {
    if (steps.length > 0) setShowAnimation(true);
  }, [steps.length]);

  const handleSelectTree = (type) => {
    setSelectedTree(type);
  };

  const handleOperate = async (operation) => {
    if (keyValue === '' || keyValue === null || keyValue === undefined) {
      return;
    }
    const numericKey = Number(keyValue);
    if (!Number.isFinite(numericKey)) return;
    await operate(operation);
  };

  const handleReset = async () => {
    await reset();
  };

  const handleRangeQuery = () => {
    performRangeQuery();
  };

  const handleConceptUpdate = async () => {
    await fetchProgress();
    await fetchGraph();
  };

  const violations = validation?.violations || [];
  const visualTreeData = getTreeSnapshot() || treeData;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">🧠</div>
          <div>
            <h1>AI Tree Tutor</h1>
            <div className="subtitle">Neuro-Symbolic Adaptive Learning Platform</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            id="tab-practice"
            className={`op-btn ${activeTab === 'practice' ? 'insert' : ''}`}
            onClick={() => setActiveTab('practice')}
            style={{ padding: '8px 18px', fontSize: '0.8rem' }}
          >
            🌳 Practice
          </button>
          <button
            id="tab-quiz"
            className={`op-btn ${activeTab === 'quiz' ? 'insert' : ''}`}
            onClick={() => setActiveTab('quiz')}
            style={{ padding: '8px 18px', fontSize: '0.8rem' }}
          >
            📝 Quiz
          </button>
          <button
            id="tab-tutor"
            className={`op-btn ${activeTab === 'tutor' ? 'insert' : ''}`}
            onClick={() => setActiveTab('tutor')}
            style={{ padding: '8px 18px', fontSize: '0.8rem' }}
          >
            🎓 AI Tutor
          </button>
          {loading && (
            <span style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 500 }}>
              ⟳ Processing...
            </span>
          )}
        </div>
      </header>

      {activeTab === 'tutor' ? (
        <TutorWorkspace />
      ) : (
        <main className="main-grid">
          <ControlPanel
            selectedTree={selectedTree}
            onSelectTree={handleSelectTree}
            keyValue={keyValue}
            onKeyChange={setKeyValue}
            onOperate={handleOperate}
            onReset={handleReset}
            loading={loading}
            operationLog={operationLog}
            treeOrder={treeOrder}
            onOrderChange={setTreeOrder}
            heapType={heapType}
            onHeapTypeChange={setHeapType}
            lastOperation={lastOperation}
            lastOperationKey={lastOperationKey}
            searchFound={searchFound}
            rangeLow={rangeLow}
            rangeHigh={rangeHigh}
            rangeResult={rangeResult}
            onRangeLowChange={setRangeLow}
            onRangeHighChange={setRangeHigh}
            onRangeQuery={handleRangeQuery}
          />

          <div className="visualization-stack">
            <AnimationController
              steps={steps}
              currentStep={currentStep}
              onStepChange={goToStep}
              onTreeSnapshot={() => {}}
              onHighlight={setHighlightedKeys}
              isActive={isActive && showAnimation}
              onClose={() => setShowAnimation(false)}
            />
            <TreeVisualizer
              treeData={visualTreeData}
              treeType={selectedTree}
              violations={violations}
              searchPath={searchPath}
              animationSteps={steps}
              currentStep={currentStep}
              highlightedKeys={highlightedKeys}
              operation={lastOperation}
              operationKey={lastOperationKey}
            />
          </div>

          <div className="right-panel">
            {activeTab === 'practice' ? (
              <ExplanationPanel
                validation={validation}
                diagnosis={diagnosis}
                teaching={teaching}
                complexity={complexity}
              />
            ) : (
              <QuizPanel onConceptUpdate={handleConceptUpdate} />
            )}
            <Dashboard progress={progress} conceptData={conceptGraph} />
          </div>
        </main>
      )}
    </div>
  );
}
