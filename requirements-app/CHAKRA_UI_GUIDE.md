# Chakra UI Complete Guide

## Overview
Chakra UI is a modern, accessible, and customizable React component library that provides a comprehensive set of components for building user interfaces. You already have Chakra UI v3 installed in your project!

## Key Features
- **Accessibility First**: All components are built with accessibility in mind
- **Dark Mode Support**: Built-in dark/light mode switching
- **Responsive Design**: Mobile-first responsive components
- **Customizable**: Easy theming and customization
- **TypeScript Support**: Full TypeScript support
- **Performance**: Optimized for performance

## Your Current Setup
You already have Chakra UI properly configured in your project:

```jsx
// src/index.tsx
import { ChakraProvider, createSystem, defaultSystem } from '@chakra-ui/react';

const customSystem = createSystem({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#e3f2ff" },
          100: { value: "#b3d4ff" },
          500: { value: "#3182ce" },
          700: { value: "#225ea8" },
        },
      },
    },
  },
});

<ChakraProvider value={defaultSystem}>
  <App />
</ChakraProvider>
```

## Basic Usage Patterns

### 1. Import Components
```jsx
import { Button, Card, Stack, Text, Heading } from '@chakra-ui/react';
```

### 2. Basic Component Structure
```jsx
function MyComponent() {
  return (
    <Card.Root>
      <Card.Header>
        <Heading size="lg">Card Title</Heading>
      </Card.Header>
      <Card.Body>
        <Text>Card content goes here</Text>
      </Card.Body>
      <Card.Footer>
        <Button>Action</Button>
      </Card.Footer>
    </Card.Root>
  );
}
```

### 3. Layout Components
```jsx
// Vertical Stack
<VStack spacing={4}>
  <Box>Item 1</Box>
  <Box>Item 2</Box>
</VStack>

// Horizontal Stack
<HStack spacing={4}>
  <Box>Item 1</Box>
  <Box>Item 2</Box>
</HStack>

// Grid Layout
<SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
  <Box>Grid Item 1</Box>
  <Box>Grid Item 2</Box>
  <Box>Grid Item 3</Box>
</SimpleGrid>
```

## Component Categories

### 1. Basic Components
- **Button**: Various styles, sizes, and states
- **Card**: Container with header, body, footer
- **Box**: Basic container component
- **Text**: Text display component
- **Heading**: Heading component with semantic levels
- **Image**: Image component with optimization
- **Icon**: Icon component
- **Avatar**: User avatar with fallback

### 2. Form Components
- **Input**: Text input fields
- **Textarea**: Multi-line text input
- **Select**: Dropdown selection
- **Checkbox**: Checkbox input
- **RadioGroup**: Radio button groups
- **Switch**: Toggle switch
- **Field**: Form field wrapper with label and error handling

### 3. Layout Components
- **Stack**: Vertical/horizontal stacking
- **HStack**: Horizontal stack
- **VStack**: Vertical stack
- **Flex**: Flexible box layout
- **Grid**: CSS Grid layout
- **SimpleGrid**: Simplified grid
- **Container**: Responsive container
- **Center**: Center content
- **Spacer**: Add space between elements

### 4. Data Display
- **Badge**: Status indicators
- **Stat**: Statistics display
- **Table**: Data tables
- **List**: List components
- **Code**: Code display
- **Kbd**: Keyboard key display
- **Progress**: Progress bars
- **Skeleton**: Loading placeholders

### 5. Feedback Components
- **Alert**: Alert messages
- **Toast**: Toast notifications
- **Spinner**: Loading spinner
- **Progress**: Progress indicators
- **Skeleton**: Loading skeletons

### 6. Navigation Components
- **Breadcrumb**: Navigation breadcrumbs
- **Tabs**: Tab navigation
- **Menu**: Dropdown menus
- **Pagination**: Page navigation
- **Steps**: Step indicators

### 7. Overlay Components
- **Modal**: Modal dialogs
- **Drawer**: Slide-out panels
- **Popover**: Popover content
- **Tooltip**: Tooltip content
- **HoverCard**: Hover content

