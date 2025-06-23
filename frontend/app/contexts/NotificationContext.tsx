import { createContext, useContext, useState, useCallback } from "react";
import Notification from "~/components/ui/Notification";
import { generateMockId } from "~/lib/utils";
import { NOTIFICATION_DURATION } from "~/lib/constants";
import type { NotificationState } from "~/types";

interface NotificationContextType {
  notifications: NotificationState[];
  addNotification: (notification: Omit<NotificationState, "id">) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  // 편의 메서드들
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: React.ReactNode;
  maxNotifications?: number;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center";
}

export const NotificationProvider = ({ 
  children, 
  maxNotifications = 5,
  position = "top-right"
}: NotificationProviderProps) => {
  const [notifications, setNotifications] = useState<NotificationState[]>([]);

  const addNotification = useCallback((notification: Omit<NotificationState, "id">) => {
    const newNotification: NotificationState = {
      ...notification,
      id: generateMockId(),
      duration: notification.duration || NOTIFICATION_DURATION.MEDIUM,
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev];
      // 최대 개수 제한
      return updated.slice(0, maxNotifications);
    });
  }, [maxNotifications]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // 편의 메서드들
  const showSuccess = useCallback((message: string, duration?: number) => {
    addNotification({ 
      message, 
      type: "success", 
      duration: duration || NOTIFICATION_DURATION.SHORT 
    });
  }, [addNotification]);

  const showError = useCallback((message: string, duration?: number) => {
    addNotification({ 
      message, 
      type: "error", 
      duration: duration || NOTIFICATION_DURATION.LONG 
    });
  }, [addNotification]);

  const showInfo = useCallback((message: string, duration?: number) => {
    addNotification({ 
      message, 
      type: "info", 
      duration: duration || NOTIFICATION_DURATION.MEDIUM 
    });
  }, [addNotification]);

  const showWarning = useCallback((message: string, duration?: number) => {
    addNotification({ 
      message, 
      type: "warning", 
      duration: duration || NOTIFICATION_DURATION.MEDIUM 
    });
  }, [addNotification]);

  const value: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showInfo,
    showWarning,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      
      {/* 알림 렌더링 */}
      <div className="fixed z-50 pointer-events-none">
        {notifications.map((notification) => (
          <Notification
            key={notification.id}
            {...notification}
            onRemove={removeNotification}
            position={position}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error("useNotification must be used within a NotificationProvider");
  }
  return context;
};

export default NotificationContext;