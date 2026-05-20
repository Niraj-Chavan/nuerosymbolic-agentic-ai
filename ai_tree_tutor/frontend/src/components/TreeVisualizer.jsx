/**
 * TreeVisualizer
 * ==============
 * Educational tree simulator surface. React owns data and controls; D3 owns the
 * SVG scene, layout, zooming, and animated transitions.
 */

import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';

const COLORS = {
  panel: '#0f172a',
  text: '#f8fafc',
  muted: '#94a3b8',
  link: 'rgba(148, 163, 184, 0.42)',
  linkActive: '#22d3ee',
  compare: '#38bdf8',
  insert: '#34d399',
  rotate: '#f59e0b',
  split: '#a78bfa',
  violation: '#fb7185',
  normal: '#334155',
  normalStroke: '#818cf8',
  red: '#ef4444',
  redStroke: '#fca5a5',
  black: '#111827',
  blackStroke: '#cbd5e1',
  heap: '#0891b2',
  segment: '#7c3aed',
};

const NODE_RADIUS = 24;
const LEVEL_GAP = 92;
const MIN_NODE_GAP = 86;
const TRANSITION_MS = 650;
const B_KEY_WIDTH = 42;
const B_NODE_HEIGHT = 42;

const CONCEPTS = {
  avl: {
    title: 'AVL balancing lens',
    rules: ['BST path: smaller left, larger right', 'Balance factor = height(left) - height(right)', 'If |BF| > 1, identify LL, RR, LR, or RL and rotate'],
  },
  red_black: {
    title: 'Red-Black invariant lens',
    rules: ['New insertions start red', 'A red node cannot have a red child', 'Every root-to-null path keeps the same black height'],
  },
  heap: {
    title: 'Heap ordering lens',
    rules: ['Shape stays complete left-to-right', 'Each parent is ordered before both children', 'Insert at next slot, then sift to restore order'],
  },
  segment_tree: {
    title: 'Segment range lens',
    rules: ['Each node owns an interval', 'Parent value summarizes its two children', 'Queries split only where ranges overlap'],
  },
  btree: {
    title: 'B-Tree split lens',
    rules: ['Keys inside a node stay sorted', 'Children separate key ranges', 'Overflow promotes the median and splits the node'],
  },
  bplus_tree: {
    title: 'B+ Tree split lens',
    rules: ['Internal nodes guide search', 'All records live in leaves', 'Leaf splits copy the separator upward and keep leaves linked'],
  },
};

const STEP_COLORS = {
  compare: COLORS.compare,
  visit: COLORS.compare,
  insert: COLORS.insert,
  rotate: COLORS.rotate,
  recolor: '#f472b6',
  split: COLORS.split,
  sift: COLORS.compare,
  delete: COLORS.violation,
  result: COLORS.insert,
  violation: COLORS.violation,
};

