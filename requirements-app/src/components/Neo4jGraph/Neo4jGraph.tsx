// Neo4jGraph.tsx
import React, { useEffect, useRef, useState } from "react";
import NVL, { Node, Relationship, HitTargets } from "@neo4j-nvl/base";
import { InteractiveNvlWrapper } from "@neo4j-nvl/react";
import { connect } from "./connections";
import { styleGraph } from "./styling";
import { calculateGraphStats, exportToJSON, exportToCSV, getNodeDisplayName } from "./graphUtils";
import { StatsPanel } from "../StatsPanel/StatsPanel";
import { PropertiesDialog } from "./PropertiesDialog";

// ------------------ Toolbar ------------------
const Toolbar = ({ projects, selectedProject, onProjectChange, onSearch, onFilter, onExport, onRefresh, onFitView, onLayoutChange }: any) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  const inputStyle = {
    flex: 1,
    minWidth: 200,
    padding: "8px 12px",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    outline: "none",
    fontSize: 14,
  };

  const selectStyle = {
    padding: "8px 12px",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    outline: "none",
    fontSize: 14,
  };

  const buttonStyle = {
    padding: "8px 16px",
    borderRadius: 6,
    border: "none",
    backgroundColor: "#0ea5e9",
    color: "#fff",
    fontWeight: 500,
    cursor: "pointer",
    transition: "background-color 0.2s, opacity 0.2s",
    opacity: 0.6,
  } as const;

  const buttonHoverStyle = { backgroundColor: "#1d4ed8", opacity: 1 };

  return (
    <div
      style={{
        position: "absolute",
        top: 5,
        left: 20,
        right: 20,
        backgroundColor: "#fff",
        padding: 16,
        borderRadius: 8,
        border: "1px solid #d1d5db",
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        display: "flex",
        gap: 12,
        alignItems: "center",
        flexWrap: "wrap",
        zIndex: 100,
      }}
    >
      <select value={selectedProject} onChange={(e) => onProjectChange(e.target.value)} style={selectStyle}>
        {projects.map((p: string) => <option key={p} value={p}>{p}</option>)}
      </select>

      <input
        type="text"
        placeholder="Search nodes..."
        value={searchQuery}
        onChange={(e) => { setSearchQuery(e.target.value); onSearch(e.target.value); }}
        style={inputStyle}
      />

      <select value={filterType} onChange={(e) => { setFilterType(e.target.value); onFilter(e.target.value); }} style={selectStyle}>
        <option value="all">All Types</option>
        <option value="Requirement">Requirement</option>
        <option value="TestCase">TestCase</option>
        <option value="Priority">Priority</option>
        <option value="Source">Source</option>
        <option value="BusinessNeed">BusinessNeed</option>
        <option value="Project">Project</option>
        <option value="Risk">Risk</option>
        <option value="RiskAssessment">RiskAssessment</option>
      </select>

      <select onChange={(e) => onLayoutChange(e.target.value)} style={selectStyle}>
        <option value="auto">Auto Layout</option>
        <option value="circular">Circular</option>
        <option value="grid">Grid</option>
      </select>

      <div style={{ display: "flex", gap: 8 }}>
        {["Fit", "Refresh", "Export JSON", "Export CSV"].map((label, idx) => (
          <button
            key={idx}
            style={buttonStyle}
            onClick={() => {
              if (label === "Fit") onFitView();
              if (label === "Refresh") onRefresh();
              if (label === "Export JSON") onExport("json");
              if (label === "Export CSV") onExport("csv");
            }}
            onMouseOver={(e) => Object.assign(e.currentTarget.style, buttonHoverStyle)}
            onMouseOut={(e) => Object.assign(e.currentTarget.style, { ...buttonStyle })}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};


// ------------------ Debug Panel ------------------
const DebugPanel = ({ nodes, filteredNodes, relationships, filteredRelationships, eventLog }: any) => (
  <div style={{
    position: "absolute",
    top: 120,
    right: 20,
    backgroundColor: "rgba(255,255,255,0.9)",
    padding: 12,
    borderRadius: 8,
    fontSize: 12,
    zIndex: 100,
    maxWidth: 300,
  }}>
    <div><strong>Debug Info:</strong></div>
    <div>Total Nodes: {nodes.length}</div>
    <div>Visible Nodes: {filteredNodes.length}</div>
    <div>Total Relationships: {relationships.length}</div>
    <div>Visible Relationships: {filteredRelationships.length}</div>
    {nodes.length > filteredNodes.length && (
      <div style={{ color: "orange" }}>⚠️ {nodes.length - filteredNodes.length} nodes filtered out</div>
    )}
    {eventLog && <div style={{ marginTop: 8 }}><strong>Last Event:</strong> {eventLog}</div>}
  </div>
);

// ------------------ Neo4jGraph Component ------------------
export const Neo4jGraph = () => {
  const [projects, setProjects] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");

  const [nodes, setNodes] = useState<Node[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [filteredNodes, setFilteredNodes] = useState<Node[]>([]);
  const [filteredRelationships, setFilteredRelationships] = useState<Relationship[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [recordObjectMap, setRecordObjectMap] = useState<Map<string, any>>(new Map());
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [stats, setStats] = useState<any>(null);
  const [eventLog, setEventLog] = useState<string>("");

  const nvlRef = useRef<NVL | null>(null);
  const counterRef = useRef(0);

  const colorPalette = ["#FFDF81","#C990C0","#F79767","#56C7E4","#F16767","#D8C7AE","#8DCC93","#ECB4C9","#4D8DDA","#FFC354","#DA7294","#579380"];
  const labelColorMap = new Map<string,string>();
  const getNodeColor = (label: string) => {
    if (!labelColorMap.has(label)) labelColorMap.set(label, colorPalette[labelColorMap.size % colorPalette.length]);
    return labelColorMap.get(label)!;
  };

  // ------------------ Event Logger ------------------
  const logEvent = (nvlEventName: string, nvlEventData: { originalEvent: MouseEvent; data?: Node | Relationship | Node[] | { x:number,y:number } | number; hitTargets?: HitTargets }) => {
    console.log(nvlEventName, nvlEventData.data, nvlEventData.hitTargets, nvlEventData.originalEvent);
    setEventLog(`${nvlEventName}: ${JSON.stringify(nvlEventData.data)}`);
  };

  // ------------------ Load Projects ------------------
  const loadProjects = async () => {
    const result = await connect(`MATCH (p:Project) RETURN p LIMIT 500`);
    if (!result) return;

    const projectNames = result.nodes
      .map(n => result.recordObjectMap.get(n.id)?.properties?.name)
      .filter(Boolean);

    setProjects(projectNames);
    if (projectNames.length) setSelectedProject(projectNames[0]);
  };
  useEffect(() => { loadProjects(); }, []);

  // ------------------ Load Nodes for Project ------------------
  const loadProjectNodes = async (projectName: string) => {
    if (!projectName) return;
    const result = await connect(
      `MATCH (p:Project {name:$projectName})-[:HAS_REQUIREMENT]->(n)-[r]-(m) RETURN n,r,m LIMIT 500`,
      { projectName }
    );
    if (!result) return;
const { styledNodes, styledRelationships } = styleGraph(result);

// Style nodes
styledNodes.forEach((node: Node) => {
  const originalNode = result.recordObjectMap.get(node.id);
  node.captions = [{ value: getNodeDisplayName(node, result.recordObjectMap) }];
  node.color = getNodeColor(originalNode?.labels?.[0] || "Unknown");
});

styledRelationships.forEach((rel: Relationship) => {
  // originalRel comes from your recordObjectMap
  const originalRel = result.recordObjectMap.get(rel.id); // This should point to the Neo4j relationship
  rel.captions = [{ value: originalRel?.type || "RELATED" }];
});

    setNodes(styledNodes);
    setRelationships(styledRelationships);
    setFilteredNodes(styledNodes);
    setFilteredRelationships(styledRelationships);
    setRecordObjectMap(result.recordObjectMap);
    setStats(calculateGraphStats(styledNodes, styledRelationships, result.recordObjectMap));
    counterRef.current = styledNodes.length - 1;
  };
  useEffect(() => { if(selectedProject) loadProjectNodes(selectedProject); }, [selectedProject]);

  // ------------------ Filter & Search ------------------
  useEffect(() => {
    let filtered = nodes;
    if (filterType !== "all") filtered = filtered.filter(n => recordObjectMap.get(n.id)?.labels?.includes(filterType));
    if (searchQuery) filtered = filtered.filter(n => {
      const props = recordObjectMap.get(n.id)?.properties || {};
      const q = searchQuery.toLowerCase();
      const matchCaption = n.captions?.some(c => c.value.toLowerCase().includes(q));
      const matchProp = Object.values(props).some(v => String(v).toLowerCase().includes(q));
      return matchCaption || matchProp;
    });
    setFilteredNodes(filtered);
    const nodeIds = new Set(filtered.map(n => n.id));
    const rels = relationships.filter(r => nodeIds.has(r.from) && nodeIds.has(r.to));
    setFilteredRelationships(rels);
    setStats(calculateGraphStats(filtered, rels, recordObjectMap));
  }, [nodes, relationships, searchQuery, filterType, recordObjectMap]);

  // ------------------ Node Click ------------------
  const handleNodeClick = async (node: Node) => {
    setSelectedNode(node);
    const result = await connect(
      `MATCH (n)-[r]-(neighbor) WHERE elementId(n) = $nodeId RETURN neighbor,r LIMIT 50`,
      { nodeId: node.id }
    );
    if (!result) return;

    const newNodes: Node[] = [];
    const newRels: Relationship[] = [];

    result.nodes.forEach((n: any) => {
      if (!nodes.find(existing => existing.id === n.id)) {
        const orig = result.recordObjectMap.get(n.id);
        newNodes.push({
          ...n,
          captions: [{ value: getNodeDisplayName(n, result.recordObjectMap) }],
          color: getNodeColor(orig?.labels?.[0] || "Neighbor"),
        });
      }
    });
    
    result.relationships.forEach((r: any) => {
  if (!relationships.find(existing => existing.id === r.id)) {
    // Get type from recordObjectMap
    const originalRel = result.recordObjectMap.get(r.id);
    r.captions = [{ value: originalRel?.type || "RELATED" }];
    newRels.push(r);
  }
});



    nvlRef.current?.addAndUpdateElementsInGraph(newNodes, newRels);
    setNodes(prev => [...prev, ...newNodes]);
    setRelationships(prev => [...prev, ...newRels]);
  };

  // ------------------ Node Add / Remove ------------------
  const addNode = (fromNodeId?: string) => {
    counterRef.current++;
    const id = `node-${counterRef.current}`;
    const newNode: Node = { id, captions:[{value:id}], color:getNodeColor("Dynamic") };
    const fromId = fromNodeId || selectedNode?.id || nodes[0]?.id || id;
    const newRel: Relationship = { id:`rel-${fromId}-${id}`, from: fromId, to:id };

    nvlRef.current?.addAndUpdateElementsInGraph([newNode],[newRel]);
    setNodes(prev => [...prev,newNode]);
    setRelationships(prev => [...prev,newRel]);
  };
  const removeNode = (nodeId:string) => {
    nvlRef.current?.removeNodesWithIds([nodeId]);
    setNodes(prev => prev.filter(n=>n.id!==nodeId));
    setRelationships(prev=>prev.filter(r=>r.from!==nodeId && r.to!==nodeId));
    if(selectedNode?.id===nodeId) setSelectedNode(null);
  };

  // ------------------ Export / Fit / Layout ------------------
  const handleExport = (format:"json"|"csv") => {
    const content = format==="json"
      ? exportToJSON(filteredNodes, filteredRelationships, recordObjectMap)
      : exportToCSV(filteredNodes, filteredRelationships, recordObjectMap);
    const blob = new Blob([content],{type:format==="json"?"application/json":"text/csv"});
    const url = URL.createObjectURL(blob);
    const a=document.createElement("a");
    a.href=url;
    a.download=`graph-export-${Date.now()}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFitView = () => nvlRef.current?.fit(filteredNodes.map(n=>n.id));
  const handleLayoutChange = (layout:string) => {
    if(!nvlRef.current) return;
    const spacing=150;
    if(layout==="circular"){
      const radius=300;
      const positions=filteredNodes.map((n,i)=>({id:n.id,x:radius*Math.cos((2*Math.PI*i)/filteredNodes.length),y:radius*Math.sin((2*Math.PI*i)/filteredNodes.length)}));
      nvlRef.current.setNodePositions?.(positions,true);
    } else if(layout==="grid"){
      const cols=Math.ceil(Math.sqrt(filteredNodes.length));
      const positions=filteredNodes.map((n,i)=>({id:n.id,x:(i%cols)*spacing,y:Math.floor(i/cols)*spacing}));
      nvlRef.current.setNodePositions?.(positions,true);
    }
    nvlRef.current.fit(filteredNodes.map(n=>n.id));
  };

  // ------------------ Mouse Events ------------------
  const mouseEventCallbacks = {
    onNodeClick: handleNodeClick,
    onNodeDoubleClick:(node,hitTargets,e)=>{ logEvent("onNodeDoubleClick",{originalEvent:e,data:node,hitTargets}); handleFitView(); },
    onNodeRightClick:(node,hitTargets,e)=>{ logEvent("onNodeRightClick",{originalEvent:e,data:node,hitTargets}); removeNode(node.id); },
    onHover:(el,hitTargets,e)=>logEvent("onHover",{originalEvent:e,data:el,hitTargets}),
    onRelationshipClick:(rel,hitTargets,e)=>logEvent("onRelationshipClick",{originalEvent:e,data:rel,hitTargets}),
    onRelationshipDoubleClick:(rel,hitTargets,e)=>logEvent("onRelationshipDoubleClick",{originalEvent:e,data:rel,hitTargets}),
    onRelationshipRightClick:(rel,hitTargets,e)=>logEvent("onRelationshipRightClick",{originalEvent:e,data:rel,hitTargets}),
    onCanvasClick:(e)=>{ logEvent("onCanvasClick",{originalEvent:e}); addNode(selectedNode?.id); },
    onCanvasDoubleClick:(e)=>logEvent("onCanvasDoubleClick",{originalEvent:e}),
    onCanvasRightClick:(e)=>logEvent("onCanvasRightClick",{originalEvent:e}),
    onDrag:(nodes,e)=>logEvent("onDrag",{originalEvent:e,data:nodes}),
    onPan:(pan,e)=>logEvent("onPan",{originalEvent:e,data:pan}),
    onZoom:(zoom,e)=>logEvent("onZoom",{originalEvent:e,data:zoom}),
  };

  return (
    <div style={{position:"relative",width:"100%",height:"100vh"}}>
       {!selectedNode && (
        <Toolbar
        projects={projects}
        selectedProject={selectedProject}
        onProjectChange={setSelectedProject}
        onSearch={setSearchQuery}
        onFilter={setFilterType}
        onExport={handleExport}
        onRefresh={()=>selectedProject && loadProjectNodes(selectedProject)}
        onFitView={handleFitView}
        onLayoutChange={handleLayoutChange}
      />    )}
      <InteractiveNvlWrapper
        ref={nvlRef}
        nodes={filteredNodes}
        rels={filteredRelationships}
        nvlOptions={{allowDynamicMinZoom:true,disableWebGL:false,instanceId:"neo4j-graph"}}
        mouseEventCallbacks={mouseEventCallbacks}
      />

<PropertiesDialog
  node={selectedNode}
  nodeProperties={selectedNode ? recordObjectMap.get(selectedNode.id)?.properties || {} : {}}
  displayName={selectedNode ? getNodeDisplayName(selectedNode, recordObjectMap) : undefined}
  onClose={() => setSelectedNode(null)}
  threadId={selectedProject}
  projectStatus={{ 
    // You might need to create this state or fetch project status
    requirements: [], // Add your requirements data here
    risks: [], // Add your risks data here
    selected_keyword: selectedProject 
  }}
  onNodeUpdate={(nodeId, updatedProperties) => {
    // Update the node in the graph
    const updatedNodes = nodes.map(node => 
      node.id === nodeId 
        ? { ...node, captions: [{ value: getNodeDisplayName({...node, ...updatedProperties}, recordObjectMap) }] }
        : node
    );
    setNodes(updatedNodes);
    setFilteredNodes(updatedNodes);
    
    // Update recordObjectMap
    const updatedRecord = recordObjectMap.get(nodeId);
    if (updatedRecord) {
      recordObjectMap.set(nodeId, { ...updatedRecord, properties: updatedProperties });
    }
  }}
/>
      {stats && <StatsPanel stats={stats} selectedNodeCount={selectedNode?1:0}/>}
    </div>
  );
};
