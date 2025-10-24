import React, { useState } from 'react';
import { Box, Flex } from '@chakra-ui/react';
import Sidebar from './components/Sidebar/Sidebar';
import RequirementsPanel from './components/RequirementsPanel/RequirementsPanel.jsx';
import RisksPanel from './components/RisksPanel/RisksPanel';
import TestsPanel from './components/TestsPanel/TestsPanel';
import ProjectPanel from './components/ProjectPanel/ProjectPanel';
import { Neo4jGraph } from './components/Neo4jGraph/Neo4jGraph';
import TopNavBar from './components/TopNavBar/TopNavBar';
import ChakraUIExamples from './components/ChakraUIExamples/ChakraUIExamples';
import QuickStartExample from './components/QuickStartExample/QuickStartExample';
// import TraceabilityView from './components/traceability/TraceabilityView/TraceabilityView';
import './styles/App.css';

function App() {
  const [activePanel, setActivePanel] = useState('projects');
  const [projectStatus, setProjectStatus] = useState(null);

  const renderActivePanel = () => {
    switch (activePanel) {
      case 'requirements':
        return (
          <RequirementsPanel
            projectStatus={projectStatus}
            setProjectStatus={setProjectStatus}
            setActivePanel={setActivePanel}
          />
        );
      case 'risks':
        return (
          <RisksPanel 
            projectStatus={projectStatus} 
            setProjectStatus={setProjectStatus}
            setActivePanel={setActivePanel}
          />
        );
      case 'tests':
        return <TestsPanel projectStatus={projectStatus} />;
      case 'projects':
        return <ProjectPanel setProjectStatus={setProjectStatus} />;
      case 'neo4jgraph':
        return <Neo4jGraph />;
      case 'chakra-examples':
        return <ChakraUIExamples />;
      case 'quick-start':
        return <QuickStartExample />;
      default:
        return (
          <RequirementsPanel
            projectStatus={projectStatus}
            setProjectStatus={setProjectStatus}
            setActivePanel={setActivePanel}
          />
        );
    }
  };

  return (
    <Box h="100vh" overflow="hidden">
      <Flex h="100%">
        <Sidebar
          activePanel={activePanel}
          setActivePanel={setActivePanel}
          projectStatus={projectStatus}
        />
        
        <Flex direction="column" flex="1" overflow="hidden">
          <TopNavBar />
          <Box flex="1" overflow="auto" bg="bg">
            {renderActivePanel()}
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
}

export default App;