function useElementSize(ref) {
  const [size, setSize] = useState({ width: 900, height: 560 });

  useEffect(() => {
    if (!ref.current) return undefined;
    const element = ref.current;
    const update = () => {
      const rect = element.getBoundingClientRect();
      setSize({
        width: Math.max(520, Math.floor(rect.width)),
        height: Math.max(460, Math.floor(rect.height || 560)),
      });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}

export default function TreeVisualizer({
  treeData,
  treeType,
  violations = [],
  searchPath = [],
  animationSteps = [],
  currentStep = 0,
  highlightedKeys = [],
  operationKey = null,
  operation = null,
}) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const sceneRef = useRef(null);
  const zoomRef = useRef(null);
  const previousPositionsRef = useRef(new Map());
  const [zoomLevel, setZoomLevel] = useState(1);
  const [sceneReady, setSceneReady] = useState(false);
  const size = useElementSize(containerRef);

  const activeStep = animationSteps?.[currentStep] || null;
  const activeKeys = useMemo(() => new Set([
    ...normalizeKeyList(searchPath),
    ...normalizeKeyList(highlightedKeys),
    ...normalizeKeyList(activeStep?.highlighted_nodes || []),
  ]), [searchPath, highlightedKeys, activeStep]);

  const violationKeys = useMemo(() => collectViolationKeys(violations), [violations]);
  const concept = CONCEPTS[treeType] || CONCEPTS.avl;
  const comparison = useMemo(
    () => buildComparison(activeStep, operationKey, treeType),
    [activeStep, operationKey, treeType],
  );

  const fitView = useCallback(() => {
    if (!svgRef.current || !sceneRef.current || !zoomRef.current) return;
    const svg = d3.select(svgRef.current);
    const scene = sceneRef.current;
    const box = scene.getBBox();
    if (!box.width || !box.height) return;

    const padding = 72;
    const scale = Math.min(
      (size.width - padding) / box.width,
      (size.height - padding) / box.height,
      1.4,
    );
    const tx = size.width / 2 - scale * (box.x + box.width / 2);
    const ty = size.height / 2 - scale * (box.y + box.height / 2);
    svg.transition().duration(TRANSITION_MS).call(
      zoomRef.current.transform,
      d3.zoomIdentity.translate(tx, ty).scale(scale),
    );
  }, [size]);

  const resetZoom = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(TRANSITION_MS)
      .call(zoomRef.current.transform, d3.zoomIdentity);
  }, []);

  // Render SVG unconditionally so D3 always has a surface to init on
  const showEmptyState = !treeData;

  // Always keep the SVG in the DOM; show empty state overlay when no data
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.attr('viewBox', `0 0 ${size.width} ${size.height}`);

    if (!sceneRef.current) {
      svg.selectAll('*').remove();
      svg.append('defs').html(`
        <filter id="nodeGlow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur"></feGaussianBlur>
          <feMerge><feMergeNode in="coloredBlur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge>
        </filter>
        <marker id="arrowHead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L7,3 z" fill="${COLORS.linkActive}"></path>
        </marker>
      `);
      sceneRef.current = svg.append('g').attr('class', 'tree-scene').node();
      zoomRef.current = d3.zoom()
        .scaleExtent([0.22, 3.2])
        .on('zoom', (event) => {
          d3.select(sceneRef.current).attr('transform', event.transform);
          setZoomLevel(event.transform.k);
        });
      svg.call(zoomRef.current);
      setSceneReady(true);
    }
  }, [size]);

  useEffect(() => {
    if (!svgRef.current || !sceneRef.current) return;
    const scene = d3.select(sceneRef.current);
    scene.selectAll('*').interrupt();
    if (!treeData) {
      scene.selectAll('*').remove();
      previousPositionsRef.current = new Map();
      return;
    }

    const renderArgs = {
      scene,
      treeData,
      treeType,
      size,
      activeKeys,
      violationKeys,
      activeStep,
      previousPositions: previousPositionsRef.current,
    };

    const nextPositions = treeType === 'btree' || treeType === 'bplus_tree'
      ? renderMultiwayTree(renderArgs)
      : renderBinaryTree(renderArgs);

    previousPositionsRef.current = nextPositions;
    requestAnimationFrame(fitView);
  }, [treeData, treeType, size, activeKeys, violationKeys, activeStep, fitView, sceneReady]);

  useEffect(() => () => {
    if (svgRef.current) d3.select(svgRef.current).on('.zoom', null).selectAll('*').interrupt();
  }, []);

  const empty = !treeData;

  return (
    <section className="tree-visualizer glass-card fade-in">
      <div className="visualizer-topbar">
        <div>
          <h2>{formatTreeName(treeType)}</h2>
          <p className="visualizer-subtitle">{concept.title}</p>
        </div>
        <div className="zoom-controls">
          <span>{Math.round(zoomLevel * 100)}%</span>
          <button onClick={fitView} title="Fit tree to view" type="button">Fit</button>
          <button onClick={resetZoom} title="Reset zoom" type="button">Reset</button>
        </div>
      </div>

      {comparison && (
        <div className={`concept-ribbon ${comparison.kind}`}>
          <strong>{comparison.label}</strong>
          <span>{comparison.detail}</span>
        </div>
      )}

      <div ref={containerRef} className="tree-svg-container" style={{ position: 'relative' }}>
        <svg ref={svgRef} className="tree-svg" role="img" aria-label={`${formatTreeName(treeType)} visualization`} style={{ display: 'block', width: '100%', height: '100%', minHeight: 470 }} />
        {empty && (
          <div className="tree-empty-state" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
            <div className="tree-empty-symbol">∅</div>
            <p>Select a structure and insert values to begin the simulation.</p>
          </div>
        )}
      </div>

      <div className="concept-strip">
        {concept.rules.map((rule) => (
          <span key={rule}>{rule}</span>
        ))}
      </div>

      {operation && (
        <div className="operation-caption">
          <span>{operation.toUpperCase()}</span>
          {operationKey !== null && operationKey !== '' ? <strong>{operationKey}</strong> : null}
        </div>
      )}
    </section>
  );
}

