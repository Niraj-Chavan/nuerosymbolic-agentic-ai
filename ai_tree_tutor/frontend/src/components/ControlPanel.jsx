/**
 * ControlPanel Component
 * =======================
 * Tree selection, operation controls, and key input.
 */

import React from 'react';

const TREE_LABELS = {
  avl: '⚖️  AVL Tree',
  red_black: '🔴  Red-Black Tree',
  heap: '🏔️  Binary Heap',
  segment_tree: '📐  Segment Tree',
  btree: '🌳  B-Tree',
  bplus_tree: '🌲  B+ Tree',
};

const NEEDS_ORDER = ['btree', 'bplus_tree'];

export default function ControlPanel({
  selectedTree,
  onSelectTree,
  keyValue,
  onKeyChange,
  onOperate,
  onReset,
  loading,
  operationLog,
  treeOrder,
  onOrderChange,
  heapType,
  onHeapTypeChange,
  lastOperation,
  lastOperationKey,
  searchFound,
  rangeLow,
  rangeHigh,
  rangeResult,
  onRangeLowChange,
  onRangeHighChange,
  onRangeQuery,
}) {
  return (
    <div className="control-panel glass-card slide-in">
      <h2>Tree Selection</h2>
      <div className="tree-selector">
        {Object.entries(TREE_LABELS).map(([type, label]) => (
          <button
            key={type}
            id={`tree-btn-${type}`}
            className={`tree-btn ${selectedTree === type ? 'active' : ''}`}
            onClick={() => onSelectTree(type)}
          >
            {label}
          </button>
        ))}
      </div>

      {NEEDS_ORDER.includes(selectedTree) && (
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Tree Order (degree)
          </label>
          <input
            id="tree-order-input"
            type="number"
            min={2}
            max={10}
            value={treeOrder}
            onChange={(e) => onOrderChange(Math.max(2, Math.min(10, Number(e.target.value) || 3)))}
            className="key-input"
            style={{ width: '100%' }}
          />
        </div>
      )}

      {selectedTree === 'segment_tree' && (
        <div style={{ marginBottom: 16, padding: 10, background: 'rgba(124,58,237,0.06)', borderRadius: 'var(--radius-sm)' }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            📐 Range Query
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 6 }}>
            <input
              id="range-low"
              type="number"
              className="key-input"
              placeholder="Low index"
              value={rangeLow}
              onChange={(e) => onRangeLowChange(e.target.value)}
              style={{ width: '100%' }}
            />
            <input
              id="range-high"
              type="number"
              className="key-input"
              placeholder="High index"
              value={rangeHigh}
              onChange={(e) => onRangeHighChange(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <button
            id="btn-range-query"
            className="op-btn insert"
            onClick={onRangeQuery}
            disabled={!rangeLow || !rangeHigh}
            style={{ width: '100%', fontSize: '0.8rem' }}
          >
            📊 Query Range Sum
          </button>
          {rangeResult !== null && rangeResult !== undefined && (
            <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(124,58,237,0.1)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
              <strong>Range [{rangeResult?.left ?? '?'}, {rangeResult?.right ?? '?'}]:</strong>{' '}
              <span style={{ fontWeight: 800, color: 'var(--accent-tertiary)' }}>{rangeResult?.result ?? rangeResult}</span>
            </div>
          )}
        </div>
      )}

      {selectedTree === 'heap' && (
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
            Heap Type
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              id="heap-type-min"
              className={`op-btn quiz-option-btn ${heapType === 'min' ? 'selected' : ''}`}
              style={{
                flex: 1,
                padding: '6px 12px',
                fontSize: '0.8rem',
                background: heapType === 'min' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${heapType === 'min' ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.1)'}`,
                borderRadius: 'var(--radius-sm)',
                color: heapType === 'min' ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
              onClick={() => onHeapTypeChange('min')}
            >
              ⬇️ Min Heap
            </button>
            <button
              id="heap-type-max"
              className={`op-btn quiz-option-btn ${heapType === 'max' ? 'selected' : ''}`}
              style={{
                flex: 1,
                padding: '6px 12px',
                fontSize: '0.8rem',
                background: heapType === 'max' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${heapType === 'max' ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.1)'}`,
                borderRadius: 'var(--radius-sm)',
                color: heapType === 'max' ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
              onClick={() => onHeapTypeChange('max')}
            >
              ⬆️ Max Heap
            </button>
          </div>
        </div>
      )}

      <h2>Operations</h2>
      <div className="operation-group">
        <div className="input-group">
          <input
            id="key-input"
            type="number"
            className="key-input"
            placeholder="Enter key value…"
            value={keyValue}
            onChange={(e) => onKeyChange(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') onOperate('insert'); }}
          />
        </div>
        <div className="input-group">
          <button id="btn-insert" className="op-btn insert" onClick={() => onOperate('insert')} disabled={loading}>
            ＋ Insert
          </button>
          <button id="btn-delete" className="op-btn delete" onClick={() => onOperate('delete')} disabled={loading}>
            ✕ Delete
          </button>
        </div>
        <div className="input-group">
          <button id="btn-search" className="op-btn search" onClick={() => onOperate('search')} disabled={loading}>
            🔍 Search
          </button>
          <button id="btn-reset" className="op-btn reset" onClick={onReset} disabled={loading}>
            ↺ Reset
          </button>
        </div>
      </div>

      {lastOperation === 'search' && lastOperationKey !== null && (
        <div
          id="search-result-alert"
          style={{
            marginTop: 12,
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.88rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: searchFound
              ? 'rgba(16, 185, 129, 0.1)'
              : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${
              searchFound ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
            }`,
            color: searchFound ? '#10b981' : '#ef4444',
            animation: 'fadeIn 0.3s ease',
          }}
        >
          <span>{searchFound ? '✅' : '❌'}</span>
          <span>
            Key <strong>{lastOperationKey}</strong> {searchFound ? 'found in the tree!' : 'not found in the tree.'}
          </span>
        </div>
      )}

      {operationLog && operationLog.length > 0 && (
        <>
          <h2>Operation Log</h2>
          <ul className="log-list">
            {operationLog.slice(-10).reverse().map((entry, i) => (
              <li key={i} className="log-item">
                <span className="log-action">{entry.action}</span>
                <span>{entry.key !== undefined ? `key: ${entry.key}` : ''}</span>
                {entry.type && <span>({entry.type})</span>}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
