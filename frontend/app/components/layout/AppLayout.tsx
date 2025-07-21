import { useState } from "react";
import Sidebar from "./Sidebar";
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
      <div className={`fixed top-0 left-0 w-[240px] h-screen z-[1002] transition-transform duration-300 ease-in-out ${
        isNavigationCollapsed ? '-translate-x-full' : 'translate-x-0'
      }`}>
        {/* Sidebar - 통합된 사이드바 */}
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onToggleCollapse={() => setIsNavigationCollapsed(!isNavigationCollapsed)}
          isCollapsed={isNavigationCollapsed}
          user={user}
          onLogout={onLogout}
        />
      </div>

      {/* 사이드바 숨김 시 나타나는 토글 버튼 - 기존 메뉴 표시 버튼과 동일한 중앙 위치 */}
      {isNavigationCollapsed && (
        <button
          onClick={() => setIsNavigationCollapsed(false)}
          className="fixed left-0 top-1/2 transform -translate-y-1/2 z-[1002] bg-gradient-to-br from-[#ff4757] to-[#ff3742] hover:from-[#ff3742] hover:to-[#ff2f3a] border-none rounded-r-lg py-6 px-1.5 text-white font-bold cursor-pointer transition-all duration-300 shadow-[2px_0_12px_rgba(255,71,87,0.3)] hover:shadow-[4px_0_16px_rgba(255,71,87,0.4)] hover:scale-110"
        >
          <div className="flex items-center gap-1">
            <div className="w-1 h-10 bg-white rounded-sm opacity-80"></div>
            <div className="w-0 h-0 border-l-[12px] border-l-white border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent opacity-80"></div>
          </div>
        </button>
      )}

      {/* Main content area */}
      <div className={`flex-1 flex flex-col relative transition-all duration-300 ease-in-out ${
        isNavigationCollapsed ? 'ml-0' : 'ml-[240px]'
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