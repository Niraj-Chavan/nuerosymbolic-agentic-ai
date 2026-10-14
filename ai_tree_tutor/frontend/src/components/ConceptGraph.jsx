import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const COLORS = {
  high: '#10b981',
  medium: '#f59e0b',
  low: '#ef4444',
  none: '#334155',
  link: 'rgba(148, 163, 184, 0.35)',
  bg: '#0f172a',
};

export default function ConceptGraph({ conceptData }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const svgRef = useRef(null);

  // Dynamic dimensions based on expanded state
  const width = isExpanded ? 1200 : 800;
  const height = isExpanded ? 800 : 280;

  useEffect(() => {
    if (!svgRef.current || !conceptData) return;
    const { nodes, edges } = conceptData;
    if (!nodes?.length) return;

    // Map backend 'from'/'to' to d3 'source'/'target'
    const mappedEdges = edges.map(e => ({ ...e, source: e.from, target: e.to }));

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Adjust forces slightly for the size
    const chargeStrength = isExpanded ? -350 : -220;
    const linkDistance = isExpanded ? 130 : 90;
    const centerForce = d3.forceCenter(width / 2, height / 2);

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(mappedEdges).id((d) => d.id).distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', centerForce)
      .force('collision', d3.forceCollide().radius(isExpanded ? 36 : 28));

    const zoom = d3.zoom()
      .scaleExtent([0.25, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    // Initial scale and translate for nice positioning
    svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));

    const link = g.append('g')
      .selectAll('line')
      .data(mappedEdges)
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
      .attr('r', (d) => {
        const base = isExpanded ? 12 : 8;
        return Math.max(base, Math.min(base * 2.5, base + (d.attempts || 0) * 1.5));
      })
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
      .attr('dy', (d) => {
        const base = isExpanded ? 12 : 8;
        const radius = Math.max(base, Math.min(base * 2.5, base + (d.attempts || 0) * 1.5));
        return radius + (isExpanded ? 16 : 12);
      })
      .attr('fill', '#f8fafc')
      .attr('font-size', (d) => (d.is_hub ? (isExpanded ? 12 : 10) : (isExpanded ? 10 : 8)))
      .attr('font-weight', (d) => (d.is_hub ? 800 : 500))
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
  }, [conceptData, isExpanded, width, height]);

  // Handle keyboard Escape to close modal
  useEffect(() => {
    if (!isExpanded) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsExpanded(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isExpanded]);

  if (!conceptData?.nodes?.length) return null;

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const graphContent = (
    <div style={{
      background: 'var(--bg-glass)',
      borderRadius: 'var(--radius-sm)',
      overflow: 'hidden',
      position: 'relative',
      border: '1px solid var(--border-glass)',
      height: isExpanded ? 'calc(100% - 60px)' : height,
      display: 'flex',
      flexDirection: 'column',
    }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: '100%', display: 'block', flex: 1 }}
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
  );

  if (isExpanded) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        backdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 40px',
        boxSizing: 'border-box',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem', color: 'white' }}>Concept Dependency Graph</h2>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Drag nodes to rearrange. Use scroll wheel or trackpad to zoom and pan. Press <kbd style={{ background: '#334155', padding: '2px 4px', borderRadius: 4 }}>Esc</kbd> to exit.
            </p>
          </div>
          <button
            onClick={handleToggleExpand}
            style={{
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '8px 16px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => e.target.style.background = '#dc2626'}
            onMouseOut={(e) => e.target.style.background = '#ef4444'}
          >
            Close View
          </button>
        </div>
        {graphContent}
      </div>
    );
  }

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-tertiary)' }}>
          Concept Graph
        </h3>
        <button
          onClick={handleToggleExpand}
          style={{
            background: 'rgba(99, 102, 241, 0.1)',
            color: 'var(--accent-primary)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            borderRadius: 'var(--radius-sm)',
            padding: '3px 8px',
            cursor: 'pointer',
            fontSize: '0.72rem',
            fontWeight: 600,
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => {
            e.target.style.background = 'rgba(99, 102, 241, 0.2)';
            e.target.style.color = 'white';
          }}
          onMouseOut={(e) => {
            e.target.style.background = 'rgba(99, 102, 241, 0.1)';
            e.target.style.color = 'var(--accent-primary)';
          }}
        >
          🔍 Expand Graph
        </button>
      </div>
      {graphContent}
    </div>
  );
}
