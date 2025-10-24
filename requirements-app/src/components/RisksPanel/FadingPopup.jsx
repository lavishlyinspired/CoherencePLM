import React, { useEffect, useState } from "react";
import { Alert } from "@chakra-ui/react"; // adjust if using a custom Alert component

const BottomFadingPopup = ({ message, duration = 3000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false); // start fade-out
      setTimeout(onClose, 500); // remove completely after fade
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!isVisible) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "20px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 9999,
        minWidth: "300px",
        maxWidth: "400px",
        transition: "opacity 0.5s ease, transform 0.5s ease",
        opacity: isVisible ? 1 : 0,
      }}
    >
      <Alert.Root
        status={
          message.includes("❌") || message.includes("Error")
            ? "error"
            : message.includes("✅") ||
              message.includes("Success") ||
              message.includes("Loaded")
            ? "success"
            : "info"
        }
        borderRadius="lg"
        boxShadow="lg"
        padding="12px 16px"
      >
        <Alert.Content>
          <Alert.Title fontWeight="bold" fontSize="sm">
            {message.includes("❌") || message.includes("Error")
              ? "Error"
              : message.includes("✅") ||
                message.includes("Success") ||
                message.includes("Loaded")
              ? "Success"
              : "Info"}
          </Alert.Title>
          <Alert.Description fontSize="xs">{message}</Alert.Description>
        </Alert.Content>
      </Alert.Root>
    </div>
  );
};

export default BottomFadingPopup;
