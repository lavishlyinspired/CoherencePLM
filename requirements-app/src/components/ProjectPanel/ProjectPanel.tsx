import React, { useState, useEffect } from 'react';
import { LuRefreshCw, LuDatabase, LuHardDrive } from 'react-icons/lu';
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
import { requirementsAPI } from '../../services/api';
import { FaFolder } from 'react-icons/fa';

interface ProjectPanelProps {
  setProjectStatus: (status: any) => void;
}

const ProjectPanel: React.FC<ProjectPanelProps> = ({ setProjectStatus }) => {
  const [projects, setProjects] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [source, setSource] = useState('');
  const [selectedProject, setSelectedProject] = useState('');

  // Load all projects
  const loadProjects = async () => {
    setLoading(true);
    setMessage('');
    try {
      const result = await requirementsAPI.getAllProjects();
      if (result.projects && result.projects.length > 0) {
        setProjects(result.projects);
        setSource('Neo4j');
        setMessage(`Found ${result.count} projects in Neo4j`);
      } else {
        const fallback = await requirementsAPI.listProjects();
        setProjects(fallback.projects || []);
        setSource('Memory');
        setMessage(
          fallback.projects?.length > 0
            ? `Found ${fallback.projects.length} projects in memory`
            : 'No projects found'
        );
      }
    } catch (error: any) {
      try {
        const fallback = await requirementsAPI.listProjects();
        setProjects(fallback.projects || []);
        setSource('Memory');
        setMessage(`Using in-memory projects: ${fallback.projects?.length || 0} found`);
      } catch {
        setMessage(`Error loading projects: ${error.response?.data?.detail || error.message}`);
        setProjects([]);
        setSource('Error');
      }
    } finally {
      setLoading(false);
    }
  };

  // Load project details
  const loadProjectDetails = async (projectName: string) => {
    setLoading(true);
    setMessage('');
    try {
      const result = await requirementsAPI.getProjectDataFromNeo4j(projectName);
      const projectStatus = {
        thread_id: projectName,
        status: 'loaded',
        selected_keyword: result.selected_keyword || projectName,
        requirements: result.requirements || [],
        risks: result.risks || [],
        message: result.message,
      };
      setProjectStatus(projectStatus);
      setMessage(`Loaded project from Neo4j: ${projectName}`);
    } catch (error: any) {
      try {
        const fallback = await requirementsAPI.getProject(projectName);
        setProjectStatus(fallback);
        setMessage(`Loaded project from memory: ${projectName}`);
      } catch (err: any) {
        setMessage(`Error loading project: ${err.response?.data?.detail || err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleProjectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedProject(value);
    if (value) loadProjectDetails(value);
  };

  // Alert helpers
  const getAlertStatus = (): 'error' | 'warning' | 'info' | 'success' => {
    if (message.includes('Error')) return 'error';
    if (message.includes('memory') || message.includes('Using')) return 'warning';
    if (message.includes('Loaded')) return 'success';
    return 'info';
  };


  const getSourceColorPalette = () => {
    if (source === 'Neo4j') return 'teal';
    if (source === 'Memory') return 'orange';
    return 'red';
  };

  return (
    <Center width="100%" minHeight="60vh" py={8}>
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
            Project Management
          </Heading>
          <Text 
            color="fg.muted" 
            fontSize="lg"
            maxW="2xl"
            mx="auto"
          >
            Select a project to load its data from Neo4j or memory storage
          </Text>
        </Box>

        {/* Status Alert with smooth transition
        {message && (
          <Alert.Root 
            status={getAlertStatus()} 
            mb={6} 
            borderRadius="lg"
          >
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title fontWeight="semibold">Status Update</Alert.Title>
              <Alert.Description>{message}</Alert.Description>
            </Alert.Content>
          </Alert.Root>
        )} */}

        {/* Main Project Card with elevated design */}
        <Card.Root 
          size="lg"
          borderRadius="xl"
        >
          <Card.Header 
            bg="bg.muted"
            borderBottomWidth="1px"
            borderColor="border.subtle"
          >
            <Flex justify="space-between" align="center">
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
                             <FaFolder size={24} />
                           </Box>
                <Box>
                  <Card.Title fontSize="xl" fontWeight="bold">
                    Available Projects
                  </Card.Title>
                  {/* <Text fontSize="sm" color="fg.muted" mt={1}>
                    {projects.length > 0 
                      ? `${projects.length} project${projects.length > 1 ? 's' : ''} available`
                      : 'Loading projects...'}
                  </Text> */}
                </Box>
              </HStack>
              <HStack gap={2}>
                {projects.length > 0 && (
                  <Badge 
                    colorPalette={getSourceColorPalette()} 
                    variant="subtle"
                    px={3}
                    py={1}
                    borderRadius="full"
                    fontSize="sm"
                  >
                    <HStack gap={1.5}>
              
                      <Text>{source}</Text>
                    </HStack>
                  </Badge>
                )}
                <IconButton
                  aria-label="Refresh projects"
                  onClick={loadProjects}
                  disabled={loading}
                  size="sm"
                  variant="ghost"
                  colorPalette="blue"
                >
                  <LuRefreshCw />
                </IconButton>
              </HStack>
            </Flex>
          </Card.Header>

          <Card.Body py={8}>
            {loading && projects.length === 0 ? (
              <VStack py={12} gap={4}>
                <Spinner size="xl" color="blue.500" borderWidth="3px" />
                <VStack gap={1}>
                  <Text fontWeight="medium" fontSize="lg">Loading projects</Text>
                  <Text color="fg.muted" fontSize="sm">
                    Please wait while we fetch your data...
                  </Text>
                </VStack>
              </VStack>
            ) : projects.length === 0 ? (
              <Center py={12}>
                <VStack gap={4} maxW="md" textAlign="center">
                  <Box
                    p={4}
                    borderRadius="full"
                    bg="gray.subtle"
                    color="gray.fg"
                  >
                 
                  </Box>
                  <VStack gap={2}>
                    <Text fontWeight="semibold" fontSize="lg">
                      No Projects Found
                    </Text>
                    <Text color="fg.muted" fontSize="sm">
                      We couldn't find any projects in your database or memory storage.
                    </Text>
                  </VStack>
                  <Button 
                    onClick={loadProjects} 
                    colorPalette="blue" 
                    variant="surface"
                    size="md"
                    mt={2}
                  >
                    <LuRefreshCw />
                    Try Again
                  </Button>
                </VStack>
              </Center>
            ) : (
              <Stack gap={6} width="100%">
                <VStack gap={2}>
                  <Text 
                    fontSize="sm" 
                    color="fg.muted" 
                    fontWeight="medium"
                    letterSpacing="wide"
                    textTransform="uppercase"
                  >
                    Select a Project
                  </Text>
                  <Text fontSize="xs" color="fg.muted">
                    Choose from {projects.length} available project{projects.length > 1 ? 's' : ''}
                  </Text>
                </VStack>
                
                <Box width="100%" maxW="500px" mx="auto">
                  <NativeSelect.Root 
                    size="lg"
                    variant="outline"
                    disabled={loading}
                  >
                    <NativeSelect.Field
                      value={selectedProject}
                      onChange={handleProjectChange}
                      placeholder="-- Choose a project --"
                      fontWeight="medium"
                    >
                      {projects.map((project, idx) => (
                        <option key={idx} value={project}>
                          {project}
                        </option>
                      ))}
                    </NativeSelect.Field>
                    <NativeSelect.Indicator />
                  </NativeSelect.Root>
                </Box>

                {selectedProject && (
                  <Center mt={4}>
                    <Badge 
                      colorPalette="green" 
                      variant="subtle"
                      px={4}
                      py={2}
                      borderRadius="full"
                    >
                      Selected: {selectedProject}
                    </Badge>
                  </Center>
                )}
              </Stack>
            )}
          </Card.Body>
        </Card.Root>
      </Container>
    </Center>
  );
};

export default ProjectPanel;