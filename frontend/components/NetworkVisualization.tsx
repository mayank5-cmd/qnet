import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useNetworkStore } from '@/lib/store';

interface NetworkVisualizationProps {
  width?: number;
  height?: number;
}

export function NetworkVisualization({ width = 800, height = 600 }: NetworkVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const { nodes, links } = useNetworkStore();
  
  useEffect(() => {
    if (!svgRef.current || nodes.size === 0) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const simulation = d3.forceSimulation(Array.from(nodes.values()) as any)
      .force('link', d3.forceLink(Array.from(links.values())).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20));
    
    const linkGroup = svg.append('g').attr('class', 'links');
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    
    const link = linkGroup.selectAll('line')
      .data(Array.from(links.values()))
      .join('line')
      .attr('stroke', (d: any) => d.isQuantum ? '#00ff88' : '#888')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6);
    
    const node = nodeGroup.selectAll('g')
      .data(Array.from(nodes.values()))
      .join('g')
      .call(d3.drag<any, any>()
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
      .attr('r', 12)
      .attr('fill', (d: any) => {
        if (d.type === 'router') return '#ff6b6b';
        if (d.type === 'repeater') return '#4ecdc4';
        return '#45b7d1';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);
    
    node.append('text')
      .text((d: any) => d.id.replace('node_', ''))
      .attr('x', 15)
      .attr('y', 5)
      .attr('font-size', '10px')
      .attr('fill', '#fff');
    
    node.append('circle')
      .attr('r', 4)
      .attr('fill', (d: any) => {
        const fidelity = d.fidelity || 1;
        if (fidelity > 0.9) return '#00ff88';
        if (fidelity > 0.7) return '#ffff00';
        return '#ff0000';
      })
      .attr('class', 'fidelity-indicator');
    
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });
    
    return () => {
      simulation.stop();
    };
  }, [nodes, links, width, height]);
  
  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ background: '#0a0a1a' }}
    />
  );
}
