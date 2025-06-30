import { useState } from "react";
import Sidebar from "./Sidebar";
import { useTheme } from "~/contexts/ThemeContext";
import type { User } from "~/types";

interface AppLayoutProps {
  children: React.ReactNode;
  user?: User | null;
  onLogout?: () => void;
  title?: string;
  subtitle?: string;
}

const AppLayout = ({ 
  children, 
  user, 
  onLogout,
  title,
  subtitle
}: AppLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-var-primary flex">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isAuthenticated={!!user}
        user={user}
        onLogout={onLogout}
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col lg:ml-0 relative">
        {/* Mobile menu button (floating) */}
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden fixed top-4 right-4 z-40 p-3 bg-var-card border border-var-color rounded-lg hover:bg-var-hover transition-colors shadow-lg"
        >
          <svg className="h-6 w-6 text-var-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          {title && (
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-var-primary">
                {title}
              </h1>
              {subtitle && (
                <p className="text-var-secondary mt-2">{subtitle}</p>
              )}
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;