import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "~/lib/utils";
import type { NotificationState } from "~/types";

interface NotificationProps extends NotificationState {
  onRemove: (id: string) => void;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center";
}

const Notification = ({ 
  id, 
  message, 
  type, 
  duration = 5000, 
  onRemove,
  position = "top-right"
}: NotificationProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // 마운트 애니메이션
    setIsVisible(true);
    
    // 자동 제거
    const timer = setTimeout(() => {
      handleRemove();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration]);

  const handleRemove = () => {
    setIsLeaving(true);
    setTimeout(() => {
      onRemove(id);
    }, 300); // 애니메이션 지속시간과 맞춤
  };

  const typeStyles = {
    success: "bg-green-500 text-white",
    error: "bg-red-500 text-white",
    warning: "bg-yellow-500 text-white",
    info: "bg-blue-500 text-white",
  };

  const typeIcons = {
    success: "✓",
    error: "✕",
    warning: "⚠",
    info: "ℹ",
  };

  const positionStyles = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-center": "top-4 left-1/2 transform -translate-x-1/2",
  };

  const animationStyles = cn(
    "transform transition-all duration-300 ease-in-out",
    isVisible && !isLeaving ? "translate-x-0 opacity-100" : "translate-x-full opacity-0",
    position.includes("left") && (isVisible && !isLeaving ? "translate-x-0" : "-translate-x-full")
  );

  const notificationContent = (
    <div 
      className={cn(
        "fixed z-50 flex items-center max-w-sm w-full p-4 rounded-lg shadow-lg",
        positionStyles[position],
        typeStyles[type],
        animationStyles
      )}
    >
      <div className="flex items-center">
        <span className="mr-3 text-lg">
          {typeIcons[type]}
        </span>
        <p className="text-sm font-medium flex-1">{message}</p>
        <button
          onClick={handleRemove}
          className="ml-3 flex-shrink-0 text-lg opacity-70 hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    </div>
  );

  return typeof window !== "undefined" 
    ? createPortal(notificationContent, document.body)
    : null;
};

export default Notification;