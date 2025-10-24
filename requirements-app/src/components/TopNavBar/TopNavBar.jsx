// src/components/TopNavBar/TopNavBar.jsx
import React, { useState } from "react";
import {
  Box,
  Flex,
  Text,
  Input,
  InputGroup,
  IconButton,
  Button,
  Avatar,
  HStack,
  Spacer,
  Badge,
  Menu,
  Portal,
} from "@chakra-ui/react";
import { FiSearch, FiBell, FiUser, FiSun, FiMoon, FiSettings, FiLogOut } from "react-icons/fi";

const TopNavBar = () => {
  const [colorMode, setColorMode] = useState('light');
  
  const toggleColorMode = () => {
    setColorMode(colorMode === 'light' ? 'dark' : 'light');
  };
  
  // Static color values (replacing useColorModeValue)
  const navbarBg = 'white';
  const borderColor = 'gray.200';
  const textColor = 'gray.800';
  const hoverBg = 'gray.50';

  return (
    <Box
      as="header"
      bg={navbarBg}
      borderBottom="1px solid"
      borderColor={borderColor}
      px={6}
      py={4}
      boxShadow="sm"
      position="sticky"
      top={0}
      zIndex={10}
    >
      <Flex align="center" gap={6}>
        {/* Search - moved to left */}
       

        <Spacer />
 <InputGroup maxW="400px" startElement={<FiSearch color="gray.600" />}>
          <Input
            placeholder="Search requirements, risks, tests..."
            variant="outline"
            size="lg"
          />
        </InputGroup>
        {/* Requirements Manager text - shifted to right
      <Text fontSize="2xl" fontWeight="bold" whiteSpace="nowrap">
              Requirements Manager
            </Text> */}

        <Spacer />

        {/* Actions */}
        <HStack spacing={2}>
          {/* Theme Toggle */}
          <IconButton
            aria-label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}
            variant="ghost"
            size="sm"
            onClick={toggleColorMode}
            _hover={{ bg: hoverBg }}
          >
            {colorMode === 'light' ? <FiMoon /> : <FiSun />}
          </IconButton>

          {/* Notifications */}
          <Box position="relative">
            <IconButton
              aria-label="Notifications"
              variant="ghost"
              size="sm"
              _hover={{ bg: hoverBg }}
            >
              <FiBell />
            </IconButton>
            <Badge
              position="absolute"
              top="-1"
              right="-1"
              colorPalette="red"
              variant="solid"
              size="xs"
              borderRadius="full"
            >
              3
            </Badge>
          </Box>

          {/* User Menu */}
          <Menu.Root>
            <Menu.Trigger asChild>
              <Button
                variant="ghost"
                size="sm"
                p={1}
                _hover={{ bg: hoverBg }}
              >
                <Avatar.Root size="sm">
                  <Avatar.Fallback name="User" />
                </Avatar.Root>
              </Button>
            </Menu.Trigger>
            <Portal>
              <Menu.Positioner>
                <Menu.Content>
                  <Menu.Item value="profile">
                    <FiUser />
                    Profile
                  </Menu.Item>
                  <Menu.Item value="settings">
                    <FiSettings />
                    Settings
                  </Menu.Item>
                  <Menu.Separator />
                  <Menu.Item value="logout" color="red.500">
                    <FiLogOut />
                    Logout
                  </Menu.Item>
                </Menu.Content>
              </Menu.Positioner>
            </Portal>
          </Menu.Root>
        </HStack>
      </Flex>
    </Box>
  );
};

export default TopNavBar;