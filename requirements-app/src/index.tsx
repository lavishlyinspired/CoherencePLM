import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider, createSystem,defaultSystem } from '@chakra-ui/react';
import App from './App';

const container = document.getElementById('app');
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


if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <ChakraProvider value={defaultSystem}>
        <App />
      </ChakraProvider>
    </React.StrictMode>
  );
} else {
  console.error('Failed to find the app element');
}
