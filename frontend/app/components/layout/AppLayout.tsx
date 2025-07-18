import { useState } from "react";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";
import { useTheme } from "~/contexts/ThemeContext";
import { useAuth } from "~/contexts/AuthContext";
import SessionWarningModal from "~/components/common/SessionWarningModal";
import SessionDebugInfo from "~/components/common/SessionDebugInfo";
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
  const [isNavigationCollapsed, setIsNavigationCollapsed] = useState(false);
  const { theme } = useTheme();
  const { showSessionWarning, dismissSessionWarning } = useAuth();

  return (
    <div className="min-h-screen bg-var-primary flex">
      {/* Navigation Area - 전체가 함께 토글됨 */}
      <div className={`fixed top-0 left-0 w-[280px] h-screen z-[1002] transition-transform duration-300 ease-in-out ${
        isNavigationCollapsed ? '-translate-x-full' : 'translate-x-0'
      }`}>
        {/* Top Navbar */}
        <TopNavbar 
          user={user}
          onLogout={onLogout}
        />
        
        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onToggleCollapse={() => setIsNavigationCollapsed(!isNavigationCollapsed)}
          isCollapsed={isNavigationCollapsed}
        />
      </div>

      {/* Menu Show Button (when collapsed) - 메뉴 숨김 버튼과 동일한 스타일과 위치 */}
      {isNavigationCollapsed && (
        <div className="fixed left-2.5 bottom-[80px] w-auto h-[50px] bg-transparent flex items-center justify-center z-[1001]">
          <button
            onClick={() => setIsNavigationCollapsed(false)}
            className="px-4 py-2 bg-gradient-to-br from-[#6B8E23] to-[#556B2F] border border-[#556B2F] rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 shadow-[0_2px_8px_rgba(107,142,35,0.2)] hover:bg-gradient-to-br hover:from-[#556B2F] hover:to-[#6B8E23] hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(107,142,35,0.3)]"
          >
            메뉴 보기
          </button>
        </div>
      )}

      {/* Main content area */}
      <div className={`flex-1 flex flex-col relative transition-all duration-300 ease-in-out ${
        isNavigationCollapsed ? 'ml-0' : 'ml-[280px]'
      }`}>
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
        <main className="flex-1 p-6 overflow-auto pt-10">
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

      {/* 세션 경고 모달 */}
      <SessionWarningModal 
        isOpen={showSessionWarning}
        onClose={dismissSessionWarning}
      />

      {/* 개발 모드에서만 표시되는 세션 디버그 정보 */}
      <SessionDebugInfo />
    </div>
  );
};

export default AppLayout;