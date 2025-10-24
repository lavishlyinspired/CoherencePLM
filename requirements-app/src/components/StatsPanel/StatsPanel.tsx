// StatsPanel.tsx
import React, { useState } from "react";
import type { Node, Relationship } from "@neo4j-nvl/base";

const DEFAULT_NODE_TYPES = [
  "TestCase",
  "Requirement",
  "Priority",
  "Source",
  "BusinessNeed",
  "Project",
  "Risk",
  "RiskAssessment",
];

interface StatsPanelProps {
  stats: any;
  selectedNodeCount: number;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats, selectedNodeCount }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        position: "absolute",
        bottom: "20px",
        left: "20px",
        backgroundColor: "white",
        padding: "16px",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
        zIndex: 100,
        minWidth: "250px",
      }}
    >
      <div style={{ display: "flex", gap: "20px", marginBottom: expanded ? "12px" : "0" }}>
        <div>
          <div style={{ fontSize: "12px", color: "#6b7280" }}>Nodes</div>
          <div style={{ fontSize: "20px", fontWeight: "600", color: "#374151" }}>
            {stats.totalNodes}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "12px", color: "#6b7280" }}>Relationships</div>
          <div style={{ fontSize: "20px", fontWeight: "600", color: "#374151" }}>
            {stats.totalRelationships}
          </div>
        </div>
        {selectedNodeCount > 0 && (
          <div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>Selected</div>
            <div style={{ fontSize: "20px", fontWeight: "600", color: "#3b82f6" }}>
              {selectedNodeCount}
            </div>
          </div>
        )}
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            padding: "0",
          }}
        >
          {expanded ? "▼" : "▶"}
        </button>
      </div>

      {expanded && (
        <div style={{ borderTop: "1px solid #e5e7eb", paddingTop: "12px" }}>
          <div style={{ fontSize: "14px", fontWeight: "600", marginBottom: "8px" }}>Node Types</div>
          {DEFAULT_NODE_TYPES.map((type) => (
            <div
              key={type}
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "12px",
                padding: "4px 0",
              }}
            >
              <span style={{ color: "#6b7280" }}>{type}</span>
              <span style={{ fontWeight: "600" }}>{stats.nodesByType[type] || 0}</span>
            </div>
          ))}
          <div style={{ marginTop: "12px", fontSize: "12px", color: "#6b7280" }}>
            <div>Avg. Degree: {stats.averageDegree}</div>
            <div>Isolated Nodes: {stats.isolatedNodes}</div>
          </div>
        </div>
      )}
    </div>
  );
};
