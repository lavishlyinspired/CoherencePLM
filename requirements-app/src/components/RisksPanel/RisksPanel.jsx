// RisksPanel.jsx
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Text, 
  Button, 
  VStack, 
  HStack, 
  Spinner,
  Card,
  Alert,
  Container,
  Badge,
  IconButton,
  Flex,
  Center,
  Stack,
  NativeSelect,
  Input
} from '@chakra-ui/react';
import { 
  FaSearch,
  FaDatabase,
  FaSync,
  FaCheckSquare,
  FaSquare,
  FaShieldAlt,
  FaExclamationTriangle,
  FaInfoCircle,
  FaTasks,
  FaCog,
  FaTrash,
  FaEdit,
  FaSave
} from 'react-icons/fa';
import { requirementsAPI } from '../../services/api';
import BottomFadingPopup from './FadingPopup';
const RisksPanel = ({ projectStatus, setProjectStatus }) => {
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedRisks, setSelectedRisks] = useState(new Set());
  const [riskAction, setRiskAction] = useState('');
  const [loadedRisks, setLoadedRisks] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [bulkFeedback, setBulkFeedback] = useState('');
  const [projectName, setProjectName] = useState('');
  const [availableProjects, setAvailableProjects] = useState([]);
  const [detailFeedback, setDetailFeedback] = useState('');
  const [detailLoading, setDetailLoading] = useState(false);
  const [testCases, setTestCases] = useState({});

  useEffect(() => {
    loadAvailableProjects();
    loadTestCases();
  }, [projectStatus]);

  const loadTestCases = async () => {
    if (!projectStatus?.thread_id || !projectStatus?.requirements) return;

    const testCasesData = {};
    for (let i = 0; i < projectStatus.requirements.length; i++) {
      try {
        const result = await requirementsAPI.getTestCases(projectStatus.thread_id, i);
        testCasesData[i] = result.test_cases || [];
      } catch (error) {
        console.error(`Error loading test cases for requirement ${i}:`, error);
        testCasesData[i] = [];
      }
    }
    setTestCases(testCasesData);
  };

  const loadAvailableProjects = async () => {
    try {
      let response;
      try {
        response = await requirementsAPI.getAllProjects();
      } catch (error) {
        console.log('First endpoint failed, trying alternative...');
        response = await requirementsAPI.listProjects();
      }
      setAvailableProjects(response.projects || []);
    } catch (error) {
      console.error('Error loading projects:', error);
      setAvailableProjects([]);
    }
  };

  const loadRisksFromNeo4j = async (targetProjectName = null) => {
    setLoading(true);
    setMessage('');
    
    const projectToLoad = targetProjectName || projectName;
    
    if (!projectToLoad) {
      setMessage('Please select a project');
      setLoading(false);
      return;
    }
    
    try {
      const result = await requirementsAPI.getProjectDataFromNeo4j(projectToLoad);
      const transformedRisks = result.risks || [];
      
      setLoadedRisks(transformedRisks);
      setSelectedRisks(new Set());
      setMessage(`✅ Successfully loaded ${transformedRisks.length} risks from "${projectToLoad}"`);
    } catch (error) {
      setMessage(`❌ Error loading risks: ${error.response?.data?.detail || error.message}`);
      setLoadedRisks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRiskSelect = (index) => {
    const newSelection = new Set(selectedRisks);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedRisks(newSelection);
  };

  const handleSelectAllRisks = () => {
    const risksToSelect = getDisplayRisks();
    if (selectedRisks.size === risksToSelect.length) {
      setSelectedRisks(new Set());
    } else {
      setSelectedRisks(new Set(risksToSelect.map((_, index) => index)));
    }
  };

  const handleRiskAction = async () => {
    if (!riskAction || selectedRisks.size === 0) {
      setMessage('⚠️ Please select risks and an action');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      if (riskAction === 'regenerate') {
        const result = await requirementsAPI.regenerateRisks(
          projectStatus.thread_id,
          Array.from(selectedRisks)
        );
        if (setProjectStatus) {
          setProjectStatus(result);
        }
        setMessage(`✅ Regenerated ${selectedRisks.size} risks successfully`);
      } else if (riskAction === 'regenerate-with-feedback') {
        const result = await requirementsAPI.regenerateWithFeedback({
          thread_id: projectStatus.thread_id,
          indexes: Array.from(selectedRisks),
          feedback: bulkFeedback,
          regenerate_type: 'risks'
        });
        if (setProjectStatus) {
          setProjectStatus(result);
        }
        setMessage(`✅ Regenerated ${selectedRisks.size} risks with feedback`);
      } else if (riskAction === 'update') {
        const displayRisks = getDisplayRisks();
        const selectedRiskData = displayRisks
          .filter((_, index) => selectedRisks.has(index))
          .map((risk, arrayIndex) => {
            const originalIndex = Array.from(selectedRisks)[arrayIndex];
            const riskDescription = typeof risk === 'string' ? risk : risk.description;
            const requirement = typeof risk === 'object' ? risk.requirement : 
                               (projectStatus?.requirements?.[originalIndex] || 'Unknown requirement');
            
            return {
              risk: riskDescription,
              requirement_index: originalIndex,
              requirement: requirement
            };
          });
        
        await requirementsAPI.updateRisksInNeo4j(
          projectStatus.thread_id,
          selectedRiskData
        );
        setMessage(`✅ Updated ${selectedRisks.size} risks in Neo4j`);
      }
      
      setSelectedRisks(new Set());
      setRiskAction('');
      setBulkFeedback('');
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateAllRisks = async () => {
    if (!projectStatus?.thread_id) {
      setMessage('⚠️ Please create a project first in the Requirements panel');
      return;
    }

    setLoading(true);
    setMessage('');
    
    try {
      const result = await requirementsAPI.regenerate(projectStatus.thread_id, 'risks');
      setMessage('✅ All risks regenerated successfully!');
      if (setProjectStatus) {
        setProjectStatus(result);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchRisks = async () => {
    if (!searchQuery.trim()) {
      setMessage('⚠️ Please enter a search query');
      return;
    }

    setLoading(true);
    setMessage('');
    
    try {
      const result = await requirementsAPI.queryRisks(searchQuery);
      setSearchResults(result);
      setMessage(`✅ Found ${result.length} risks matching your search`);
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (index) => {
    const items = getDisplayRisks();
    const item = items[index];
    
    const riskDescription = typeof item === 'string' ? item : item.description;
    const associatedRequirement = typeof item === 'object' ? item.requirement : 
                                  (projectStatus?.requirements?.[index] || 'No associated requirement');
    
    setSelectedItem({
      index,
      type: 'risk',
      content: riskDescription,
      requirement: associatedRequirement
    });
    setDetailFeedback('');
  };

  const handleRegenerateWithFeedback = async () => {
    if (!detailFeedback.trim()) {
      setMessage('⚠️ Please provide feedback');
      return;
    }

    if (!projectStatus?.thread_id) {
      setMessage('⚠️ No project loaded. Please load a project first.');
      return;
    }

    setDetailLoading(true);
    
    const effectiveKeyword = projectStatus.selected_keyword || projectStatus.thread_id;
    
    const requestData = {
      thread_id: projectStatus.thread_id,
      indexes: [selectedItem.index],
      feedback: detailFeedback,
      regenerate_type: 'risks'
    };

    try {
      const result = await requirementsAPI.regenerateWithFeedback(requestData);

      const newRisk = result.risks ? result.risks[selectedItem.index] : selectedItem.content;
      const newRequirement = result.requirements ? result.requirements[selectedItem.index] : selectedItem.requirement;

      if (loadedRisks.length > 0) {
        const updatedLoadedRisks = [...loadedRisks];
        if (selectedItem.index < updatedLoadedRisks.length) {
          if (typeof updatedLoadedRisks[selectedItem.index] === 'object') {
            updatedLoadedRisks[selectedItem.index] = {
              ...updatedLoadedRisks[selectedItem.index],
              description: newRisk,
              requirement: newRequirement
            };
          } else {
            updatedLoadedRisks[selectedItem.index] = newRisk;
          }
          setLoadedRisks(updatedLoadedRisks);
        }
      }

      const updatedProjectStatus = {
        thread_id: projectStatus.thread_id,
        status: 'regenerated',
        selected_keyword: result.selected_keyword || effectiveKeyword,
        requirements: result.requirements || projectStatus.requirements,
        risks: result.risks || projectStatus.risks
      };
      
      if (setProjectStatus) {
        setProjectStatus(updatedProjectStatus);
      }
      
      setSelectedItem({
        ...selectedItem,
        content: newRisk,
        requirement: newRequirement
      });
      
      setMessage(`✅ Risk #${selectedItem.index + 1} regenerated successfully!`);
      setDetailFeedback('');
    } catch (error) {
      console.error('❌ Error during regeneration:', error);
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const getDisplayRisks = () => {
    return projectStatus?.risks || loadedRisks;
  };

  const displayRisks = getDisplayRisks();

  return (
    <Center width="100%" minHeight="70vh" py={8}>
      <Container maxW="7xl" px={{ base: 4, md: 6 }}>
        {/* Header with gradient background */}
       <Box 
                 mb={8} 
                 textAlign="center"
                 py={6}
                 px={4}
                 borderRadius="xl"
                 bgGradient="to-r"
                 gradientFrom="blue.50"
                 gradientTo="purple.50"
                 _dark={{
                   gradientFrom: "blue.900",
                   gradientTo: "purple.900"
                 }}
               >
         <Heading 
                     size="xl" 
                     mb={3}
                     bgGradient="to-r"
                     gradientFrom="blue.500"
                     gradientTo="blue.500"
                     bgClip="text"
                     fontWeight="bold"
                   >
                     Risk Management
                   </Heading>
                   <Text 
                     color="fg.muted" 
                     fontSize="lg"
                     maxW="2xl"
                     mx="auto"
                   >
            Load, analyze, and manage project risks with intelligent insights
          </Text>
        </Box>
        

        {/* Message Alert */}
         {message && (
      <BottomFadingPopup
        message={message}
        duration={4000}
        onClose={() => setMessage(null)}
      />
    )}

        {/* Load Risks Card */}
        <Card.Root size="lg" borderRadius="2xl" mb={6} boxShadow="md">
          <Card.Header 
            bg="bg.muted"
            borderBottomWidth="1px"
            borderColor="border.subtle"
            py={6}
          >
            <HStack gap={4}>
              <Box
                p={3}
                borderRadius="xl"
                bg="blue.100"
                color="blue.600"
                _dark={{
                  bg: "blue.900",
                  color: "blue.200"
                }}
              >
                <FaDatabase size={24} />
              </Box>
              <Box flex={1}>
                <Card.Title fontSize="xl" fontWeight="bold">
                  Load Risks from Database
                </Card.Title>
                <Text fontSize="md" color="fg.muted" mt={1}>
                  Select a project to load existing risks from the database
                </Text>
              </Box>
            </HStack>
          </Card.Header>
          <Card.Body style={{ padding: "2rem" }}>
  <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
    {/* Title */}
    <div>
      <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem", color: "#2D3748" }}>
        Select Project
      </h3>

      {/* Dropdown + Button Row */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        {/* Dropdown */}
        <select
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          style={{
            flex: 1,
            padding: "0.75rem 1rem",
            fontSize: "1rem",
            border: "1px solid #CBD5E0",
            borderRadius: "0.75rem",
            backgroundColor: "#fff",
            color: "#2D3748",
            boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
            outline: "none",
            transition: "border-color 0.2s ease, box-shadow 0.2s ease",
          }}
          onFocus={(e) => (e.target.style.borderColor = "#3182CE")}
          onBlur={(e) => (e.target.style.borderColor = "#CBD5E0")}
        >
          <option value="">-- Select a project --</option>
          {availableProjects.map((project, index) => (
            <option key={index} value={project}>
              {project}
            </option>
          ))}
        </select>

        {/* Load Button */}
        <button
          onClick={() => loadRisksFromNeo4j()}
          disabled={loading || !projectName.trim()}
          style={{
            padding: "0.75rem 1.5rem",
            backgroundColor: loading ? "#A0AEC0" : "#3182CE",
            color: "#fff",
            border: "none",
            borderRadius: "0.75rem",
            fontSize: "1rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: loading || !projectName.trim() ? "not-allowed" : "pointer",
            transition: "background-color 0.2s ease, transform 0.1s ease",
            boxShadow: "0 2px 6px rgba(49,130,206,0.3)",
          }}
          onMouseEnter={(e) => !loading && (e.currentTarget.style.backgroundColor = "#2B6CB0")}
          onMouseLeave={(e) => !loading && (e.currentTarget.style.backgroundColor = "#3182CE")}
          onMouseDown={(e) => !loading && (e.currentTarget.style.transform = "scale(0.98)")}
          onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ marginRight: "8px" }}></span> Loading...
            </>
          ) : (
            <>
              <FaDatabase style={{ marginRight: "10px", fontSize: "18px" }} />
              Load Risks
            </>
          )}
        </button>
      </div>

      {/* Status Text */}
      <p style={{ fontSize: "0.9rem", color: "#718096", marginTop: "0.75rem" }}>
        {availableProjects.length > 0
          ? `${availableProjects.length} projects available in database`
          : "No projects found in database"}
      </p>
    </div>

    {/* Success Message */}
    {/* {loadedRisks.length > 0 && (
      <div
        style={{
          padding: "1rem",
          borderRadius: "0.75rem",
          backgroundColor: "#F0FFF4",
          border: "1px solid #9AE6B4",
          color: "#22543D",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <strong>✓</strong>
        <span>
          Loaded {loadedRisks.length} risks from "<strong>{projectName}</strong>"
        </span>
      </div>
    )} */}
  </div>
</Card.Body>

        </Card.Root>

        {displayRisks.length > 0 && (
          <Stack gap={6}>
            {/* Bulk Actions */}
            {selectedRisks.size > 0 && (
              <Card.Root borderRadius="2xl" borderWidth="2px" borderColor="yellow.300" boxShadow="lg">
                <Card.Header 
                  bg="yellow.50" 
                  borderBottomWidth="2px" 
                  borderColor="yellow.200"
                  py={6}
                  _dark={{
                    bg: "yellow.950"
                  }}
                >
                  <HStack gap={4}>
                    <Box
                      p={3}
                      borderRadius="xl"
                      bg="yellow.200"
                      color="yellow.800"
                    >
                      <FaTasks size={24} />
                    </Box>
                    <Box flex={1}>
                      <Card.Title fontSize="2xl" fontWeight="bold" color="fg">
                        Bulk Actions
                      </Card.Title>
                      <Text fontSize="md" color="fg.muted" mt={1}>
                        {selectedRisks.size} risk{selectedRisks.size > 1 ? 's' : ''} selected
                      </Text>
                    </Box>
                  </HStack>
                </Card.Header>
                
                <Card.Body py={6}>
                  <Stack gap={5}>
                    <Stack direction={{ base: 'column', lg: 'row' }} gap={4} align="start">
                      <Box flex={1}>
                        <Text fontSize="md" fontWeight="semibold" mb={3} color="fg">
                          Choose Action
                        </Text>
                        <NativeSelect.Root size="lg">
                          <NativeSelect.Field
                            value={riskAction}
                            onChange={(e) => setRiskAction(e.target.value)}
                            fontSize="md"
                            fontWeight="medium"
                          >
                            <option value="">-- Select an action --</option>
                            <option value="regenerate">🔄 Regenerate Selected Risks</option>
                            <option value="regenerate-with-feedback">💬 Regenerate with Feedback</option>
                            <option value="update">💾 Update Selected in Neo4j</option>
                          </NativeSelect.Field>
                        </NativeSelect.Root>
                      </Box>

                      {riskAction === 'regenerate-with-feedback' && (
                        <Box flex={1} width="100%">
                          <Text fontSize="md" fontWeight="semibold" mb={3} color="fg">
                            Feedback for Regeneration
                          </Text>
                          <textarea
                            style={{
                              width: '100%',
                              padding: '14px',
                              border: '2px solid #e2e8f0',
                              borderRadius: '12px',
                              fontSize: '15px',
                              minHeight: '100px',
                              resize: 'vertical',
                              fontFamily: 'inherit'
                            }}
                            value={bulkFeedback}
                            onChange={(e) => setBulkFeedback(e.target.value)}
                            placeholder="Provide specific feedback to improve these risks..."
                          />
                        </Box>
                      )}
                    </Stack>

                    <HStack gap={3}>
                      <Button
                        colorPalette="yellow"
                        size="lg"
                        onClick={handleRiskAction}
                        disabled={loading || !riskAction || 
                          (riskAction === 'regenerate-with-feedback' && !bulkFeedback.trim())
                        }
                        px={8}
                        fontWeight="semibold"
                        fontSize="md"
                      >
                        {loading ? (
                          <>
                            <Spinner size="sm" mr={2} />
                            Processing...
                          </>
                        ) : (
                          <>
                            <FaSync style={{ marginRight: '10px', fontSize: '18px' }} />
                            {riskAction === 'regenerate-with-feedback' ? 'Regenerate with Feedback' : 'Apply Action'}
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => {
                          setSelectedRisks(new Set());
                          setRiskAction('');
                          setBulkFeedback('');
                        }}
                        px={8}
                        fontWeight="semibold"
                        fontSize="md"
                      >
                        <FaTrash style={{ marginRight: '10px', fontSize: '18px' }} />
                        Clear Selection
                      </Button>
                    </HStack>
                  </Stack>
                </Card.Body>
              </Card.Root>
            )}

            {/* Risks Table */}
            <Card.Root size="lg" borderRadius="2xl" boxShadow="lg">
              <Card.Header 
                bg="bg.muted"
                borderBottomWidth="1px"
                borderColor="border.subtle"
                py={6}
              >
                <Flex 
                  direction={{ base: 'column', lg: 'row' }}
                  justify="space-between" 
                  align={{ base: 'start', lg: 'center' }} 
                  gap={4}
                >
                  <HStack gap={4}>
                    <Box
                      p={3}
                      borderRadius="xl"
                      bg="red.100"
                      color="red.600"
                      _dark={{
                        bg: "red.900",
                        color: "red.200"
                      }}
                    >
                      <FaShieldAlt size={24} />
                    </Box>
                    <Box>
                      <Card.Title fontSize="2xl" fontWeight="bold">
                        {projectStatus?.risks ? 'Current Project Risks' : 'Loaded Risks'} 
                      </Card.Title>
                      <Text fontSize="md" color="fg.muted" mt={1}>
                        {displayRisks.length} total risk{displayRisks.length !== 1 ? 's' : ''} • {selectedRisks.size} selected
                      </Text>
                    </Box>
                  </HStack>
                  <HStack gap={3}>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={handleSelectAllRisks}
                      px={6}
                      fontWeight="semibold"
                      fontSize="md"
                    >
                      {selectedRisks.size === displayRisks.length ? (
                        <>
                          <FaCheckSquare style={{ marginRight: '10px', fontSize: '18px' }} />
                          Deselect All
                        </>
                      ) : (
                        <>
                          <FaSquare style={{ marginRight: '10px', fontSize: '18px' }} />
                          Select All
                        </>
                      )}
                    </Button>
                    {projectStatus?.risks && (
                      <Button
                        colorPalette="blue"
                        size="lg"
                        onClick={handleRegenerateAllRisks}
                        disabled={loading}
                        px={6}
                        fontWeight="semibold"
                        fontSize="md"
                      >
                        {loading ? (
                          <>
                            <Spinner size="sm" mr={2} />
                            Regenerating...
                          </>
                        ) : (
                          <>
                            <FaSync style={{ marginRight: '10px', fontSize: '18px' }} />
                            Regenerate All
                          </>
                        )}
                      </Button>
                    )}
                  </HStack>
                </Flex>
              </Card.Header>

              {/* Risks Table */}
              <Box overflowX="auto">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ 
                      background: 'linear-gradient(to right, #f9fafb, #f3f4f6)',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'center', 
                        width: '60px',
                        fontSize: '15px',
                        fontWeight: '600'
                      }}>
                        <input
                          type="checkbox"
                          checked={selectedRisks.size === displayRisks.length}
                          onChange={handleSelectAllRisks}
                          style={{ 
                            transform: 'scale(1.3)',
                            cursor: 'pointer'
                          }}
                        />
                      </th>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'center', 
                        width: '80px',
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#6b7280'
                      }}>
                        #
                      </th>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'left', 
                        minWidth: '450px',
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#6b7280'
                      }}>
                        <HStack gap={2}>
                          <FaExclamationTriangle color="#ef4444" size={16} />
                          <span>Risk Description</span>
                        </HStack>
                      </th>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'left', 
                        minWidth: '350px',
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#6b7280'
                      }}>
                        Associated Requirement
                      </th>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'center', 
                        width: '140px',
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#6b7280'
                      }}>
                        Severity
                      </th>
                      <th style={{ 
                        padding: '16px', 
                        textAlign: 'center', 
                        width: '160px',
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#6b7280'
                      }}>
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayRisks.map((risk, index) => {
                      const riskDescription = typeof risk === 'string' ? risk : risk.description;
                      const associatedRequirement = typeof risk === 'object' ? risk.requirement : 
                                                    (projectStatus?.requirements?.[index] || 'No associated requirement');
                      const isSelected = selectedRisks.has(index);
                      
                      return (
                        <tr 
                          key={index}
                          style={{
                            background: isSelected ? '#dbeafe' : index % 2 === 0 ? '#ffffff' : '#f9fafb',
                            borderBottom: '1px solid #e5e7eb',
                            transition: 'all 0.2s ease',
                            cursor: 'pointer'
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.background = '#eff6ff';
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) e.currentTarget.style.background = index % 2 === 0 ? '#ffffff' : '#f9fafb';
                          }}
                        >
                          <td style={{ padding: '16px', textAlign: 'center' }}>
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleRiskSelect(index)}
                              style={{ 
                                transform: 'scale(1.3)',
                                cursor: 'pointer'
                              }}
                            />
                          </td>
                          <td style={{ padding: '16px', textAlign: 'center' }}>
                            <Badge
                              bg="gray.100"
                              color="fg"
                              borderRadius="lg"
                              px={3}
                              py={1.5}
                              fontWeight="700"
                              fontSize="md"
                            >
                              {index + 1}
                            </Badge>
                          </td>
                          <td 
                            style={{ 
                              padding: '16px',
                              fontSize: '15px',
                              lineHeight: '1.6',
                              minWidth: '450px'
                            }}
                            onClick={() => handleItemClick(index)}
                          >
                            <Text 
                              color="fg" 
                              fontWeight="medium"
                              _hover={{ color: 'blue.600', textDecoration: 'underline' }}
                            >
                              {riskDescription}
                            </Text>
                          </td>
                          <td style={{ padding: '16px' }}>
                            <Text color="fg.muted" fontSize="14px" lineHeight="1.5">
                              {associatedRequirement}
                            </Text>
                          </td>
                          <td style={{ padding: '16px', textAlign: 'center' }}>
                            <NativeSelect.Root size="md">
                              <NativeSelect.Field
                                defaultValue="medium"
                                onChange={(e) => {
                                  console.log(`Updated severity for risk ${index} to ${e.target.value}`);
                                }}
                                fontSize="14px"
                                fontWeight="medium"
                              >
                                <option value="low">🟢 Low</option>
                                <option value="medium">🟡 Medium</option>
                                <option value="high">🟠 High</option>
                                <option value="critical">🔴 Critical</option>
                              </NativeSelect.Field>
                            </NativeSelect.Root>
                          </td>
                          <td style={{ padding: '16px', textAlign: 'center' }}>
                            <HStack gap={2} justify="center">
                              <IconButton
                                size="md"
                                variant="outline"
                                onClick={() => handleItemClick(index)}
                                title="View details"
                                colorPalette="blue"
                              >
                                📋
                              </IconButton>
                              <IconButton
                                size="md"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    await requirementsAPI.updateSingleRisk(
                                      projectStatus?.thread_id || 'loaded_risks',
                                      index,
                                      riskDescription,
                                      associatedRequirement
                                    );
                                    setMessage('✅ Risk updated in Neo4j successfully!');
                                  } catch (error) {
                                    setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
                                  }
                                }}
                                title="Update in Neo4j"
                                colorPalette="green"
                              >
                                💾
                              </IconButton>
                            </HStack>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </Box>

              <Card.Footer 
                bg="gray.50" 
                borderTopWidth="2px" 
                borderColor="gray.200"
                _dark={{
                  bg: "gray.900"
                }}
              >
                <Flex 
                  direction={{ base: 'column', md: 'row' }}
                  justify="space-between" 
                  align="center" 
                  gap={4} 
                  p={5}
                >
                  <HStack gap={4} color="fg.muted" fontSize="md" fontWeight="medium">
                    <Text>
                      {projectStatus?.thread_id ? `📁 Project: ${projectStatus.thread_id}` : '📚 Loaded from Database'}
                    </Text>
                    <Text>•</Text>
                    <Text>
                      Selected: <strong style={{ color: '#3b82f6' }}>{selectedRisks.size}</strong> of <strong>{displayRisks.length}</strong>
                    </Text>
                  </HStack>
                  <Text color="fg.muted" fontSize="sm" fontWeight="medium">
                    💡 Click on any risk to provide feedback and regenerate
                  </Text>
                </Flex>
              </Card.Footer>
            </Card.Root>
          </Stack>
        )}

        {/* Detail Card Modal */}
        {selectedItem && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '24px',
              maxWidth: '800px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'auto',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
            }}>
              <div style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                padding: '24px 32px',
                borderRadius: '24px 24px 0 0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <h3 style={{
                  fontSize: '24px',
                  fontWeight: 'bold',
                  color: 'white',
                  margin: 0
                }}>
                  🛡️ Risk #{selectedItem.index + 1}
                </h3>
                <button
                  onClick={() => setSelectedItem(null)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.2)',
                    border: 'none',
                    color: 'white',
                    fontSize: '28px',
                    cursor: 'pointer',
                    borderRadius: '12px',
                    width: '40px',
                    height: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.3)'}
                  onMouseLeave={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
                >
                  ×
                </button>
              </div>

              <div style={{ padding: '32px' }}>
                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    fontSize: '15px',
                    fontWeight: '700',
                    color: '#374151',
                    marginBottom: '12px',
                    display: 'block'
                  }}>
                    📋 Associated Requirement:
                  </label>
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '12px',
                    border: '2px solid #e5e7eb',
                    fontSize: '15px',
                    lineHeight: '1.6',
                    color: '#1f2937'
                  }}>
                    {selectedItem.requirement}
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    fontSize: '15px',
                    fontWeight: '700',
                    color: '#374151',
                    marginBottom: '12px',
                    display: 'block'
                  }}>
                    ⚠️ Current Risk:
                  </label>
                  <div style={{
                    padding: '16px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '12px',
                    border: '2px solid #fbbf24',
                    fontSize: '15px',
                    lineHeight: '1.6',
                    color: '#92400e'
                  }}>
                    {selectedItem.content}
                  </div>
                </div>

                {/* Test Cases Section */}
                {testCases[selectedItem.index] && testCases[selectedItem.index].length > 0 && (
                  <div style={{ marginBottom: '24px' }}>
                    <label style={{
                      fontSize: '15px',
                      fontWeight: '700',
                      color: '#374151',
                      marginBottom: '12px',
                      display: 'block'
                    }}>
                      ✅ Related Test Cases ({testCases[selectedItem.index].length}):
                    </label>
                    <div style={{
                      padding: '16px',
                      backgroundColor: '#d1fae5',
                      borderRadius: '12px',
                      border: '2px solid #10b981',
                      maxHeight: '200px',
                      overflowY: 'auto'
                    }}>
                      {testCases[selectedItem.index].map((testCase, idx) => (
                        <div key={idx} style={{
                          marginBottom: idx < testCases[selectedItem.index].length - 1 ? '12px' : '0',
                          paddingBottom: idx < testCases[selectedItem.index].length - 1 ? '12px' : '0',
                          borderBottom: idx < testCases[selectedItem.index].length - 1 ? '1px solid #6ee7b7' : 'none'
                        }}>
                          <div style={{
                            fontSize: '13px',
                            fontWeight: '700',
                            color: '#047857',
                            marginBottom: '4px'
                          }}>
                            {testCase.test_id}
                          </div>
                          <div style={{
                            fontSize: '14px',
                            color: '#065f46',
                            lineHeight: '1.5'
                          }}>
                            {testCase.description}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ marginBottom: '28px' }}>
                  <label style={{
                    fontSize: '15px',
                    fontWeight: '700',
                    color: '#374151',
                    marginBottom: '12px',
                    display: 'block'
                  }}>
                    💬 Feedback for Regeneration:
                  </label>
                  <textarea
                    value={detailFeedback}
                    onChange={(e) => setDetailFeedback(e.target.value)}
                    placeholder="Provide specific feedback to improve this risk..."
                    style={{
                      width: '100%',
                      padding: '16px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      fontSize: '15px',
                      minHeight: '120px',
                      resize: 'vertical',
                      fontFamily: 'inherit',
                      lineHeight: '1.6',
                      transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>

                <div style={{
                  display: 'flex',
                  gap: '12px',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    onClick={() => setSelectedItem(null)}
                    style={{
                      padding: '12px 28px',
                      fontSize: '15px',
                      fontWeight: '600',
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      backgroundColor: 'white',
                      color: '#374151',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = '#f3f4f6';
                      e.target.style.borderColor = '#d1d5db';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'white';
                      e.target.style.borderColor = '#e5e7eb';
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRegenerateWithFeedback}
                    disabled={detailLoading || !detailFeedback.trim()}
                    style={{
                      padding: '12px 28px',
                      fontSize: '15px',
                      fontWeight: '600',
                      border: 'none',
                      borderRadius: '12px',
                      backgroundColor: detailLoading || !detailFeedback.trim() ? '#d1d5db' : '#3b82f6',
                      color: 'white',
                      cursor: detailLoading || !detailFeedback.trim() ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      opacity: detailLoading || !detailFeedback.trim() ? 0.6 : 1
                    }}
                    onMouseEnter={(e) => {
                      if (!detailLoading && detailFeedback.trim()) {
                        e.target.style.backgroundColor = '#2563eb';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!detailLoading && detailFeedback.trim()) {
                        e.target.style.backgroundColor = '#3b82f6';
                      }
                    }}
                  >
                    {detailLoading ? '🔄 Regenerating...' : '🚀 Regenerate Risk'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </Container>
    </Center>
  );
};

export default RisksPanel;