## Styling and Theming

### 1. Color Palette System
```jsx
// Use semantic tokens for automatic dark mode
<Button colorPalette="blue">Blue Button</Button>
<Text color="fg.muted">Muted text</Text>
<Box bg="bg.subtle">Subtle background</Box>
```

### 2. Responsive Design
```jsx
// Responsive props
<Box 
  width={{ base: "100%", md: "50%", lg: "33%" }}
  fontSize={{ base: "sm", md: "md", lg: "lg" }}
>
  Responsive content
</Box>
```

### 3. Spacing System
```jsx
// Use spacing tokens
<VStack spacing={4}>  // 1rem spacing
<HStack gap={6}>      // 1.5rem spacing
<Box p={8}>           // 2rem padding
```

### 4. Size System
```jsx
// Component sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Text sizes
<Text textStyle="sm">Small text</Text>
<Text textStyle="md">Medium text</Text>
<Text textStyle="lg">Large text</Text>
```

## Dark Mode Support

### 1. Color Mode Hook
```jsx
import { useColorMode, useColorModeValue } from '@chakra-ui/react';

function MyComponent() {
  const { colorMode, toggleColorMode } = useColorMode();
  const bgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Box bg={bgColor}>
      <Button onClick={toggleColorMode}>
        Toggle {colorMode === 'light' ? 'Dark' : 'Light'} Mode
      </Button>
    </Box>
  );
}
```

### 2. Semantic Tokens
```jsx
// These automatically adapt to color mode
<Box bg="bg">Background</Box>
<Text color="fg">Foreground text</Text>
<Box borderColor="border">Border</Box>
```

## Form Handling

### 1. Field Components
```jsx
<Field.Root>
  <Field.Label>Email Address</Field.Label>
  <Input type="email" placeholder="Enter your email" />
  <Field.ErrorText>Please enter a valid email</Field.ErrorText>
  <Field.HelperText>We'll never share your email</Field.HelperText>
</Field.Root>
```

### 2. Form Validation
```jsx
const [email, setEmail] = useState('');
const [isValid, setIsValid] = useState(true);

<Field.Root invalid={!isValid}>
  <Field.Label>Email</Field.Label>
  <Input 
    value={email}
    onChange={(e) => {
      setEmail(e.target.value);
      setIsValid(e.target.value.includes('@'));
    }}
  />
  {!isValid && <Field.ErrorText>Invalid email format</Field.ErrorText>}
</Field.Root>
```

## Advanced Patterns

### 1. Compound Components
Many Chakra UI components use compound component patterns:
```jsx
// Card compound components
<Card.Root>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Body>Content</Card.Body>
  <Card.Footer>Footer</Card.Footer>
</Card.Root>

// Alert compound components
<Alert status="success">
  <Alert.Icon />
  <Alert.Title>Success!</Alert.Title>
  <Alert.Description>Operation completed</Alert.Description>
</Alert>
```

### 2. Portal Components
For overlays that need to render outside the component tree:
```jsx
<Modal.Root>
  <Modal.Backdrop />
  <Modal.Positioner>
    <Modal.Content>
      <Modal.Header>Title</Modal.Header>
      <Modal.Body>Content</Modal.Body>
    </Modal.Content>
  </Modal.Positioner>
</Modal.Root>
```

### 3. Custom Styling
```jsx
// Style props
<Box 
  bg="blue.500"
  color="white"
  p={4}
  borderRadius="md"
  boxShadow="lg"
  _hover={{ bg: "blue.600" }}
>
  Custom styled box
</Box>

// CSS-in-JS
<Box 
  css={{
    '&:hover': {
      transform: 'scale(1.05)',
    },
  }}
>
  Hover effect
</Box>
```

## Best Practices

### 1. Accessibility
- Always provide `aria-label` for icon buttons
- Use semantic HTML elements when possible
- Ensure proper color contrast
- Test with screen readers