function renderBinaryTree({
  scene,
  treeData,
  treeType,
  activeKeys,
  violationKeys,
  activeStep,
  previousPositions,
}) {
  const hierarchyData = normalizeBinaryNode(treeData, 'root', null, treeType);
  const root = d3.hierarchy(hierarchyData, (node) => node.children || null);

  const maxDepth = Math.max(1, root.height);
  const leafCount = Math.max(1, root.leaves().filter((d) => !d.data.placeholder).length);
  const labelGap = d3.max(root.descendants(), (d) => textWidth(d.data.label)) || MIN_NODE_GAP;
  const nodeGap = clamp(Math.max(MIN_NODE_GAP, labelGap + 54), MIN_NODE_GAP, leafCount > 18 ? 104 : 132);
  const levelGap = maxDepth > 7 ? 78 : LEVEL_GAP;
  const layout = d3.tree()
    .nodeSize([nodeGap, levelGap])
    .separation((a, b) => {
      const base = a.parent === b.parent ? 1 : 1.35;
      const aWide = textWidth(a.data.label);
      const bWide = textWidth(b.data.label);
      return base + (aWide + bWide) / 170;
    });

  layout(root);
  enforceBinaryDirection(root, nodeGap);

  const allNodes = root.descendants();
  const nodes = allNodes.filter((d) => !d.data.placeholder);
  const slots = allNodes.filter((d) => d.data.placeholder && d.depth < 5);
  const links = root.links().filter((link) => !link.source.data.placeholder && !link.target.data.placeholder);
  const slotLinks = root.links().filter((link) => !link.source.data.placeholder && link.target.data.placeholder);
  const nextPositions = new Map();
  nodes.forEach((d) => nextPositions.set(d.data.id, { x: d.x, y: d.y }));

  scene.selectAll('.btree-layer').remove();
  drawBinaryLinks(scene, links, slotLinks, previousPositions, activeKeys);
  drawBinarySlots(scene, slots);
  drawBinaryNodes(scene, nodes, treeType, activeKeys, violationKeys, previousPositions, activeStep);
  drawEducationalBadges(scene, nodes, treeType, activeStep, activeKeys, violationKeys);

  return nextPositions;
}

function drawBinaryLinks(scene, links, slotLinks, previousPositions, activeKeys) {
  const linkLayer = scene.selectAll('.link-layer').data([null]).join('g').attr('class', 'link-layer');
  const path = d3.linkVertical().x((d) => d.x).y((d) => d.y);

  linkLayer.selectAll('path.tree-link')
    .data(links, (d) => `${d.source.data.id}->${d.target.data.id}`)
    .join(
      (enter) => enter.append('path')
        .attr('class', 'tree-link')
        .attr('fill', 'none')
        .attr('d', (d) => {
          const p = previousPositions.get(d.source.data.id) || { x: d.source.x, y: d.source.y };
          return path({ source: p, target: p });
        }),
      (update) => update,
      (exit) => exit.transition().duration(TRANSITION_MS / 2).attr('opacity', 0).remove(),
    )
    .attr('stroke-width', (d) => linkIsActive(d, activeKeys) ? 4 : 2.2)
    .attr('stroke', (d) => linkIsActive(d, activeKeys) ? COLORS.linkActive : COLORS.link)
    .attr('marker-end', (d) => linkIsActive(d, activeKeys) ? 'url(#arrowHead)' : null)
    .transition()
    .duration(TRANSITION_MS)
    .ease(d3.easeCubicOut)
    .attr('d', path)
    .attr('opacity', 1);

  linkLayer.selectAll('path.slot-link')
    .data(slotLinks, (d) => `${d.source.data.id}->${d.target.data.id}`)
    .join('path')
    .attr('class', 'slot-link')
    .attr('fill', 'none')
    .attr('stroke', 'rgba(148,163,184,0.16)')
    .attr('stroke-dasharray', '4 6')
    .attr('stroke-width', 1.4)
    .transition()
    .duration(TRANSITION_MS)
    .attr('d', path)
    .attr('opacity', 0.8);
}

function drawBinarySlots(scene, slots) {
  const slotLayer = scene.selectAll('.slot-layer').data([null]).join('g').attr('class', 'slot-layer');
  slotLayer.selectAll('g.child-slot')
    .data(slots, (d) => d.data.id)
    .join(
      (enter) => {
        const g = enter.append('g').attr('class', 'child-slot').attr('opacity', 0);
        g.append('circle').attr('r', 7);
        g.append('text').attr('y', 22).attr('text-anchor', 'middle').text((d) => d.data.side);
        return g;
      },
      (update) => update,
      (exit) => exit.transition().duration(220).attr('opacity', 0).remove(),
    )
    .transition()
    .duration(TRANSITION_MS)
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .attr('opacity', 0.45);
}

