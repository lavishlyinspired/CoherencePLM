import { Node, Relationship } from "@neo4j-nvl/base";
import { RecordShape } from "neo4j-driver";

const colorPalette = [
  "#FFDF81", "#C990C0", "#F79767", "#56C7E4", "#F16767",
  "#D8C7AE", "#8DCC93", "#ECB4C9", "#4D8DDA", "#FFC354",
];

const labelColorMap = new Map<string, string>();
let colorIndex = 0;

export const getUniqueColorForLabel = (label: string): string => {
  if (!labelColorMap.has(label)) {
    const color = colorPalette[colorIndex % colorPalette.length];
    labelColorMap.set(label, color);
    colorIndex++;
  }
  return labelColorMap.get(label)!;
};

// Optimized display name helper
export const getNodeDisplayName = (
  properties: Record<string, any> | null,
  labels: string[] = [],
  fallbackId?: string
): string => {
  if (properties && typeof properties === 'object') {
    // Quick checks for common property names
    const quickChecks = ['name', 'title', 'label', 'id', 'username'];
    for (const key of quickChecks) {
      const value = properties[key];
      if (value != null && value !== '') {
        return String(value);
      }
    }

    // Only do full object iteration if necessary
    for (const [key, value] of Object.entries(properties)) {
      if (value != null && value !== '' && !key.startsWith('_')) {
        const stringValue = String(value);
        if (stringValue.trim().length > 0 && stringValue.length < 50) {
          return stringValue;
        }
      }
    }
  }

  return labels[0] || fallbackId?.slice(0, 8) || 'Node';
};

// Optimized graph styling with performance in mind
export const styleGraph = (
  data: {
    nodes: Node[];
    relationships: Relationship[];
    recordObjectMap: Map<string, RecordShape>;
  },
  label = ""
): {
  styledNodes: Node[];
  styledRelationships: Relationship[];
  positions: { id: string; x: number; y: number }[];
} => {
  const positions: { id: string; x: number; y: number }[] = [];
  const isLargeGraph = data.nodes.length > 200;

  // Batch process nodes for better performance
  const styledNodes: Node[] = data.nodes.map((node, index) => {
    const originalNode = data.recordObjectMap.get(node.id);
    const properties = originalNode?.properties || {};
    const nodeLabels = originalNode?.labels || [];
    const nodeLabel = nodeLabels[0] || "Node";
    
    // Use simpler display names for large graphs
    const displayName = isLargeGraph 
      ? getNodeDisplayName(properties, nodeLabels, node.id)
      : getNodeDisplayName(properties, nodeLabels, node.id);

    const newNode: Node = {
      ...node,
      color: getUniqueColorForLabel(nodeLabel),
      captions: isLargeGraph ? [] : [{ value: displayName }], // No captions for large graphs
      size: 25, // Smaller default size for large graphs
    };

    // Only compute complex styling for smaller graphs
    if (!isLargeGraph && properties.priority !== undefined) {
      const priority = properties.priority.toNumber 
        ? properties.priority.toNumber()
        : properties.priority;
      newNode.size = Math.max(20, 60 - (priority * 10));
    }

    return newNode;
  });

  // Simplify relationships for large graphs
  const styledRelationships = data.relationships.map((rel) => {
    const originalRelationship = data.recordObjectMap.get(rel.id);
    const relType = originalRelationship?.type || "RELATED_TO";
    
    return {
      ...rel,
      captions: isLargeGraph ? [] : [{ value: relType }], // No captions for large graphs
    };
  });

  return { styledNodes, styledRelationships, positions };
};