import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const COLORS = {
  high: '#10b981',
  medium: '#f59e0b',
  low: '#ef4444',
  none: '#334155',
  link: 'rgba(148, 163, 184, 0.35)',
  bg: '#0f172a',
};

export default function ConceptGraph({ conceptData, width = 520, height = 400 }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !conceptData) return;
    const { nodes, edges } = conceptData;
    if (!nodes?.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id((d) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(32));

    const zoom = d3.zoom()
      .scaleExtent([0.25, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', COLORS.link)
      .attr('stroke-width', (d) => Math.max(0.5, (d.weight || 0.5) * 2.5))
      .attr('stroke-opacity', 0.6);

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    node.append('circle')
      .attr('r', (d) => Math.max(6, Math.min(20, 8 + (d.attempts || 0) * 2)))
      .attr('fill', (d) => {
        const m = d.mastery ?? 0;
        if (m >= 0.7) return COLORS.high;
        if (m >= 0.4) return COLORS.medium;
        if (d.attempts > 0) return COLORS.low;
        return COLORS.none;
      })
      .attr('stroke', (d) => {
        const m = d.mastery ?? 0;
        if (m >= 0.7) return '#047857';
        if (m >= 0.4) return '#b45309';
        if (d.attempts > 0) return '#dc2626';
        return '#475569';
      })
      .attr('stroke-width', 2);

    node.append('text')
      .text((d) => d.name || d.id)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => Math.max(6, Math.min(20, 8 + (d.attempts || 0) * 2)) + 14)
      .attr('fill', '#f8fafc')
      .attr('font-size', (d) => d.is_hub ? 11 : 9)
      .attr('font-weight', (d) => d.is_hub ? 800 : 500)
      .attr('font-family', 'var(--font-sans)')
      .style('pointer-events', 'none');

    node.append('title')
      .text((d) => `${d.name || d.id}\nMastery: ${Math.round((d.mastery ?? 0) * 100)}%\nAttempts: ${d.attempts || 0}\nMistakes: ${d.mistakes || 0}`);

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [conceptData, width, height]);

  if (!conceptData?.nodes?.length) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <h3>Concept Graph</h3>
      <div style={{
        background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)',
        overflow: 'hidden', position: 'relative',
      }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height, display: 'block' }}
        />
        <div style={{
          position: 'absolute', bottom: 8, right: 10,
          display: 'flex', gap: 12, fontSize: '0.7rem', color: 'var(--text-muted)',
          pointerEvents: 'none',
        }}>
          <span><span style={{ color: COLORS.high }}>●</span> Mastered</span>
          <span><span style={{ color: COLORS.medium }}>●</span> Learning</span>
          <span><span style={{ color: COLORS.low }}>●</span> Weak</span>
          <span><span style={{ color: COLORS.none }}>●</span> Unseen</span>
        </div>
      </div>
    </div>
  );
}
