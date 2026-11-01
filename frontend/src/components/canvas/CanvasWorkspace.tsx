import React, { useCallback, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes } from './CustomNodes';

interface CanvasWorkspaceProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  onNodeClick: (node: Node) => void;
  onDropItem: (type: string, data: any, position: { x: number; y: number }) => void;
}

export const CanvasWorkspace: React.FC<CanvasWorkspaceProps> = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onDropItem,
}) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const rawData = event.dataTransfer.getData('application/evalforge-node');
      if (!rawData || !reactFlowWrapper.current) return;

      try {
        const item = JSON.parse(rawData);
        const bounds = reactFlowWrapper.current.getBoundingClientRect();
        const position = {
          x: event.clientX - bounds.left - 100,
          y: event.clientY - bounds.top - 40,
        };
        onDropItem(item.type, item.data, position);
      } catch (e) {
        console.error('Failed to parse dropped node', e);
      }
    },
    [onDropItem]
  );

  return (
    <div ref={reactFlowWrapper} className="w-full h-full relative bg-[#F1F5F9]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick(node)}
        onDragOver={onDragOver}
        onDrop={onDrop}
        fitView
        deleteKeyCode={['Backspace', 'Delete']}
        defaultEdgeOptions={{
          animated: true,
          style: { stroke: '#2563EB', strokeWidth: 2 },
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#CBD5E1" />
        <Controls
          className="!bg-white !border !border-[#E2E8F0] !shadow-sm !rounded-md"
          showInteractive={false}
        />
        <MiniMap
          className="!bg-white !border !border-[#E2E8F0] !shadow-sm !rounded-md"
          nodeColor={(n) => {
            if (n.type === 'model') return '#2563EB';
            if (n.type === 'dataset') return '#16A34A';
            if (n.type === 'benchmark') return '#D97706';
            return '#7C3AED';
          }}
          maskColor="rgba(241, 245, 249, 0.7)"
        />
      </ReactFlow>
    </div>
  );
};