function drawBinaryNodes(scene, nodes, treeType, activeKeys, violationKeys, previousPositions, activeStep) {
  const nodeLayer = scene.selectAll('.node-layer').data([null]).join('g').attr('class', 'node-layer');

  const groups = nodeLayer.selectAll('g.tree-node')
    .data(nodes, (d) => d.data.id)
    .join(
      (enter) => {
        const g = enter.append('g')
          .attr('class', 'tree-node')
          .attr('transform', (d) => {
            const p = d.parent ? previousPositions.get(d.parent.data.id) : previousPositions.get(d.data.id);
            const from = p || { x: d.x, y: d.y - 48 };
            return `translate(${from.x},${from.y})`;
          })
          .attr('opacity', 0);
        g.append('circle').attr('r', 0);
        g.append('text').attr('class', 'node-key').attr('dy', '0.35em');
        g.append('title');
        return g;
      },
      (update) => update,
      (exit) => exit.transition().duration(TRANSITION_MS / 2).attr('opacity', 0).attr('transform', (d) => `translate(${d.x},${d.y + 34})`).remove(),
    );

  groups.select('title').text((d) => tooltipForNode(d, treeType));

  groups.transition()
    .duration(TRANSITION_MS)
    .ease(d3.easeCubicOut)
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .attr('opacity', 1);

  groups.select('circle')
    .transition()
    .duration(TRANSITION_MS)
    .attr('r', NODE_RADIUS)
    .attr('fill', (d) => nodeFill(d.data, treeType, activeKeys, violationKeys))
    .attr('stroke', (d) => nodeStroke(d.data, treeType, activeKeys, violationKeys))
    .attr('stroke-width', (d) => activeKeys.has(d.data.key) || violationKeys.has(d.data.key) ? 4 : 2.5)
    .attr('filter', (d) => activeKeys.has(d.data.key) || violationKeys.has(d.data.key) ? 'url(#nodeGlow)' : null);

  groups.select('.node-key')
    .attr('text-anchor', 'middle')
    .attr('fill', COLORS.text)
    .attr('font-weight', 800)
    .attr('font-size', (d) => String(d.data.label).length > 3 ? 12 : 14)
    .attr('font-family', 'var(--font-mono)')
    .text((d) => d.data.label);

  nodeLayer.selectAll('g.rotation-halo')
    .data(activeStep && isRotationStep(activeStep) ? nodes.filter((d) => activeKeys.has(d.data.key)) : [], (d) => d.data.id)
    .join(
      (enter) => {
        const g = enter.append('g').attr('class', 'rotation-halo').attr('opacity', 0);
        g.append('circle').attr('r', NODE_RADIUS + 12);
        g.append('text').attr('y', -(NODE_RADIUS + 24)).attr('text-anchor', 'middle');
        return g;
      },
      (update) => update,
      (exit) => exit.remove(),
    )
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .attr('opacity', 1)
    .select('text')
    .text(rotationLabel(activeStep));
}

function drawEducationalBadges(scene, nodes, treeType, activeStep, activeKeys, violationKeys) {
  const badgeLayer = scene.selectAll('.badge-layer').data([null]).join('g').attr('class', 'badge-layer');
  const badgeData = nodes.flatMap((d) => labelsForNode(d, treeType, activeStep, activeKeys, violationKeys));

  const badges = badgeLayer.selectAll('g.edu-badge')
    .data(badgeData, (d) => d.id)
    .join(
      (enter) => {
        const g = enter.append('g').attr('class', 'edu-badge').attr('opacity', 0);
        g.append('rect').attr('rx', 6).attr('height', 20);
        g.append('text').attr('y', 14).attr('text-anchor', 'middle');
        return g;
      },
      (update) => update,
      (exit) => exit.transition().duration(180).attr('opacity', 0).remove(),
    );

  badges.each(function (d) {
    const g = d3.select(this);
    const w = Math.max(36, d.text.length * 7.2 + 12);
    g.select('rect')
      .attr('x', -w / 2)
      .attr('y', -10)
      .attr('width', w)
      .attr('fill', d.fill)
      .attr('stroke', d.stroke);
    g.select('text')
      .attr('fill', d.color)
      .attr('font-family', 'var(--font-mono)')
      .attr('font-size', 10)
      .attr('font-weight', 800)
      .text(d.text);
  });

  badges.transition()
    .duration(TRANSITION_MS)
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .attr('opacity', 1);
}

