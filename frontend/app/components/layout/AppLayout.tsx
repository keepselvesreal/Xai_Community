import { useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import type { User } from "~/types";

interface AppLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  user?: User | null;
  onLogout?: () => void;
}

const AppLayout = ({ 
  children, 
  title, 
  subtitle, 
  user, 
  onLogout 
}: AppLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleMenuClick = () => {
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
        isAuthenticated={!!user}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        {/* Header */}
        <Header
          title={title}
          subtitle={subtitle}
          user={user}
          onMenuClick={handleMenuClick}
          onLogout={onLogout}
        />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;