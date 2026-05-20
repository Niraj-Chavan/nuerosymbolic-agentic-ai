import { create } from 'zustand';
import { operateTree, resetTree, operateTreeSteps, rangeQuery } from '../api/api';

function conceptWhy(treeType, operation) {
  const base = {
    avl: 'AVL operations first preserve BST order, then restore |balance factor| <= 1.',
    red_black: 'Red-Black operations preserve BST order while repairing color and black-height rules.',
    heap: 'Heap operations preserve complete-tree shape and parent-child priority ordering.',
    segment_tree: 'Segment tree operations update range summaries from children to parents.',
    btree: 'B-Tree operations keep sorted multi-key nodes balanced by splitting overflow.',
    bplus_tree: 'B+ Tree operations keep leaves ordered and internal keys as search guides.',
  };
  return base[treeType] || `This step advances the ${operation} while preserving the tree invariant.`;
}

function normalizeStepType(type) {
  const text = String(type || '').toLowerCase();
  if (text.includes('rotate') || text.includes('rotation')) return 'rotate';
  if (text.includes('recolor')) return 'recolor';
  if (text.includes('split')) return 'split';
  if (text.includes('compare') || text.includes('search')) return 'compare';
  if (text.includes('delete')) return 'delete';
  if (text.includes('insert')) return 'insert';
  if (text.includes('sift') || text.includes('heap')) return 'sift';
  return text || 'info';
}

function describeLogEntry(entry, operation, key, treeType) {
  if (entry.message) return entry.message;
  if (entry.action) return `${treeType} ${entry.action} during ${operation} ${key}`;
  return `${operation} ${key}`;
}

function normalizePath(path) {
  if (!Array.isArray(path)) return [];
  return path.flatMap((item) => {
    if (typeof item === 'number' || typeof item === 'string') return [Number(item)];
    if (item?.key !== undefined) return [Number(item.key)];
    if (Array.isArray(item?.keys)) return item.keys.map(Number);
    return [];
  });
}

function buildAnimationSteps(result, operation, key, treeType, path) {
  const logSteps = (result.log || [])
    .map((entry, index) => ({
      step_number: index + 1,
      tree: entry.tree_state || entry.tree || result.tree,
      description: entry.description || describeLogEntry(entry, operation, key, treeType),
      step_type: normalizeStepType(entry.action || entry.type || operation),
      highlighted_nodes: entry.node_keys || entry.affected_nodes || entry.highlighted_nodes || [],
      why: entry.why || entry.concept_tag || conceptWhy(treeType, operation),
    }))
    .filter((step) => step.description);

  if (logSteps.length > 0) return logSteps;

  const pathKeys = normalizePath(path);
  const fallback = [];
  if (operation === 'search' && pathKeys.length) {
    pathKeys.forEach((nodeKey) => {
      fallback.push({
        step_number: fallback.length + 1,
        tree: result.tree,
        description: `Visit ${nodeKey} while searching for ${key}`,
        step_type: 'compare',
        highlighted_nodes: [nodeKey, key],
        why: key < nodeKey
          ? `${key} is smaller, so the search moves left.`
          : key > nodeKey
            ? `${key} is larger, so the search moves right.`
            : 'The search key matches this node.',
      });
    });
  }

  fallback.push({
    step_number: fallback.length + 1,
    tree: result.tree,
    description: `${operation} ${key} complete`,
    step_type: result.validation?.valid === false ? 'violation' : 'result',
    highlighted_nodes: [key],
    why: conceptWhy(treeType, operation),
  });

  return fallback;
}