function renderMultiwayTree({
  scene,
  treeData,
  treeType,
  activeKeys,
  violationKeys,
  activeStep,
  previousPositions,
}) {
  const root = measureMultiwayNode(normalizeMultiwayNode(treeData, 'root'), treeType);
  assignMultiwayPositions(root, -root.subtreeWidth / 2, 0);
  const nodes = flattenMultiway(root);
  const links = nodes.flatMap((node) => (node.children || []).map((child) => ({ source: node, target: child })));
  const nextPositions = new Map(nodes.map((node) => [node.id, { x: node.x, y: node.y }]));

  scene.selectAll('.slot-layer,.node-layer,.badge-layer,.link-layer').remove();
  const layer = scene.selectAll('.btree-layer').data([null]).join('g').attr('class', 'btree-layer');
  drawMultiwayLinks(layer, links, activeKeys);
  drawMultiwayNodes(layer, nodes, treeType, activeKeys, violationKeys, activeStep, previousPositions);
  if (treeType === 'bplus_tree') drawLeafChain(layer, nodes);
  return nextPositions;
}

function drawMultiwayLinks(layer, links, activeKeys) {
  const path = (d) => {
    const sx = d.source.x;
    const sy = d.source.y + B_NODE_HEIGHT / 2;
    const tx = d.target.x;
    const ty = d.target.y - B_NODE_HEIGHT / 2;
    const mid = (sy + ty) / 2;
    return `M${sx},${sy} C${sx},${mid} ${tx},${mid} ${tx},${ty}`;
  };

  layer.selectAll('path.btree-link')
    .data(links, (d) => `${d.source.id}->${d.target.id}`)
    .join('path')
    .attr('class', 'btree-link')
    .attr('fill', 'none')
    .attr('stroke', (d) => multiwayActive(d.source, activeKeys) && multiwayActive(d.target, activeKeys) ? COLORS.linkActive : COLORS.link)
    .attr('stroke-width', (d) => multiwayActive(d.source, activeKeys) && multiwayActive(d.target, activeKeys) ? 4 : 2.2)
    .transition()
    .duration(TRANSITION_MS)
    .attr('d', path);
}

function drawMultiwayNodes(layer, nodes, treeType, activeKeys, violationKeys, activeStep, previousPositions) {
  const groups = layer.selectAll('g.btree-node')
    .data(nodes, (d) => d.id)
    .join(
      (enter) => {
        const g = enter.append('g')
          .attr('class', 'btree-node')
          .attr('transform', (d) => {
            const p = previousPositions.get(d.id) || { x: d.x, y: d.y - 40 };
            return `translate(${p.x},${p.y})`;
          })
          .attr('opacity', 0);
        g.append('rect');
        g.append('text').attr('class', 'btree-kind');
        return g;
      },
      (update) => update,
      (exit) => exit.transition().duration(220).attr('opacity', 0).remove(),
    );

  groups.transition()
    .duration(TRANSITION_MS)
    .ease(d3.easeCubicOut)
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .attr('opacity', 1);

  groups.select('rect')
    .transition()
    .duration(TRANSITION_MS)
    .attr('x', (d) => -d.width / 2)
    .attr('y', -B_NODE_HEIGHT / 2)
    .attr('width', (d) => d.width)
    .attr('height', B_NODE_HEIGHT)
    .attr('rx', 8)
    .attr('fill', (d) => multiwayNodeFill(d, activeKeys, violationKeys))
    .attr('stroke', (d) => multiwayNodeStroke(d, activeKeys, violationKeys))
    .attr('stroke-width', (d) => multiwayActive(d, activeKeys) || nodeKeyViolates(d, violationKeys) ? 3 : 2);

  groups.each(function (d) {
    const g = d3.select(this);
    const keyData = d.keys.map((key, i) => ({ key, i, id: `${d.id}:key:${key}:${i}` }));
    const keyJoin = g.selectAll('g.b-key').data(keyData, (k) => k.id);
    const keyEnter = keyJoin.enter().append('g').attr('class', 'b-key');
    keyEnter.append('line');
    keyEnter.append('text');
    keyJoin.exit().remove();

    g.selectAll('g.b-key')
      .attr('transform', (k) => `translate(${(-d.width / 2) + B_KEY_WIDTH / 2 + k.i * B_KEY_WIDTH},0)`)
      .each(function (k) {
        const kg = d3.select(this);
        kg.select('text')
          .attr('text-anchor', 'middle')
          .attr('dy', '0.35em')
          .attr('fill', activeKeys.has(k.key) ? '#ecfeff' : COLORS.text)
          .attr('font-family', 'var(--font-mono)')
          .attr('font-size', 13)
          .attr('font-weight', 800)
          .text(k.key);
        kg.select('line')
          .attr('x1', B_KEY_WIDTH / 2)
          .attr('y1', -B_NODE_HEIGHT / 2 + 6)
          .attr('x2', B_KEY_WIDTH / 2)
          .attr('y2', B_NODE_HEIGHT / 2 - 6)
          .attr('stroke', k.i < d.keys.length - 1 ? 'rgba(255,255,255,0.18)' : 'transparent');
      });

    const showSplit = activeStep && String(activeStep.step_type || '').includes('split') && multiwayActive(d, activeKeys);
    const label = showSplit ? 'split overflow' : d.leaf ? 'leaf' : 'router';
    g.select('.btree-kind')
      .attr('text-anchor', 'middle')
      .attr('y', B_NODE_HEIGHT / 2 + 18)
      .attr('fill', showSplit ? COLORS.split : COLORS.muted)
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .text(label);
  });
}