### 2. Performance
- Use `React.memo` for expensive components
- Lazy load heavy components
- Optimize images with the `Image` component

### 3. Responsive Design
- Use responsive props for mobile-first design
- Test on different screen sizes
- Use semantic tokens for consistent theming

### 4. Component Composition
- Compose components rather than creating monolithic ones
- Use compound components for complex UI patterns
- Keep components focused and reusable

## Common Use Cases

### 1. Dashboard Layout
```jsx
function Dashboard() {
  return (
    <Box>
      <Flex>
        <Sidebar />
        <Box flex="1">
          <Header />
          <Main>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              <StatCard />
              <ChartCard />
              <TableCard />
            </SimpleGrid>
          </Main>
        </Box>
      </Flex>
    </Box>
  );
}
```

### 2. Form with Validation
```jsx
function ContactForm() {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  
  return (
    <Card.Root maxW="md">
      <Card.Header>
        <Card.Title>Contact Us</Card.Title>
      </Card.Header>
      <Card.Body>
        <VStack spacing={4}>
          <Field.Root invalid={!!errors.name}>
            <Field.Label>Name</Field.Label>
            <Input 
              value={formData.name || ''}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
            {errors.name && <Field.ErrorText>{errors.name}</Field.ErrorText>}
          </Field.Root>
          
          <Field.Root invalid={!!errors.email}>
            <Field.Label>Email</Field.Label>
            <Input 
              type="email"
              value={formData.email || ''}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
            />
            {errors.email && <Field.ErrorText>{errors.email}</Field.ErrorText>}
          </Field.Root>
        </VStack>
      </Card.Body>
      <Card.Footer>
        <Button width="full">Submit</Button>
      </Card.Footer>
    </Card.Root>
  );
}
```

### 3. Data Table with Actions
```jsx
function DataTable({ data }) {
  return (
    <TableContainer>
      <Table>
        <Thead>
          <Tr>
            <Th>Name</Th>
            <Th>Email</Th>
            <Th>Status</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {data.map((item) => (
            <Tr key={item.id}>
              <Td>{item.name}</Td>
              <Td>{item.email}</Td>
              <Td>
                <Badge colorPalette={item.status === 'active' ? 'green' : 'red'}>
                  {item.status}
                </Badge>
              </Td>
              <Td>
                <HStack spacing={2}>
                  <IconButton size="sm" aria-label="Edit">
                    <Icon><FiEdit /></Icon>
                  </IconButton>
                  <IconButton size="sm" aria-label="Delete">
                    <Icon><FiTrash2 /></Icon>
                  </IconButton>
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );
}
```

## Migration from v2 to v3

If you're upgrading from Chakra UI v2, here are the key changes:

### 1. Component Structure
- Components now use compound component patterns
- `Card` becomes `Card.Root`, `Card.Header`, etc.
- `Alert` becomes `Alert.Root`, `Alert.Icon`, etc.

### 2. Props Changes
- `colorScheme` becomes `colorPalette`
- `isDisabled` becomes `disabled`
- `isLoading` becomes `loading`

### 3. Theme System
- New token-based theming system
- Semantic tokens for automatic dark mode
- Improved customization options

## Resources

- **Documentation**: https://chakra-ui.com/docs
- **Components**: https://chakra-ui.com/docs/components
- **Examples**: Check the `ChakraUIExamples.jsx` component I created
- **GitHub**: https://github.com/chakra-ui/chakra-ui
- **Discord**: Join the Chakra UI Discord community

## Next Steps

1. **Explore the Examples**: Check out the `ChakraUIExamples.jsx` component I created
2. **Start Small**: Begin with basic components like `Button`, `Card`, and `Stack`
3. **Build Forms**: Practice with form components and validation
4. **Implement Layouts**: Use layout components for responsive design
5. **Add Interactions**: Implement modals, tooltips, and other overlay components
6. **Customize Theme**: Explore theming and customization options

Remember: Chakra UI is designed to be intuitive and accessible. Start with the basics and gradually explore more advanced features as you become comfortable with the library.
