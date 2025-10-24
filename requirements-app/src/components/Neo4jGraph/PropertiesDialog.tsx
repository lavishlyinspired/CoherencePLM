import React, { useState, useEffect } from "react";
import { Node } from "@neo4j-nvl/base";
import { connect } from "./connections";
import { getUniqueColorForLabel } from "./styling";
import { requirementsAPI } from '../../services/api';

interface PropertiesPanelProps {
  node: Node | null;
  nodeProperties: Record<string, any>;
  displayName?: string;
  onClose: () => void;
  onSave?: (properties: Record<string, any>) => void;
  onRegenerate?: (result: any) => void;
  threadId?: string;
  onNodeUpdate?: (nodeId: string, updatedProperties: Record<string, any>) => void;
  projectStatus?: any; // Add this to access requirements and risks data
}
export const PropertiesDialog: React.FC<PropertiesPanelProps> = ({
  node,
  nodeProperties,
  displayName,
  onClose,
  onSave,
  onRegenerate,
  threadId,
  onNodeUpdate,
  projectStatus, // Add this
}) => {
  const [activeTab, setActiveTab] = useState<"edit" | "relationships">("edit");
  const [isEditing, setIsEditing] = useState(false);
  const [editedProperties, setEditedProperties] = useState<Record<string, any>>({});
  const [relationships, setRelationships] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [message, setMessage] = useState('');
  const [resizing, setResizing] = useState(false);
  const [dialogWidth, setDialogWidth] = useState(380);

  useEffect(() => {
    if (!threadId && node) {
      console.warn('⚠️ No threadId provided for PropertiesDialog. Regeneration features may not work.');
    }
  }, [threadId, node]);

  useEffect(() => {
    setEditedProperties(nodeProperties);
  }, [nodeProperties]);

  useEffect(() => {
    if (!node) return;

 
      loadRelationships();

  }, [node, activeTab]);

  // Load relationships
  const loadRelationships = async () => {
    if (!node) return;
    setLoading(true);
    try {
      const query = `
        MATCH (n)-[r]-(other)
        WHERE elementId(n) = $nodeId
        WITH DISTINCT r, other, CASE WHEN startNode(r) = n THEN true ELSE false END as isOutgoing
        RETURN 
          type(r) as relationshipType,
          isOutgoing,
          other,
          labels(other) as otherLabels,
          elementId(other) as otherId,
          properties(other) as otherProperties,
          elementId(r) as relId
        LIMIT 100
      `;
      const result = await connect(query, { nodeId: node.id });
      
      if (result?.rawRecords) {
        const relMap = new Map();
        result.rawRecords.forEach((record: any) => {
          const relationshipType = record.relationshipType || "RELATED";
          const relId = record.relId || `${record.relationshipType}-${record.otherId}`;
          const isOutgoing = Boolean(record.isOutgoing);
          const otherNode = record.other || record;
          const otherLabels = record.otherLabels || otherNode?.labels || [];
          const otherId = record.otherId || otherNode?.elementId || otherNode?.id;
          const otherProperties = record.otherProperties || otherNode?.properties || {};
          
          if (!relMap.has(relId)) {
            relMap.set(relId, {
              id: relId,
              type: relationshipType,
              isOutgoing,
              other: otherNode,
              otherLabels,
              otherProperties,
              otherDisplayName: getNodeDisplayName(otherProperties, otherLabels, otherId),
            });
          }
        });
        setRelationships(Array.from(relMap.values()));
      }
    } catch (err) {
      console.error("Error loading relationships:", err);
    } finally {
      setLoading(false);
    }
  };

  const getNodeDisplayName = (properties: Record<string, any> | null, labels: string[] = [], fallbackId?: string) => {
    if (properties) {
      const keys = ["title", "name", "id", "description", "label", "requirement_title", "feature_name", "user_name", "location_name", "text", "value", "content", "identifier"];
      for (const key of keys) {
        if (properties[key] != null && properties[key] !== "") return String(properties[key]);
      }
      for (const [key, value] of Object.entries(properties)) {
        if (value != null && value !== "" && !key.startsWith("_")) return `${String(value)} (${key})`;
      }
    }
    if (labels.length > 0) return `${labels.join(", ")}${fallbackId ? ` (${fallbackId})` : ""}`;
    if (fallbackId) return `Node ${fallbackId}`;
    return "Unnamed Node";
  };

  const formatPropertyName = (key: string) =>
    key.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

  const formatPropertyValue = (value: any) => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "object") {
      if (value.toNumber) return value.toNumber().toString();
      if (Array.isArray(value)) return value.join(", ");
      return JSON.stringify(value);
    }
    if (typeof value === "string" && value.includes("T")) {
      const date = new Date(value);
      if (!isNaN(date.getTime())) return date.toLocaleString();
    }
    return String(value);
  };

  const getPropertyRows = () => {
    const props = isEditing ? editedProperties : nodeProperties;
    return Object.entries(props)
      .filter(([key]) => !["labels", "id"].includes(key))
      .map(([key, value]) => ({
        key,
        displayName: formatPropertyName(key),
        value: formatPropertyValue(value),
        originalValue: value,
      }));
  };

  const handleSave = () => {
    if (onSave) onSave(editedProperties);
    setIsEditing(false);
    setMessage('Properties saved locally! ✓');
    setTimeout(() => setMessage(''), 3000);
  };

