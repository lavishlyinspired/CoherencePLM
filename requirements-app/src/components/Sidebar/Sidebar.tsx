"use client";
import React, { useState, useEffect, useRef } from "react";
import { 
  Box, 
  Flex, 
  Text, 
  VStack, 
  HStack, 
  Button, 
  Icon, 
  Separator,
  Badge,
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent
} from "@chakra-ui/react";
import {
  FiChevronLeft,
  FiChevronRight,
  FiFolder,
  FiEdit,
  FiAlertTriangle,
  FiCheckCircle,
  FiShare2,
  FiCode,
  FiPlay,
} from "react-icons/fi";

interface SidebarProps {
  activePanel: string;
  setActivePanel: (id: string) => void;
  projectStatus?: {
    thread_id: string;
    status: string;
    selected_keyword?: string;
  };
}

const Sidebar: React.FC<SidebarProps> = ({
  activePanel,
  setActivePanel,
  projectStatus,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  // Static color values (replacing useColorModeValue)
  const sidebarBg = 'white';
  const borderColor = 'gray.200';
  const textColor = 'gray.800';
  const hoverBg = 'gray.50';
  const activeBg = 'blue.50';
  const activeTextColor = 'blue.600';

  const menuItems = [
    { id: "projects", label: "Projects", icon: FiFolder, category: "main" },
    { id: "requirements", label: "Requirements", icon: FiEdit, category: "main" },
    { id: "risks", label: "Risks", icon: FiAlertTriangle, category: "main" },
    { id: "tests", label: "Tests", icon: FiCheckCircle, category: "main" },
    { id: "neo4jgraph", label: "Graph View", icon: FiShare2, category: "main" },
    { id: "chakra-examples", label: "Chakra UI Examples", icon: FiCode, category: "examples" },
    { id: "quick-start", label: "Quick Start", icon: FiPlay, category: "examples" },
  ];

  // Collapse sidebar when clicking outside
  useEffect(() => {
    // const handleClickOutside = (event: MouseEvent) => {
    //   if (
    //     sidebarRef.current &&
    //     !sidebarRef.current.contains(event.target as Node)
    //   ) {
    //     setCollapsed(true);
    //   }
    // };
    // document.addEventListener("mousedown", handleClickOutside);
    // return () => {
    //   document.removeEventListener("mousedown", handleClickOutside);
    // };
  }, []);

  return (
    <>
      {/* Sidebar */}
      <Flex
        ref={sidebarRef}
        direction="column"
        w={collapsed ? "60px" : "280px"}
        transition="width 0.3s ease-in-out"
        bg={sidebarBg}
        color={textColor}
        h="100vh"
        overflow="hidden"
        flexShrink={0}
        position="relative"
        borderRight="1px solid"
        borderColor={borderColor}
        boxShadow="sm"
      >
        {/* Header */}
        <Flex
          align="center"
          justify={collapsed ? "center" : "space-between"}
          p={4}
          borderBottom="1px solid"
          borderColor={borderColor}
          minH="64px"
        >
          {!collapsed && (
            <Text fontSize="lg" fontWeight="bold" whiteSpace="nowrap">
              Requirements Manager
            </Text>
          )}
        </Flex>

        {/* Menu Items */}
        <VStack align="stretch" gap={0} flex={1} p={2}>
          {/* Main Navigation */}
          <Box mb={2}>
            {!collapsed && (
              <Text fontSize="xs" fontWeight="semibold" color="gray.500" px={3} py={2} textTransform="uppercase" letterSpacing="wide">
                Main
              </Text>
            )}
            <VStack align="stretch" gap={1}>
              {menuItems.filter(item => item.category === "main").map((item) => (
                <Button
                  key={item.id}
                  variant="ghost"
                  justifyContent={collapsed ? "center" : "flex-start"}
                  h="40px"
                  px={collapsed ? 2 : 3}
                  bg={activePanel === item.id ? activeBg : "transparent"}
                  color={activePanel === item.id ? activeTextColor : textColor}
                  _hover={{ bg: hoverBg }}
                  onClick={() => setActivePanel(item.id)}
                  aria-label={collapsed ? item.label : undefined}
                >
                  {!collapsed && <Icon as={item.icon} boxSize={4} mr={2} />}
                  {!collapsed && item.label}
                  {collapsed && <Icon as={item.icon} boxSize={4} />}
                </Button>
              ))}
            </VStack>
          </Box>

          <Separator my={2} />

          {/* Examples Section */}
          <Box>
            {!collapsed && (
              <Text fontSize="xs" fontWeight="semibold" color="gray.500" px={3} py={2} textTransform="uppercase" letterSpacing="wide">
                Examples
              </Text>
            )}
            <VStack align="stretch" gap={1}>
              {menuItems.filter(item => item.category === "examples").map((item) => (
                <Button
                  key={item.id}
                  variant="ghost"
                  justifyContent={collapsed ? "center" : "flex-start"}
                  h="40px"
                  px={collapsed ? 2 : 3}
                  bg={activePanel === item.id ? activeBg : "transparent"}
                  color={activePanel === item.id ? activeTextColor : textColor}
                  _hover={{ bg: hoverBg }}
                  onClick={() => setActivePanel(item.id)}
                  aria-label={collapsed ? item.label : undefined}
                >
                  {!collapsed && <Icon as={item.icon} boxSize={4} mr={2} />}
                  {!collapsed && item.label}
                  {collapsed && <Icon as={item.icon} boxSize={4} />}
                </Button>
              ))}
            </VStack>
          </Box>
        </VStack>

        {/* Project Status Section */}
        {!collapsed && projectStatus && (
          <Box
            px={4}
            py={3}
            bg="gray.50"
            borderRadius="md"
            m={2}
            mt="auto"
            boxShadow="sm"
            border="1px solid"
            borderColor={borderColor}
          >
            {/* Header */}
            <Text
              fontSize="xs"
              fontWeight="bold"
              textTransform="uppercase"
              mb={2}
              color="gray.500"
              letterSpacing="wide"
            >
              Current Project
            </Text>

            {/* Project ID */}
            <Text fontSize="sm" fontWeight="semibold" mb={2} color={textColor}>
              {projectStatus.thread_id}
            </Text>

            {/* Status Badge */}
            {/* <Badge
              colorPalette={projectStatus.status === "loaded" ? "green" : "yellow"}
              variant="solid"
              size="sm"
              mb={2}
            >
              {projectStatus.status}
            </Badge> */}

            {/* Keyword Badge */}
            {projectStatus.selected_keyword && (
              <Badge
                colorPalette="teal"
                variant="subtle"
                size="sm"
                maxW="100%"
                overflow="hidden"
                textOverflow="ellipsis"
                whiteSpace="nowrap"
              >
                {projectStatus.selected_keyword}
              </Badge>
            )}
          </Box>
        )}

      </Flex>

      {/* Toggle Button */}
      <Box 
        position="fixed" 
        top="20px" 
        left={collapsed ? "70px" : "290px"} 
        zIndex={50}
        transition="left 0.3s ease-in-out"
      >
        <Button
          onClick={() => setCollapsed(!collapsed)}
          variant="outline"
          size="sm"
          minW="auto"
          p={2}
          bg={sidebarBg}
          borderColor={borderColor}
          _hover={{ bg: hoverBg }}
          boxShadow="sm"
        >
          <Icon as={collapsed ? FiChevronRight : FiChevronLeft} boxSize={4} />
        </Button>
      </Box>
    </>
  );
};

export default Sidebar;
