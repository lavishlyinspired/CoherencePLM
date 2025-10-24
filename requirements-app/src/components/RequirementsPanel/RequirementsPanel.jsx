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
  NativeSelect
} from '@chakra-ui/react';
import { 
  FaPlus, 
  FaSave, 
  FaSync, 
  FaEye, 
  FaCheck, 
  FaCheckSquare, 
  FaSquare,
  FaListOl,
  FaExclamationTriangle,
  FaFlask,
  FaDatabase,
  FaProjectDiagram,
  FaKey,
  FaTasks,
  FaArrowLeft,
  FaSearch,
  FaEdit,
  FaTrash,
  FaCopy,
  FaInfoCircle,
  FaLightbulb,
  FaShieldAlt,
  FaCog
} from 'react-icons/fa';
import { requirementsAPI } from '../../services/api';
import DetailCard from '../DetailCard/DetailCard';

const RequirementsPanel = ({ projectStatus, setProjectStatus, setActivePanel }) => {
  const [requirementDesc, setRequirementDesc] = useState('');
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedKeywordIndex, setSelectedKeywordIndex] = useState(null);
  const [message, setMessage] = useState('');
  const [selectedRequirements, setSelectedRequirements] = useState(new Set());
  const [bulkAction, setBulkAction] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [bulkFeedback, setBulkFeedback] = useState('');
  const [testCases, setTestCases] = useState({});

  // Load test cases when project status changes
  useEffect(() => {
    if (projectStatus?.thread_id && projectStatus?.requirements) {
      loadAllTestCases();
    }
  }, [projectStatus?.thread_id, projectStatus?.requirements]);

  const loadAllTestCases = async () => {
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

  const handleCreateProject = async () => {
    if (!requirementDesc.trim()) {
      setMessage('Please enter a requirement description');
      return;
    }

    setLoading(true);
    setMessage('');
    
    try {
      const payload = { requirement_description: requirementDesc };
      if (projectName.trim()) {
        payload.project_name = projectName;
      }

      const result = await requirementsAPI.createProject(payload);
      setProjectStatus(result);
      setMessage('Project created successfully! Please select a keyword.');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectKeyword = async (index) => {
    if (!projectStatus?.thread_id) return;

    setLoading(true);
    setMessage('');
    
    try {
      const result = await requirementsAPI.selectKeyword(projectStatus.thread_id, index);
      setProjectStatus(result);
      setSelectedKeywordIndex(index);
      setMessage('Requirements and risks generated successfully!');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRequirementSelect = (index) => {
    const newSelection = new Set(selectedRequirements);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedRequirements(newSelection);
  };

  const handleSelectAllRequirements = () => {
    if (selectedRequirements.size === projectStatus.requirements.length) {
      setSelectedRequirements(new Set());
    } else {
      setSelectedRequirements(new Set(projectStatus.requirements.map((_, index) => index)));
    }
  };

  const handleBulkAction = async () => {
    if (!bulkAction || selectedRequirements.size === 0) {
      setMessage('Please select requirements and an action');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      if (bulkAction === 'regenerate') {
        const result = await requirementsAPI.regenerateRequirements(
          projectStatus.thread_id,
          Array.from(selectedRequirements)
        );
        setProjectStatus(result);
        setMessage(`Regenerated ${selectedRequirements.size} requirements`);
      } else if (bulkAction === 'save') {
        const selectedReq = projectStatus.requirements.filter((_, index) => 
          selectedRequirements.has(index)
        );
        const selectedRisks = projectStatus.risks.filter((_, index) => 
          selectedRequirements.has(index)
        );
        
        await requirementsAPI.saveSelectedRequirements(
          projectStatus.thread_id,
          selectedReq,
          selectedRisks,
          projectStatus.selected_keyword
        );
        setMessage(`Saved ${selectedRequirements.size} requirements to Neo4j`);
      }
      
      setSelectedRequirements(new Set());
      setBulkAction('');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkRegenerateWithFeedback = async () => {
    if (!bulkFeedback.trim()) {
      setMessage('Please provide feedback for regeneration');
      return;
    }

    if (selectedRequirements.size === 0) {
      setMessage('Please select requirements to regenerate');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const result = await requirementsAPI.regenerateWithFeedback({
        thread_id: projectStatus.thread_id,
        indexes: Array.from(selectedRequirements),
        feedback: bulkFeedback,
        regenerate_type: 'requirements'
      });

      setProjectStatus(result);
      setMessage(`Regenerated ${selectedRequirements.size} requirements with feedback!`);
      setSelectedRequirements(new Set());
      setBulkFeedback('');
      setBulkAction('');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAll = async () => {
    if (!projectStatus?.thread_id) return;

    setLoading(true);
    setMessage('');
    
    try {
      await requirementsAPI.saveProject(projectStatus.thread_id);
      setMessage('All requirements saved to Neo4j successfully!');
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (index, type) => {
    setSelectedItem({
      index,
      type,
      content: type === 'requirement' 
        ? projectStatus.requirements[index]
        : projectStatus.risks[index]
    });
  };

  const handleDetailUpdate = (updatedData) => {
    console.log('🔍 [DEBUG] handleDetailUpdate called with:', updatedData);
    setProjectStatus(updatedData);
    setSelectedItem(null);
  };

  const generateTestCasesForRequirement = async (reqIndex) => {
    if (!projectStatus?.thread_id) return;

    setLoading(true);
    try {
      await requirementsAPI.generateTestCases(projectStatus.thread_id, reqIndex);
      const result = await requirementsAPI.getTestCases(projectStatus.thread_id, reqIndex);
      setTestCases(prev => ({
        ...prev,
        [reqIndex]: result.test_cases || []
      }));
      setMessage(`Generated test cases for requirement ${reqIndex + 1}`);
    } catch (error) {
      setMessage(`Error generating test cases: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getTestCasesCount = (reqIndex) => {
    return testCases[reqIndex] ? testCases[reqIndex].length : 0;
  };

  return (
    <Center width="100%" minHeight="70vh" py={8}>
      <Container maxW="7xl" px={{ base: 4, md: 6 }}>
        {/* Header with gradient background - Matching ProjectPanel */}
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
            Requirements Management
          </Heading>
          <Text 
            color="fg.muted" 
            fontSize="lg"
            maxW="2xl"
            mx="auto"
          >
            Create, select, and manage individual requirements
          </Text>
        </Box>

        {/* Message Alert */}
        {message && (
          <Alert.Root 
            status={message.includes('Error') ? 'error' : 'success'}
            mb={6}
            borderRadius="lg"
          >
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title fontWeight="semibold">
                {message.includes('Error') ? 'Error' : 'Success'}
              </Alert.Title>
              <Alert.Description>{message}</Alert.Description>
            </Alert.Content>
          </Alert.Root>
        )}

        {/* Step 1: Create Project */}
        {!projectStatus && (
          <Card.Root size="lg" borderRadius="xl">
            <Card.Header 
              bg="bg.muted"
              borderBottomWidth="1px"
              borderColor="border.subtle"
            >
              <HStack gap={3}>
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
                             <FaEdit size={24} />
                           </Box>
                <Box>
                  <Card.Title fontSize="xl" fontWeight="bold">
                    Requirement Description
                  </Card.Title>
                  <Text fontSize="sm" color="fg.muted" mt={1}>
                    Start by describing your requirements
                  </Text>
                </Box>
              </HStack>
            </Card.Header>
            
            <Card.Body py={8}>
              <Stack gap={6}>
                <Box>
                  
                  <textarea
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      fontSize: '14px',
                      minHeight: '120px',
                      resize: 'vertical'
                    }}
                    value={requirementDesc}
                    onChange={(e) => setRequirementDesc(e.target.value)}
                    placeholder="Describe your requirements here... Be as specific as possible for better results."
                    disabled={loading}
                  />
                </Box>

                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2} color="fg">
                    Project Name (Optional)
                  </Text>
                  <input
                    type="text"
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      fontSize: '14px'
                    }}
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Enter project name or leave blank for auto-generation"
                    disabled={loading}
                  />
                </Box>

                <Button
                  colorPalette="blue"
                  size="lg"
                  onClick={handleCreateProject}
                  disabled={loading || !requirementDesc.trim()}
                  width="100%"
                >
                  {loading ? (
                    <Spinner size="sm" mr={2} />
                  ) : (
                    <FaPlus style={{ marginRight: '8px' }} />
                  )}
                  {loading ? 'Creating Project...' : 'Create Project'}
                </Button>
              </Stack>
            </Card.Body>
          </Card.Root>
        )}

        {/* Step 2: Select Keyword */}
        {projectStatus?.keywords && !projectStatus?.requirements && (
          <Card.Root size="lg" borderRadius="xl">
            <Card.Header 
              bg="bg.muted"
              borderBottomWidth="1px"
              borderColor="border.subtle"
            >
              <HStack gap={3}>
                <Box
                  p={2}
                  borderRadius="lg"
                  bg="purple.subtle"
                  color="purple.fg"
                >
                  <FaKey />
                </Box>
                <Box>
                  <Card.Title fontSize="xl" fontWeight="bold">
                    Select Keyword
                  </Card.Title>
                  <Text fontSize="sm" color="fg.muted" mt={1}>
                    Choose the most relevant keyword for your requirements
                  </Text>
                </Box>
              </HStack>
            </Card.Header>
            
            <Card.Body py={8}>
              <Stack gap={4}>
                {projectStatus.keywords.map((keyword, index) => (
                  <Box
                    key={index}
                    p={4}
                    border="2px solid"
                    borderColor={selectedKeywordIndex === index ? "green.500" : "gray.200"}
                    borderRadius="lg"
                    bg={selectedKeywordIndex === index ? "green.50" : "white"}
                    cursor="pointer"
                    onClick={() => handleSelectKeyword(index)}
                    transition="all 0.2s"
                    _hover={{
                      borderColor: "purple.500",
                      shadow: "md"
                    }}
                  >
                    <Flex justify="space-between" align="center">
                      <Text fontWeight="semibold" color="fg">
                        {keyword}
                      </Text>
                      <Box
                        w={6}
                        h={6}
                        borderRadius="full"
                        border="2px solid"
                        borderColor={selectedKeywordIndex === index ? "green.500" : "gray.300"}
                        bg={selectedKeywordIndex === index ? "green.500" : "transparent"}
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        {selectedKeywordIndex === index && (
                          <FaCheck size={12} color="white" />
                        )}
                      </Box>
                    </Flex>
                    <Text fontSize="sm" color="fg.muted" mt={2}>
                      Click to select and generate requirements
                    </Text>
                  </Box>
                ))}
              </Stack>
            </Card.Body>
          </Card.Root>
        )}

        {/* Step 3: Requirements and Risks Table */}
        {projectStatus?.requirements && projectStatus?.risks && (
          <Stack gap={6}>
            {/* Bulk Actions */}
            {selectedRequirements.size > 0 && (
              <Card.Root borderRadius="xl" borderColor="yellow.200">
                <Card.Header bg="yellow.50" borderBottomWidth="1px" borderColor="yellow.200">
                  <HStack gap={3}>
                    <Box
                      p={2}
                      borderRadius="lg"
                      bg="yellow.100"
                      color="yellow.600"
                    >
                      <FaTasks />
                    </Box>
                    <Box>
                      <Card.Title fontSize="lg" fontWeight="bold" color="fg">
                        Selected {selectedRequirements.size} requirement(s)
                      </Card.Title>
                    </Box>
                  </HStack>
                </Card.Header>
                
                <Card.Body py={6}>
                  <Stack gap={4}>
                    <Stack direction={{ base: 'column', md: 'row' }} gap={4} align="start">
                      <Box flex={1}>
                        <Text fontSize="sm" fontWeight="medium" mb={2} color="fg">
                          Bulk Action
                        </Text>
                        <NativeSelect.Root>
                          <NativeSelect.Field
                            value={bulkAction}
                            onChange={(e) => setBulkAction(e.target.value)}
                          >
                            <option value="">Select action...</option>
                            <option value="regenerate">Regenerate Selected</option>
                            <option value="regenerate-with-feedback">Regenerate with Feedback</option>
                            <option value="save">Save Selected to Neo4j</option>
                          </NativeSelect.Field>
                        </NativeSelect.Root>
                      </Box>

                      {bulkAction === 'regenerate-with-feedback' && (
                        <Box flex={1} width="100%">
                          <Text fontSize="sm" fontWeight="medium" mb={2} color="fg">
                            Feedback for regeneration
                          </Text>
                          <textarea
                            style={{
                              width: '100%',
                              padding: '12px',
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px',
                              fontSize: '14px',
                              minHeight: '80px',
                              resize: 'vertical'
                            }}
                            value={bulkFeedback}
                            onChange={(e) => setBulkFeedback(e.target.value)}
                            placeholder="Provide specific feedback to improve these requirements..."
                          />
                        </Box>
                      )}
                    </Stack>

                    <HStack gap={3}>
                      <Button
                        colorPalette="yellow"
                        onClick={bulkAction === 'regenerate-with-feedback' 
                          ? handleBulkRegenerateWithFeedback 
                          : handleBulkAction
                        }
                        disabled={loading || !bulkAction || 
                          (bulkAction === 'regenerate-with-feedback' && !bulkFeedback.trim())
                        }
                      >
                        {loading ? (
                          <Spinner size="sm" mr={2} />
                        ) : (
                          <FaSync style={{ marginRight: '8px' }} />
                        )}
                        {bulkAction === 'regenerate-with-feedback' ? 'Regenerate with Feedback' : 'Apply Action'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSelectedRequirements(new Set());
                          setBulkAction('');
                          setBulkFeedback('');
                        }}
                      >
                        <FaTrash style={{ marginRight: '8px' }} />
                        Clear Selection
                      </Button>
                    </HStack>
                  </Stack>
                </Card.Body>
              </Card.Root>
            )}

            {/* Requirements Table */}
            <Card.Root size="lg" borderRadius="xl">
              <Card.Header 
                bg="bg.muted"
                borderBottomWidth="1px"
                borderColor="border.subtle"
              >
                <Flex justify="space-between" align="center" gap={4}>
                  <HStack gap={3}>
                    <Box
                      p={2}
                      borderRadius="lg"
                      bg="green.subtle"
                      color="green.fg"
                    >
                      <FaListOl />
                    </Box>
                    <Box>
                      <Card.Title fontSize="xl" fontWeight="bold">
                        Requirements, Risks and Tests
                      </Card.Title>
                      <Text fontSize="sm" color="fg.muted" mt={1}>
                        {projectStatus.requirements.length} requirements generated
                      </Text>
                    </Box>
                  </HStack>
                  <HStack gap={2}>
                    <Button
                      variant="outline"
                      onClick={handleSelectAllRequirements}
                    >
                      {selectedRequirements.size === projectStatus.requirements.length ? (
                        <FaCheckSquare style={{ marginRight: '8px' }} />
                      ) : (
                        <FaSquare style={{ marginRight: '8px' }} />
                      )}
                      {selectedRequirements.size === projectStatus.requirements.length 
                        ? 'Deselect All' 
                        : 'Select All'
                      }
                    </Button>
                    <Button
                      colorPalette="blue"
                      onClick={handleSaveAll}
                      disabled={loading}
                    >
                      {loading ? (
                        <Spinner size="sm" mr={2} />
                      ) : (
                        <FaSave style={{ marginRight: '2px' }} />
                      )}
                      Save All to Database
                    </Button>
                  </HStack>
                </Flex>
              </Card.Header>

              {/* Requirements Table */}
              <Box overflowX="auto">
                <table style={{ width: '100%', fontSize: '14px' }}>
                  <thead style={{ background: '#f9fafb' }}>
                    <tr>
                      <th style={{ padding: '12px 16px', textAlign: 'center', width: '48px' }}>
                        <input
                          type="checkbox"
                          checked={selectedRequirements.size === projectStatus.requirements.length}
                          onChange={handleSelectAllRequirements}
                          style={{ transform: 'scale(1.1)' }}
                        />
                      </th>
                      <th style={{ padding: '12px 16px', textAlign: 'center', width: '64px' }}>
                        <HStack gap={1} justify="center">
                          <FaListOl size={14} color="gray" />
                          <Text fontSize="sm" color="fg.muted">#</Text>
                        </HStack>
                      </th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', minWidth: '320px' }}>
                        <HStack gap={2}>
                          <FaLightbulb color="#eab308" />
                          <Text fontSize="sm" color="fg.muted">Requirement</Text>
                        </HStack>
                      </th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', minWidth: '320px' }}>
                        <HStack gap={2}>
                          <FaShieldAlt color="#ef4444" />
                          <Text fontSize="sm" color="fg.muted">Associated Risk</Text>
                        </HStack>
                      </th>
                      <th style={{ padding: '12px 16px', textAlign: 'center', width: '128px' }}>
                        <HStack gap={2} justify="center">
                          <FaFlask color="#8b5cf6" />
                          <Text fontSize="sm" color="fg.muted">Test Cases</Text>
                        </HStack>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {projectStatus.requirements.map((requirement, index) => (
                      <tr 
                        key={index}
                        style={{
                          background: selectedRequirements.has(index) ? '#dbeafe' : 'white',
                          transition: 'background-color 0.15s ease'
                        }}
                        _hover={{ background: '#eff6ff' }}
                      >
                        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={selectedRequirements.has(index)}
                            onChange={() => handleRequirementSelect(index)}
                            style={{ transform: 'scale(1.1)' }}
                          />
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                          <Badge
                            bg="gray.100"
                            color="fg"
                            borderRadius="md"
                            px={2}
                            py={1}
                            fontWeight="600"
                          >
                            {index + 1}
                          </Badge>
                        </td>
                        <td 
                          style={{ 
                            padding: '12px 16px',
                            cursor: 'pointer'
                          }}
                          onClick={() => handleItemClick(index, 'requirement')}
                        >
                          <HStack gap={3} align="start">
                            <FaLightbulb color="#eab308" style={{ marginTop: '4px', flexShrink: 0 }} />
                            <Text color="fg" _hover={{ color: 'blue.600' }}>
                              {requirement}
                            </Text>
                          </HStack>
                        </td>
                        <td 
                          style={{ 
                            padding: '12px 16px',
                            cursor: 'pointer'
                          }}
                          onClick={() => handleItemClick(index, 'risk')}
                        >
                          <HStack gap={3} align="start">
                            <FaShieldAlt color="#ef4444" style={{ marginTop: '4px', flexShrink: 0 }} />
                            <Text color="fg" _hover={{ color: 'blue.600' }}>
                              {projectStatus.risks && projectStatus.risks[index] ? projectStatus.risks[index] : 'No risk identified'}
                            </Text>
                          </HStack>
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                          <VStack gap={2}>
                            <Badge
                              bg={getTestCasesCount(index) > 0 ? "green.100" : "gray.100"}
                              color={getTestCasesCount(index) > 0 ? "green.800" : "gray.600"}
                              borderRadius="md"
                              px={2}
                              py={1}
                            >
                              <HStack gap={1}>
                                <FaFlask size={12} />
                                <Text fontSize="xs">
                                  {getTestCasesCount(index)} tests
                                </Text>
                              </HStack>
                            </Badge>
                            {getTestCasesCount(index) === 0 && (
                              <Button
                                size="xs"
                                colorPalette="blue"
                                onClick={() => generateTestCasesForRequirement(index)}
                                disabled={loading}
                              >
                                <FaPlus size={10} />
                                Generate
                              </Button>
                            )}
                          </VStack>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>

              <Card.Footer bg="gray.50" borderTopWidth="1px" borderColor="gray.200">
                <Flex justify="space-between" align="center" gap={4} p={4}>
                  <HStack gap={4} color="fg.muted" fontSize="sm">
                    <HStack gap={2}>
                      <FaProjectDiagram color="#3b82f6" />
                      <Text>Project: <strong>{projectStatus.thread_id}</strong></Text>
                    </HStack>
                    <HStack gap={2}>
                      <FaKey color="#8b5cf6" />
                      <Text>Keyword: <strong>{projectStatus.selected_keyword}</strong></Text>
                    </HStack>
                    <HStack gap={2}>
                      <FaCheckSquare color="#10b981" />
                      <Text>Selected: <strong>{selectedRequirements.size}</strong> of <strong>{projectStatus.requirements.length}</strong></Text>
                    </HStack>
                  </HStack>
                  <Text color="fg.muted" fontSize="sm">
                    💡 Click on any requirement or risk to provide feedback and regenerate
                  </Text>
                </Flex>
              </Card.Footer>
            </Card.Root>
          </Stack>
        )}

        {/* Detail Card Overlay */}
        {selectedItem && (
          <DetailCard
            item={selectedItem}
            projectStatus={projectStatus}
            onClose={() => setSelectedItem(null)}
            onUpdate={handleDetailUpdate}
          />
        )}
      </Container>
    </Center>
  );
};

export default RequirementsPanel;