function drawLeafChain(layer, nodes) {
  const leaves = nodes.filter((node) => node.leaf).sort((a, b) => a.x - b.x);
  const pairs = d3.pairs(leaves);
  layer.selectAll('path.leaf-chain')
    .data(pairs, (d) => `${d[0].id}->${d[1].id}`)
    .join('path')
    .attr('class', 'leaf-chain')
    .attr('fill', 'none')
    .attr('stroke', COLORS.compare)
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '5 5')
    .attr('marker-end', 'url(#arrowHead)')
    .attr('d', ([a, b]) => {
      const y = a.y + B_NODE_HEIGHT / 2 + 28;
      return `M${a.x + a.width / 2},${y} C${a.x + a.width},${y + 18} ${b.x - b.width},${y + 18} ${b.x - b.width / 2},${y}`;
    });
}

function normalizeBinaryNode(node, id, side, treeType) {
  if (!node) return null;
  const key = node.key ?? node.value ?? node.label ?? id;
  const label = treeType === 'segment_tree' ? node.value : (node.value ?? key);
  const normalized = {
    ...node,
    id,
    key,
    value: node.value ?? key,
    label,
    side,
    children: [],
  };
  const { leftChild, rightChild } = binaryChildrenFrom(node, treeType);
  const left = leftChild
    ? normalizeBinaryNode(leftChild, `${id}.L:${leftChild.key ?? leftChild.value ?? 'node'}`, 'left', treeType)
    : placeholder(`${id}.L:null`, 'left');
  const right = rightChild
    ? normalizeBinaryNode(rightChild, `${id}.R:${rightChild.key ?? rightChild.value ?? 'node'}`, 'right', treeType)
    : placeholder(`${id}.R:null`, 'right');

  if (treeType === 'heap' || treeType === 'segment_tree' || leftChild || rightChild) {
    normalized.children = [left, right].filter(Boolean);
  }
  return normalized;
}

function binaryChildrenFrom(node, treeType) {
  if (node.left || node.right) return { leftChild: node.left || null, rightChild: node.right || null };

  const children = Array.isArray(node.children) ? node.children.filter(Boolean) : [];
  if (children.length === 0) return { leftChild: null, rightChild: null };

  if (treeType === 'heap' || treeType === 'segment_tree') {
    return { leftChild: children[0] || null, rightChild: children[1] || null };
  }

  const parentValue = Number(node.key ?? node.value);
  return children.reduce((slots, child, index) => {
    const childValue = Number(child.key ?? child.value);
    const explicitSide = child.side || child.position;
    if (explicitSide === 'left') slots.leftChild = child;
    else if (explicitSide === 'right') slots.rightChild = child;
    else if (Number.isFinite(parentValue) && Number.isFinite(childValue)) {
      if (childValue < parentValue) slots.leftChild = child;
      else slots.rightChild = child;
    } else if (index === 0) slots.leftChild = child;
    else slots.rightChild = child;
    return slots;
  }, { leftChild: null, rightChild: null });
}

function placeholder(id, side) {
  return { id, key: id, label: '', side, placeholder: true, children: [] };
}

function enforceBinaryDirection(root, nodeGap) {
  root.each((node) => {
    if (!node.parent || node.data.placeholder) return;
    const minOffset = Math.max(nodeGap / Math.max(1.1, node.depth + 0.2), NODE_RADIUS * 1.8);
    if (node.data.side === 'left' && node.x > node.parent.x - minOffset) {
      shiftSubtree(node, node.parent.x - minOffset - node.x);
    }
    if (node.data.side === 'right' && node.x < node.parent.x + minOffset) {
      shiftSubtree(node, node.parent.x + minOffset - node.x);
    }
  });
}