const useTreeStore = create((set, get) => ({
  treeData: null,
  operationLog: [],
  validation: null,
  diagnosis: null,
  teaching: null,
  complexity: null,
  animationSteps: [],
  searchPath: [],
  highlightedKeys: [],
  selectedTree: 'avl',
  keyValue: '',
  treeOrder: 3,
  heapType: 'min',
  lastOperation: null,
  lastOperationKey: null,
  searchFound: null,
  rangeLow: '',
  rangeHigh: '',
  rangeResult: null,
  loading: false,
  error: null,

  setSelectedTree: (tree) => {
    const defaultOrder = tree === 'bplus_tree' ? 4 : 3;
    set({
      selectedTree: tree,
      treeOrder: defaultOrder,
      heapType: 'min',
      treeData: null,
      operationLog: [],
      validation: null,
      diagnosis: null,
      teaching: null,
      complexity: null,
      animationSteps: [],
      searchPath: [],
      highlightedKeys: [],
      lastOperation: null,
      lastOperationKey: null,
      searchFound: null,
      rangeLow: '',
      rangeHigh: '',
      rangeResult: null,
    });
  },

  setKeyValue: (key) => set({ keyValue: key }),

  setTreeOrder: (order) => set({ treeOrder: order }),

  setHeapType: (type) => {
    set({ heapType: type });
    get().reset();
  },

  setRangeLow: (v) => set({ rangeLow: v }),
  setRangeHigh: (v) => set({ rangeHigh: v }),

  performRangeQuery: async () => {
    const { rangeLow, rangeHigh } = get();
    const low = Number(rangeLow);
    const high = Number(rangeHigh);
    if (!Number.isFinite(low) || !Number.isFinite(high) || low > high) {
      set({ error: 'Invalid range: ensure both indices are valid numbers and low ≤ high.' });
      return;
    }
    set({ loading: true, error: null });
    try {
      const result = await rangeQuery(low, high);
      set({ rangeResult: result, rangeLow: '', rangeHigh: '', loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  performOperation: async (operation) => {
    const { selectedTree, keyValue, treeOrder, heapType } = get();
    if (keyValue === '' || keyValue === null || keyValue === undefined) return;
    const numericKey = Number(keyValue);
    if (!Number.isFinite(numericKey)) {
      set({ error: 'Please enter a valid numeric key.' });
      return;
    }
    set({ loading: true, error: null });
    try {
      const opts = selectedTree === 'heap'
        ? { heap_type: heapType }
        : ['btree', 'bplus_tree'].includes(selectedTree)
          ? { order: treeOrder }
          : {};
      const result = await operateTree(selectedTree, operation, numericKey, 'default', opts);
      const path = operation === 'search'
        ? (result.path || result.log?.find((l) => l.action === 'search')?.path || [])
        : [];
      const steps = buildAnimationSteps(result, operation, numericKey, selectedTree, path);
      set({
        treeData: result.tree,
        operationLog: result.log || [],
        validation: result.validation || null,
        diagnosis: result.diagnosis || null,
        teaching: result.teaching || null,
        complexity: result.complexity || null,
        searchPath: path,
        animationSteps: steps,
        highlightedKeys: steps[0]?.highlighted_nodes || [],
        lastOperation: operation,
        lastOperationKey: numericKey,
        searchFound: operation === 'search' ? result.found : null,
        keyValue: '',
        loading: false,
      });
      if (result.concept_update) {
        const { fetchProgress } = await import('./useConceptStore').then((m) => m.default.getState());
        if (fetchProgress) fetchProgress();
      }
      return result;
    } catch (err) {
      set({
        validation: { valid: false, violations: [{ type: 'api_error', message: err.message || 'Request failed' }] },
        error: err.message,
        loading: false,
      });
    }
  },

  fetchAnimationSteps: async (operation) => {
    const { selectedTree, keyValue, treeOrder, heapType } = get();
    if (keyValue === '' || keyValue === null || keyValue === undefined) return;
    const numericKey = Number(keyValue);
    if (!Number.isFinite(numericKey)) {
      set({ error: 'Please enter a valid numeric key.' });
      return;
    }
    try {
      const opts = selectedTree === 'heap'
        ? { heap_type: heapType }
        : ['btree', 'bplus_tree'].includes(selectedTree)
          ? { order: treeOrder }
          : {};
      const res = await operateTreeSteps(selectedTree, operation, numericKey, 'default', opts);
      set({ animationSteps: res.animation_steps || [] });
      return res;
    } catch (err) {
      set({ error: err.message });
    }
  },

  reset: async () => {
    const { selectedTree, treeOrder, heapType } = get();
    set({ loading: true });
    try {
      const opts = selectedTree === 'heap'
        ? { heap_type: heapType }
        : ['btree', 'bplus_tree'].includes(selectedTree)
          ? { order: treeOrder }
          : {};
      await resetTree(selectedTree, 'default', opts);
      set({
        treeData: null,
        operationLog: [],
        validation: null,
        diagnosis: null,
        teaching: null,
        complexity: null,
        animationSteps: [],
        searchPath: [],
        highlightedKeys: [],
        lastOperation: null,
        lastOperationKey: null,
        searchFound: null,
        loading: false,
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  setHighlightedKeys: (keys) => set({ highlightedKeys: keys }),
}));

export default useTreeStore;
