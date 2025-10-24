import React, { useEffect, useRef, useState, ReactNode } from "react";
import { InteractiveNvlWrapper } from "@neo4j-nvl/react";
import NVL, { Node, NvlOptions, Relationship } from "@neo4j-nvl/base";
import { connect } from "./connections";
import { styleGraph } from "./styling";

interface ModalProps {
  label: string;
  onClose?: () => void;
  children?: ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ label, onClose, children }) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [renderer, setRenderer] = useState<NvlOptions["renderer"]>("webgl");
  const nvlRef = useRef<NVL | null>(null);

  useEffect(() => {
    setRenderer("webgl");
    setNodes([]);
    setRelationships([]);

    const query = `MATCH (a:$($label))-[r]-(b) RETURN a, r, b LIMIT 10000`;
    connect(query, { label })
      .then((result) => {
        if (!result) return;

        const { styledNodes, styledRelationships, positions } = styleGraph(result, label);
        setNodes(styledNodes);
        setRelationships(styledRelationships);

        setTimeout(() => {
          nvlRef.current?.setNodePositions(positions, true);
        });
      })
      .catch((err) => {
        console.log(err);
      });
  }, [label]);

  return (
    <div
      style={{
        backdropFilter: `blur(3px)`,
        borderRadius: "16px",
        border: `2px solid black`,
        width: 800,
        height: 800,
        margin: 10,
        position: "fixed",
        top: `50%`,
        left: `50%`,
        transform: `translate(-50%, -50%)`,
        overflow: "hidden",
        boxShadow: "0 0 10px 10px lightgrey",
        background: "radial-gradient(circle, rgba(255, 255, 255, 0.75), lightgrey)",
        display: "flex",
        flexDirection: "column",
        zIndex: 1000,
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          background: "red",
          color: "white",
          border: "none",
          borderRadius: 4,
          padding: "4px 8px",
          cursor: "pointer",
          zIndex: 1001,
        }}
      >
        ✖
      </button>

      {/* Render children (e.g., PropertiesDialog) */}
      {children}

      {/* NVL Graph */}
      <InteractiveNvlWrapper
        ref={nvlRef}
        nvlOptions={{ renderer, initialZoom: 0.1 }}
        nodes={nodes}
        rels={relationships}
        mouseEventCallbacks={{
          onZoom: true,
          onPan: true,
        }}
        nvlCallbacks={{
          onLayoutDone: () => {
            setRenderer("canvas");
          },
        }}
        style={{ flex: 1 }}
      />
    </div>
  );
};