function shiftSubtree(node, dx) {
  node.each((descendant) => {
    descendant.x += dx;
  });
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function normalizeMultiwayNode(node, id) {
  const keys = Array.isArray(node?.keys) ? node.keys : [];
  const children = Array.isArray(node?.children)
    ? node.children.map((child, i) => normalizeMultiwayNode(child, `${id}.${i}:${(child.keys || [i]).join('-')}`))
    : [];
  return {
    ...node,
    id,
    keys,
    leaf: Boolean(node?.leaf || children.length === 0),
    children,
  };
}

function measureMultiwayNode(node) {
  node.width = Math.max(58, node.keys.length * B_KEY_WIDTH);
  if (!node.children?.length) {
    node.subtreeWidth = node.width + 44;
    return node;
  }
  node.children.forEach(measureMultiwayNode);
  const childWidth = d3.sum(node.children, (child) => child.subtreeWidth);
  node.subtreeWidth = Math.max(node.width + 44, childWidth);
  return node;
}

function assignMultiwayPositions(node, left, depth) {
  node.x = left + node.subtreeWidth / 2;
  node.y = depth * 104;
  let cursor = left;
  node.children?.forEach((child) => {
    assignMultiwayPositions(child, cursor, depth + 1);
    cursor += child.subtreeWidth;
  });
}

function flattenMultiway(node) {
  return [node, ...(node.children || []).flatMap(flattenMultiway)];
}

function collectViolationKeys(violations) {
  const keys = new Set();
  violations.forEach((violation) => {
    ['node', 'parent', 'child', 'key'].forEach((field) => {
      if (violation?.[field] !== undefined) keys.add(violation[field]);
    });
    (violation?.affected_nodes || []).forEach((key) => keys.add(key));
    (violation?.keys || []).forEach((key) => keys.add(key));
  });
  return keys;
}

function normalizeKeyList(value) {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (typeof item === 'number' || typeof item === 'string') return [item];
    if (Array.isArray(item?.keys)) return item.keys;
    if (item?.key !== undefined) return [item.key];
    return [];
  });
}

function linkIsActive(link, activeKeys) {
  return activeKeys.has(link.source.data.key) && activeKeys.has(link.target.data.key);
}

function nodeFill(node, treeType, activeKeys, violationKeys) {
  if (violationKeys.has(node.key)) return COLORS.violation;
  if (activeKeys.has(node.key)) return COLORS.compare;
  if (treeType === 'red_black') return String(node.color).toUpperCase() === 'RED' ? COLORS.red : COLORS.black;
  if (treeType === 'heap') return COLORS.heap;
  if (treeType === 'segment_tree') return COLORS.segment;
  return COLORS.normal;
}

function nodeStroke(node, treeType, activeKeys, violationKeys) {
  if (violationKeys.has(node.key)) return '#fecdd3';
  if (activeKeys.has(node.key)) return '#cffafe';
  if (treeType === 'red_black') return String(node.color).toUpperCase() === 'RED' ? COLORS.redStroke : COLORS.blackStroke;
  return COLORS.normalStroke;
}

function labelsForNode(d, treeType, activeStep, activeKeys, violationKeys) {
  const labels = [];
  if (treeType === 'avl' && d.data.balance_factor !== undefined) {
    const bf = Number(d.data.balance_factor);
    labels.push({
      id: `${d.data.id}:bf`,
      text: `BF ${bf}`,
      x: d.x,
      y: d.y - NODE_RADIUS - 17,
      fill: Math.abs(bf) > 1 ? 'rgba(251,113,133,0.18)' : 'rgba(245,158,11,0.16)',
      stroke: Math.abs(bf) > 1 ? COLORS.violation : 'rgba(245,158,11,0.45)',
      color: Math.abs(bf) > 1 ? '#fecdd3' : '#fde68a',
    });
  }
  if (treeType === 'avl' && d.data.height !== undefined) {
    labels.push({
      id: `${d.data.id}:h`,
      text: `h=${d.data.height}`,
      x: d.x,
      y: d.y + NODE_RADIUS + 17,
      fill: 'rgba(148,163,184,0.12)',
      stroke: 'rgba(148,163,184,0.24)',
      color: COLORS.muted,
    });
  }
  if (treeType === 'red_black') {
    labels.push({
      id: `${d.data.id}:color`,
      text: String(d.data.color).toUpperCase() === 'RED' ? 'RED' : 'BLACK',
      x: d.x,
      y: d.y - NODE_RADIUS - 17,
      fill: String(d.data.color).toUpperCase() === 'RED' ? 'rgba(239,68,68,0.18)' : 'rgba(203,213,225,0.14)',
      stroke: String(d.data.color).toUpperCase() === 'RED' ? COLORS.redStroke : COLORS.blackStroke,
      color: String(d.data.color).toUpperCase() === 'RED' ? '#fecaca' : '#e2e8f0',
    });
    if (d.data.black_height_from_root !== undefined) {
      labels.push({
        id: `${d.data.id}:bh`,
        text: `bh ${d.data.black_height_from_root}`,
        x: d.x,
        y: d.y + NODE_RADIUS + 17,
        fill: 'rgba(167,139,250,0.14)',
        stroke: 'rgba(167,139,250,0.42)',
        color: '#ddd6fe',
      });
    }
  }
  if (treeType === 'heap' && d.data.index !== undefined) {
    labels.push({
      id: `${d.data.id}:index`,
      text: `[${d.data.index}]`,
      x: d.x,
      y: d.y - NODE_RADIUS - 17,
      fill: 'rgba(34,211,238,0.12)',
      stroke: 'rgba(34,211,238,0.38)',
      color: '#a5f3fc',
    });
  }
  if (treeType === 'segment_tree' && d.data.range) {
    labels.push({
      id: `${d.data.id}:range`,
      text: `[${d.data.range[0]},${d.data.range[1]}]`,
      x: d.x,
      y: d.y - NODE_RADIUS - 17,
      fill: 'rgba(167,139,250,0.14)',
      stroke: 'rgba(167,139,250,0.42)',
      color: '#ddd6fe',
    });
  }
  if (activeKeys.has(d.data.key) && activeStep?.step_type) {
    labels.push({
      id: `${d.data.id}:step`,
      text: String(activeStep.step_type).toUpperCase(),
      x: d.x,
      y: d.y - NODE_RADIUS - 41,
      fill: 'rgba(34,211,238,0.16)',
      stroke: 'rgba(34,211,238,0.55)',
      color: '#ecfeff',
    });
  }
  if (violationKeys.has(d.data.key)) {
    labels.push({
      id: `${d.data.id}:violation`,
      text: 'CHECK',
      x: d.x,
      y: d.y - NODE_RADIUS - 41,
      fill: 'rgba(251,113,133,0.2)',
      stroke: COLORS.violation,
      color: '#ffe4e6',
    });
  }
  return labels;
}

