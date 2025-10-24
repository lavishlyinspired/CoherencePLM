import { Node, Relationship } from "@neo4j-nvl/base";

// Node filtering utilities
export const filterNodesByLabel = (
  nodes: Node[],
  recordObjectMap: Map<string, any>,
  label: string
): Node[] => {
  return nodes.filter((node) => {
    const originalNode = recordObjectMap.get(node.id);
    return originalNode?.labels?.includes(label);
  });
};

export const filterNodesByProperty = (
  nodes: Node[],
  recordObjectMap: Map<string, any>,
  propertyKey: string,
  propertyValue: any
): Node[] => {
  return nodes.filter((node) => {
    const originalNode = recordObjectMap.get(node.id);
    return originalNode?.properties?.[propertyKey] === propertyValue;
  });
};

// Search utilities
export const searchNodes = (
  nodes: Node[],
  recordObjectMap: Map<string, any>,
  query: string
): Node[] => {
  const searchLower = query.toLowerCase();
  return nodes.filter((node) => {
    const originalNode = recordObjectMap.get(node.id);
    
    // Search in captions
    const captionMatch = node.captions?.some((caption) =>
      caption.value?.toLowerCase().includes(searchLower)
    );

    // Search in all properties
    const propertyMatch = Object.values(originalNode?.properties || {}).some(
      (value) => String(value).toLowerCase().includes(searchLower)
    );

    return captionMatch || propertyMatch;
  });
};

// Graph statistics
export interface GraphStats {
  totalNodes: number;
  totalRelationships: number;
  nodesByType: Record<string, number>;
  relationshipsByType: Record<string, number>;
  averageDegree: number;
  isolatedNodes: number;
}

export const calculateGraphStats = (
  nodes: Node[],
  relationships: Relationship[],
  recordObjectMap: Map<string, any>
): GraphStats => {
  const nodesByType: Record<string, number> = {};
  const relationshipsByType: Record<string, number> = {};
  const nodeDegrees = new Map<string, number>();

  // Count nodes by type
  nodes.forEach((node) => {
    const originalNode = recordObjectMap.get(node.id);
    const type = originalNode?.labels?.[0] || "Unknown";
    nodesByType[type] = (nodesByType[type] || 0) + 1;
    nodeDegrees.set(node.id, 0);
  });

  // Count relationships by type and node degrees
  relationships.forEach((rel) => {
    const originalRel = recordObjectMap.get(rel.id);
    const type = originalRel?.type || "Unknown";
    relationshipsByType[type] = (relationshipsByType[type] || 0) + 1;

    // Update node degrees
    nodeDegrees.set(rel.from, (nodeDegrees.get(rel.from) || 0) + 1);
    nodeDegrees.set(rel.to, (nodeDegrees.get(rel.to) || 0) + 1);
  });

  // Calculate average degree
  const totalDegree = Array.from(nodeDegrees.values()).reduce((sum, deg) => sum + deg, 0);
  const averageDegree = nodes.length > 0 ? totalDegree / nodes.length : 0;

  // Count isolated nodes
  const isolatedNodes = Array.from(nodeDegrees.values()).filter((deg) => deg === 0).length;

  return {
    totalNodes: nodes.length,
    totalRelationships: relationships.length,
    nodesByType,
    relationshipsByType,
    averageDegree: Math.round(averageDegree * 100) / 100,
    isolatedNodes,
  };
};

// Export utilities
export const exportToCSV = (
  nodes: Node[],
  relationships: Relationship[],
  recordObjectMap: Map<string, any>
): string => {
  // Export nodes
  let csv = "Node Type,Node ID,Properties\n";
  nodes.forEach((node) => {
    const originalNode = recordObjectMap.get(node.id);
    const type = originalNode?.labels?.[0] || "Unknown";
    const props = JSON.stringify(originalNode?.properties || {});
    csv += `${type},${node.id},"${props}"\n`;
  });

  csv += "\n\nRelationship Type,From,To,Properties\n";
  relationships.forEach((rel) => {
    const originalRel = recordObjectMap.get(rel.id);
    const type = originalRel?.type || "Unknown";
    const props = JSON.stringify(originalRel?.properties || {});
    csv += `${type},${rel.from},${rel.to},"${props}"\n`;
  });

  return csv;
};

export const exportToJSON = (
  nodes: Node[],
  relationships: Relationship[],
  recordObjectMap: Map<string, any>
): string => {
  const data = {
    nodes: nodes.map((node) => {
      const originalNode = recordObjectMap.get(node.id);
      return {
        id: node.id,
        labels: originalNode?.labels || [],
        properties: originalNode?.properties || {},
      };
    }),
    relationships: relationships.map((rel) => {
      const originalRel = recordObjectMap.get(rel.id);
      return {
        id: rel.id,
        type: originalRel?.type || "Unknown",
        from: rel.from,
        to: rel.to,
        properties: originalRel?.properties || {},
      };
    }),
  };

  return JSON.stringify(data, null, 2);
};

// Layout utilities
export const applyCircularLayout = (
  nodes: Node[],
  centerX = 0,
  centerY = 0,
  radius = 300
): Array<{ id: string; x: number; y: number }> => {
  const positions: Array<{ id: string; x: number; y: number }> = [];
  const angleStep = (2 * Math.PI) / nodes.length;

  nodes.forEach((node, index) => {
    const angle = index * angleStep;
    positions.push({
      id: node.id,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    });
  });

  return positions;
};

export const applyGridLayout = (
  nodes: Node[],
  startX = 0,
  startY = 0,
  spacing = 150
): Array<{ id: string; x: number; y: number }> => {
  const positions: Array<{ id: string; x: number; y: number }> = [];
  const columns = Math.ceil(Math.sqrt(nodes.length));

  nodes.forEach((node, index) => {
    const row = Math.floor(index / columns);
    const col = index % columns;
    positions.push({
      id: node.id,
      x: startX + col * spacing,
      y: startY + row * spacing,
    });
  });

  return positions;
};

// Node comparison
export const compareNodes = (
  node1: any,
  node2: any
): {
  common: Record<string, any>;
  different: Record<string, { node1: any; node2: any }>;
  unique1: Record<string, any>;
  unique2: Record<string, any>;
} => {
  const props1 = node1?.properties || {};
  const props2 = node2?.properties || {};

  const common: Record<string, any> = {};
  const different: Record<string, { node1: any; node2: any }> = {};
  const unique1: Record<string, any> = {};
  const unique2: Record<string, any> = {};

  // Find common and different properties
  Object.keys(props1).forEach((key) => {
    if (key in props2) {
      if (props1[key] === props2[key]) {
        common[key] = props1[key];
      } else {
        different[key] = { node1: props1[key], node2: props2[key] };
      }
    } else {
      unique1[key] = props1[key];
    }
  });

  // Find properties unique to node2
  Object.keys(props2).forEach((key) => {
    if (!(key in props1)) {
      unique2[key] = props2[key];
    }
  });

  return { common, different, unique1, unique2 };
};



export const getNodeDisplayName = (
  node: Node,
  recordObjectMap: Map<string, any>
): string => {
  
  const originalNode = recordObjectMap.get(node.id);
  const props = originalNode?.properties || {};
  
  if (props.name) return props.name;
  if (props.title) return props.title;
  if (props.label) return props.label;
  if (props.id) return props.id;

  // Join all labels if multiple exist
  if (originalNode?.labels?.length) return originalNode.labels.join(", ");

  return "Unnamed Node";
};