const handleSaveToNeo4j = async () => {
  if (!node || !threadId) {
    setMessage('Error: No project or node selected');
    setTimeout(() => setMessage(''), 5000);
    return;
  }

  setLoading(true);
  setMessage('');

  try {
    // Determine node type and appropriate save method
    const nodeLabel = nodeProperties?.labels?.[0]?.toLowerCase() || '';
    const nodeId = node.id;
    const propertiesToSave = isEditing ? editedProperties : nodeProperties;

    console.log('🔍 [DEBUG] Saving to Neo4j:', {
      nodeId,
      nodeLabel,
      threadId,
      properties: propertiesToSave
    });

    // Extract index from node properties if available
    const nodeIndex = nodeProperties?.index || nodeProperties?.requirement_index || 0;

    if (nodeLabel.includes('requirement')) {
      // For requirements, use saveSelectedRequirements API
      const selectedReq = [propertiesToSave.description || JSON.stringify(propertiesToSave)];
      const selectedRisks = [projectStatus?.risks?.[nodeIndex] || 'Associated risk'];
      
      await requirementsAPI.saveSelectedRequirements(
        threadId,
        selectedReq,
        selectedRisks,
        projectStatus?.selected_keyword || threadId
      );
      console.log('✅ Requirement saved to Neo4j');
      
    } else if (nodeLabel.includes('risk')) {
      // For risks, use updateSingleRisk API
      await requirementsAPI.updateSingleRisk({
        thread_id: threadId,
        risk_index: nodeIndex,
        risk: propertiesToSave.description || JSON.stringify(propertiesToSave),
        requirement: propertiesToSave.related_requirement || projectStatus?.requirements?.[nodeIndex] || ''
      });
      console.log('✅ Risk saved to Neo4j');
      
    } else if (nodeLabel.includes('test') || nodeLabel.includes('testcase')) {
      // For test cases, use save-test-cases API
      const testCases = propertiesToSave.test_cases || [propertiesToSave.description] || [JSON.stringify(propertiesToSave)];
      
      await requirementsAPI.saveTestCases({
        thread_id: threadId,
        requirement_index: nodeIndex,
        test_cases: testCases
      });
      console.log('✅ Test case saved to Neo4j');
      
    } else {
      // Generic node update - fallback
      setMessage('⚠️ Generic node save - using requirement API as fallback');
      const selectedReq = [propertiesToSave.description || JSON.stringify(propertiesToSave)];
      const selectedRisks = ['Associated risk'];
      
      await requirementsAPI.saveSelectedRequirements(
        threadId,
        selectedReq,
        selectedRisks,
        threadId
      );
      console.log('✅ Generic node saved to Neo4j using fallback');
    }

    setMessage('✅ Successfully saved to Neo4j!');
    
    // Notify parent component about the update
    if (onNodeUpdate && node) {
      onNodeUpdate(node.id, propertiesToSave);
    }

  } catch (error: any) {
    console.error('❌ Error saving to Neo4j:', error);
    setMessage(`Error: ${error.response?.data?.detail || error.message || 'Failed to save to Neo4j'}`);
    setTimeout(() => setMessage(''), 5000);
  } finally {
    setLoading(false);
  }
};

  const handleRegenerateWithFeedback = async () => {
    if (!feedback.trim()) {
      setMessage('Please provide feedback for regeneration');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      if (!threadId) {
        setMessage('Error: No project selected. Please select a project first.');
        setTimeout(() => setMessage(''), 5000);
        return;
      }

      console.log('🔍 [DEBUG] Sending node regeneration request:', {
        thread_id: threadId,
        nodeType: nodeProperties?.labels?.[0] || 'Node',
        feedback: feedback,
      });

      let regenerateType = 'requirement';
      const nodeLabel = nodeProperties?.labels?.[0]?.toLowerCase() || '';
      
      if (nodeLabel.includes('risk')) {
        regenerateType = 'risks';
      }

      const indexes = [0]; // Default to first item

      const result = await requirementsAPI.regenerateWithFeedback({
        thread_id: threadId,
        indexes: indexes,
        feedback: feedback,
        regenerate_type: regenerateType
      });

      console.log('🔍 [DEBUG] Received regeneration response:', result);

      // Update the node properties with the regenerated content
      if (result) {
        const updatedProperties = { ...nodeProperties };
        let updatedContent = '';
        
        if (regenerateType === 'requirement' && result.requirements && result.requirements[0]) {
          updatedContent = result.requirements[0];
          updatedProperties.description = updatedContent;
        } else if (regenerateType === 'risks' && result.risks && result.risks[0]) {
          updatedContent = result.risks[0];
          updatedProperties.description = updatedContent;
        }
        
        if (updatedContent) {
          setEditedProperties(updatedProperties);
          
          if (onSave) {
            onSave(updatedProperties);
          }

          // Notify parent component about the regeneration
          if (onNodeUpdate && node) {
            onNodeUpdate(node.id, updatedProperties);
          }

          // Also notify via onRegenerate if provided
          if (onRegenerate) {
            onRegenerate(result);
          }

          setMessage('✅ Node regenerated successfully! Changes applied to UI.');
        } else {
          setMessage('⚠️ Regeneration completed but no content was returned');
        }
      }

      setFeedback('');

    } catch (error: any) {
      console.error('🔍 [DEBUG] Error regenerating node:', error);
      setMessage(`Error: ${error.response?.data?.detail || error.message || 'Failed to regenerate node'}`);
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleManualUpdate = async () => {
    if (!editedProperties) {
      setMessage('Properties cannot be empty');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    if (!threadId) {
      setMessage('Error: No project selected. Please select a project first.');
      setTimeout(() => setMessage(''), 5000);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const nodeLabel = nodeProperties?.labels?.[0]?.toLowerCase() || '';
      let updateType = 'requirement';
      
      if (nodeLabel.includes('risk')) {
        updateType = 'risk';
      }

      const result = await requirementsAPI.updateItem({
        thread_id: threadId,
        index: 0,
        type: updateType,
        new_content: editedProperties.description || JSON.stringify(editedProperties),
        update_related: true
      });

      console.log('🔍 [DEBUG] Manual update response:', result);

      if (onSave) {
        onSave(editedProperties);
      }

      // Notify parent component about the update
      if (onNodeUpdate && node) {
        onNodeUpdate(node.id, editedProperties);
      }

      setMessage('✅ Properties updated successfully! Changes saved.');
      setIsEditing(false);

      setTimeout(() => setMessage(''), 3000);

    } catch (error: any) {
      console.error('🔍 [DEBUG] Error updating node:', error);
      setMessage(`Error: ${error.response?.data?.detail || error.message || 'Failed to update properties'}`);
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Resize handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!resizing) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= 300 && newWidth <= 800) {
        setDialogWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setResizing(false);
    };

    if (resizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizing]);

  if (!node) return null;

  const getNodeLabel = () => nodeProperties?.labels?.[0] || "Node";
  const getNodeTitle = () => displayName || getNodeDisplayName(nodeProperties, [getNodeLabel()], node?.id);

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        height: "100%",
        width: `${dialogWidth}px`,
        maxWidth: "90%",
        backgroundColor: "#fff",
        borderLeft: "1px solid #e1e5e9",
        boxShadow: "-4px 0 12px rgba(0,0,0,0.1)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        transform: node ? "translateX(0)" : "translateX(100%)",
        transition: resizing ? "none" : "transform 0.3s ease-in-out",
      }}
    >
      {/* Resize handle */}
      <div
        style={{
          position: "absolute",
          left: -4,
          top: 0,
          bottom: 0,
          width: 8,
          cursor: "col-resize",
          zIndex: 1001,
        }}
        onMouseDown={handleMouseDown}
      />

      {/* Header */}
      <div style={{ padding: "20px", borderBottom: "1px solid #e1e5e9", backgroundColor: "#f8fafc", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ backgroundColor: node.color || "#3b82f6", color: "#fff", padding: "4px 10px", borderRadius: "12px", fontSize: "12px", fontWeight: 600, display: "inline-block", marginBottom: "8px" }}>
            {getNodeLabel()}
          </div>
          <h2 style={{ margin: "8px 0 0 0", fontSize: "20px", fontWeight: 700 }}>{getNodeTitle()}</h2>
        </div>
        <button onClick={onClose} style={{ fontSize: "18px", background: "none", border: "none", cursor: "pointer", color: "#64748b" }}>✕</button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid #e1e5e9", backgroundColor: "#f1f5f9" }}>
        {["edit", "relationships"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            style={{
              flex: 1,
              padding: "12px",
              background: "none",
              border: "none",
              borderBottom: activeTab === tab ? "3px solid #3b82f6" : "3px solid transparent",
              color: activeTab === tab ? "#3b82f6" : "#64748b",
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            {tab === "edit" ? "Edit & Regenerate" : `Relationships (${relationships.length})`}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
        {message && (
          <div
            style={{
              padding: "12px 16px",
              marginBottom: "20px",
              borderRadius: "6px",
              backgroundColor: message.includes('Error') ? "#fee2e2" : "#d1fae5",
              color: message.includes('Error') ? "#991b1b" : "#065f46",
              border: message.includes('Error') ? "1px solid #fecaca" : "1px solid #86efac",
              fontSize: "14px",
              fontWeight: "500",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            <span>{message.includes('Error') ? '❌' : '✅'}</span>
            <span>{message}</span>
          </div>
        )}

        {activeTab === "edit" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Properties Editing Section */}
            <div>
              <h3 style={{
                borderBottom: "2px solid #e1e5e9",
                paddingBottom: "8px",
                marginBottom: "16px",
                fontWeight: "700",
                color: "#1e293b",
                fontSize: "16px"
              }}>
                Properties
              </h3>

              {isEditing ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {getPropertyRows().map((prop) => (
                    <div key={prop.key} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <label style={{ fontWeight: "600", fontSize: "14px", color: "#374151" }}>
                        {prop.displayName}
                      </label>
                      <textarea
                        value={editedProperties[prop.key] || ''}
                        onChange={(e) => setEditedProperties({
                          ...editedProperties,
                          [prop.key]: e.target.value
                        })}
                        rows={3}
                        disabled={loading}
                        style={{
                          width: "100%",
                          border: "1px solid #d1d5db",
                          borderRadius: "6px",
                          padding: "8px 12px",
                          fontSize: "14px",
                          resize: "vertical",
                          fontFamily: "inherit",
                          backgroundColor: loading ? "#f9fafb" : "white"
                        }}
                      />
                    </div>
                  ))}
                  <div style={{ display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap" }}>
                    <button
                      onClick={handleSave}
                      disabled={loading}
                      style={{
                        padding: "10px 16px",
                        backgroundColor: loading ? "#94a3b8" : "#3b82f6",
                        color: "white",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: "600",
                        cursor: loading ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        flex: 1
                      }}
                    >
                      <span>💾</span>
                      <span>Save Locally</span>
                    </button>
                    <button
                      onClick={handleSaveToNeo4j}
                      disabled={loading}
                      style={{
                        padding: "10px 16px",
                        backgroundColor: loading ? "#94a3b8" : "#10b981",
                        color: "white",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: "600",
                        cursor: loading ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        flex: 1
                      }}
                    >
                      <span>💾</span>
                      <span>Save to Neo4j</span>
                    </button>
                    <button
                      onClick={() => {
                        setIsEditing(false);
                        setEditedProperties(nodeProperties);
                        setMessage('');
                      }}
                      disabled={loading}
                      style={{
                        padding: "10px 16px",
                        backgroundColor: "#e2e8f0",
                        color: "#475569",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: "600",
                        cursor: loading ? "not-allowed" : "pointer",
                        flex: 1
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  {getPropertyRows().map((prop, idx) => (
                    <div key={prop.key} style={{ display: "flex", padding: "12px 0", borderBottom: "1px solid #f1f5f9" }}>
                      <div style={{ flex: "0 0 140px", fontWeight: 600, fontSize: "14px" }}>{prop.displayName}</div>
                      <div style={{ flex: 1, fontSize: "14px", color: "#374151" }}>{prop.value}</div>
                    </div>
                  ))}
                  <div style={{ display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap" }}>
                    <button
                      onClick={() => {
                        setIsEditing(true);
                        setMessage('');
                      }}
                      style={{
                        padding: "10px 16px",
                        backgroundColor: "#3b82f6",
                        color: "white",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: "600",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        flex: 1
                      }}
                    >
                      
                      <span>Edit Properties</span>
                    </button>
                    <button
                      onClick={handleSaveToNeo4j}
                      disabled={loading}
                      style={{
                        padding: "10px 16px",
                        backgroundColor: loading ? "#94a3b8" : "#10b981",
                        color: "white",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "14px",
                        fontWeight: "600",
                        cursor: loading ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        flex: 1
                      }}
                    >
             
                      <span>Save to Neo4j</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* AI Regeneration Section */}
            <div style={{
              padding: "20px",
              backgroundColor: "#f0f9ff",
              borderRadius: "8px",
              border: "1px solid #bae6fd"
            }}>
              <h4 style={{
                borderBottom: "2px solid #7dd3fc",
                paddingBottom: "8px",
                marginBottom: "16px",
                fontWeight: "700",
                color: "#0c4a6e",
                fontSize: "15px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
             
                <span>Regenerate with AI </span>
              </h4>
              <div style={{ marginBottom: "12px" }}>
                <label style={{
                  display: "block",
                  marginBottom: "8px",
                  fontWeight: "600",
                  fontSize: "13px",
                  color: "#0c4a6e"
                }}>
                  What would you like to improve about this node?
                </label>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Example: 'Make the description more detailed' or 'Add technical specifications'"
                  rows={4}
                  disabled={loading}
                  style={{
                    width: "100%",
                    border: "1px solid #7dd3fc",
                    borderRadius: "6px",
                    padding: "12px",
                    fontSize: "14px",
                    resize: "vertical",
                    fontFamily: "inherit",
                    backgroundColor: loading ? "#f0f9ff" : "white"
                  }}
                />
              </div>
              <button
                onClick={handleRegenerateWithFeedback}
                disabled={loading || !feedback.trim()}
                style={{
                  width: "100%",
                  padding: "12px 20px",
                  backgroundColor: (loading || !feedback.trim()) ? "#94a3b8" : "#10b981",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "14px",
                  fontWeight: "600",
                  cursor: (loading || !feedback.trim()) ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px"
                }}
              >
                {loading ? (
                  <>
                    <span>⏳</span>
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>✨</span>
                    <span>Regenerate with Feedback</span>
                  </>
                )}
              </button>
              {!feedback.trim() && !loading && (
                <p style={{
                  marginTop: "8px",
                  fontSize: "12px",
                  color: "#64748b",
                  fontStyle: "italic",
                  textAlign: "center"
                }}>
                  💡 Tip: Provide clear feedback to get better results
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === "relationships" && (
          <div>
            {loading ? <div style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>Loading relationships...</div> :
              relationships.length ? relationships.map(r => (
                <div key={r.id} style={{ padding: "12px", border: "1px solid #e1e5e9", borderRadius: "6px", marginBottom: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                    <span style={{ fontWeight: "bold" }}>{r.isOutgoing ? "→" : "←"}</span>
                    <span style={{ backgroundColor: "#e0e7ff", padding: "2px 6px", borderRadius: "12px", fontSize: "12px" }}>{r.type}</span>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>{r.isOutgoing ? "outgoing" : "incoming"}</span>
                  </div>
                  <div style={{ paddingLeft: "16px" }}>
                    <div style={{ fontWeight: 600, marginBottom: "4px" }}>{r.otherDisplayName}</div>
                    <div style={{ fontSize: "12px", color: "#64748b" }}>
                      <span style={{ backgroundColor: getUniqueColorForLabel(r.otherLabels[0]), color: "#fff", padding: "2px 6px", borderRadius: "4px", marginRight: "4px" }}>{r.otherLabels[0]}</span>
                      Connected node
                    </div>
                  </div>
                </div>
              )) : <div style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>No relationships found</div>}
          </div>
        )}
      </div>
    </div>
  );
};