function tooltipForNode(d, treeType) {
  const parts = [`key: ${d.data.key}`, `depth: ${d.depth}`];
  if (d.data.side) parts.push(`${d.data.side} child`);
  if (treeType === 'avl' && d.data.balance_factor !== undefined) parts.push(`balance factor: ${d.data.balance_factor}`);
  if (treeType === 'red_black') parts.push(`color: ${d.data.color || 'BLACK'}`);
  if (treeType === 'heap' && d.data.index !== undefined) parts.push(`array index: ${d.data.index}`);
  return parts.join('\n');
}

function textWidth(value) {
  return Math.max(1, String(value ?? '').length) * 10;
}

function isRotationStep(step) {
  return /rotate|rotation|LL|RR|LR|RL/i.test(`${step?.step_type || ''} ${step?.description || ''}`);
}

function rotationLabel(step) {
  const text = `${step?.description || ''} ${step?.why || ''}`;
  const match = text.match(/\b(LL|RR|LR|RL)\b/i);
  if (match) return `${match[1].toUpperCase()} rotation`;
  if (/left rotate|rotate left/i.test(text)) return 'left rotate';
  if (/right rotate|rotate right/i.test(text)) return 'right rotate';
  return 'rotation';
}

function buildComparison(step, operationKey, treeType) {
  if (step?.description) {
    return {
      kind: step.step_type || 'info',
      label: String(step.step_type || 'step').replaceAll('_', ' '),
      detail: step.description,
    };
  }
  if (operationKey !== null && operationKey !== '' && ['avl', 'red_black'].includes(treeType)) {
    return {
      kind: 'compare',
      label: 'BST decision path',
      detail: `Compare ${operationKey} with each visited node: smaller moves left, larger moves right.`,
    };
  }
  return null;
}

function multiwayActive(node, activeKeys) {
  return node.keys.some((key) => activeKeys.has(key));
}

function nodeKeyViolates(node, violationKeys) {
  return node.keys.some((key) => violationKeys.has(key));
}

function multiwayNodeFill(node, activeKeys, violationKeys) {
  if (nodeKeyViolates(node, violationKeys)) return 'rgba(251,113,133,0.22)';
  if (multiwayActive(node, activeKeys)) return 'rgba(34,211,238,0.22)';
  return 'rgba(51,65,85,0.92)';
}

function multiwayNodeStroke(node, activeKeys, violationKeys) {
  if (nodeKeyViolates(node, violationKeys)) return COLORS.violation;
  if (multiwayActive(node, activeKeys)) return COLORS.linkActive;
  return COLORS.normalStroke;
}

function formatTreeName(type) {
  const names = {
    avl: 'AVL Tree',
    red_black: 'Red-Black Tree',
    heap: 'Binary Heap',
    segment_tree: 'Segment Tree',
    btree: 'B-Tree',
    bplus_tree: 'B+ Tree',
  };
  return names[type] || type;
}
