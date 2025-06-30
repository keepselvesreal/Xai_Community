import { Link, useLocation } from "@remix-run/react";
import { useState } from "react";
import { useTheme } from "~/contexts/ThemeContext";

const navigationItems = [
  { 
    id: 'board', 
    name: '게시판', 
    path: '/board',
    icon: '📝',
    section: 'main'
  },
  { 
    id: 'info', 
    name: '정보', 
    path: '/info',
    icon: 'ℹ️',
    section: 'main'
  },
  { 
    id: 'services', 
    name: '입주 업체 서비스', 
    path: '/services',
    icon: '🏢',
    section: 'main'
  },
  { 
    id: 'tips', 
    name: '전문가 꿀정보', 
    path: '/tips',
    icon: '💡',
    section: 'main'
  },
  { 
    id: 'mypage', 
    name: '회원정보', 
    path: '/mypage',
    icon: '👤',
    section: 'main'
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isAuthenticated?: boolean;
  user?: any;
  onLogout?: () => void;
}

const Sidebar = ({ isOpen = true, onClose, isAuthenticated = false, user, onLogout }: SidebarProps) => {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { theme, toggleTheme } = useTheme();
  
  // 디버깅을 위한 로그
  console.log('Sidebar: isAuthenticated:', isAuthenticated);
  console.log('Sidebar: user:', user);

  const groupedItems = navigationItems.reduce((acc, item) => {
    if (!acc[item.section]) {
      acc[item.section] = [];
    }
    acc[item.section].push(item);
    return acc;
  }, {} as Record<string, typeof navigationItems>);

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const sectionNames = {
    main: '메인 메뉴'
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        className={`fixed left-0 top-0 z-50 h-screen transform bg-var-card border-r border-var-color transition-all duration-300 ease-in-out lg:static lg:translate-x-0 ${
          isCollapsed ? 'w-16' : 'w-64'
        } ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Header */}
        <div className="p-4 border-b border-var-color bg-gradient-to-r from-accent-primary to-accent-secondary">
          {/* Top row: Logo and Toggle */}
          <div className="flex items-center justify-between mb-3">
            {!isCollapsed && (
              <div className="flex items-center space-x-2">
                <span className="text-2xl">🏠</span>
                <h1 className="text-lg font-semibold text-white">XAI 커뮤니티</h1>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              {/* Toggle button */}
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="text-white hover:text-gray-200 transition-colors p-1 rounded"
              >
                {isCollapsed ? '👉' : '👈'}
              </button>
              
              {/* Mobile close button */}
              <button
                onClick={onClose}
                className="lg:hidden text-white hover:text-gray-200 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* User controls row */}
          {!isCollapsed && (
            <div className="space-y-2">
              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="w-full bg-black/20 hover:bg-black/30 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 text-white border border-white/20"
              >
                {theme === 'light' ? '🌙' : '☀️'} 
                {theme === 'light' ? ' 다크' : ' 라이트'}
              </button>
              
              {/* User authentication */}
              {user ? (
                <div className="space-y-2">
                  <div className="text-white text-sm px-3 py-1 font-medium">
                    {user.email}님
                  </div>
                  <button
                    onClick={onLogout}
                    className="w-full bg-black/20 hover:bg-black/30 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 text-white border border-white/20"
                  >
                    로그아웃
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <a
                    href="/auth/login"
                    className="flex-1 bg-black/20 hover:bg-black/30 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 text-white text-center border border-white/20"
                  >
                    로그인
                  </a>
                  <a
                    href="/auth/register"
                    className="flex-1 bg-black/20 hover:bg-black/30 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 text-white text-center border border-white/20"
                  >
                    회원가입
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-6 overflow-y-auto">
          {Object.entries(groupedItems).map(([section, items]) => (
            <div key={section}>
              {!isCollapsed && (
                <h3 className="px-3 text-xs font-semibold text-var-muted uppercase tracking-wider mb-3">
                  {sectionNames[section as keyof typeof sectionNames] || section}
                </h3>
              )}
              <div className="space-y-1">
                {items.map((item) => {
                  const active = isActive(item.path);
                  
                  return (
                    <Link
                      key={item.id}
                      to={item.path}
                      onClick={onClose}
                      className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                        active
                          ? 'bg-accent-primary text-white shadow-lg'
                          : 'text-var-secondary hover:bg-var-hover hover:text-var-primary'
                      }`}
                      title={isCollapsed ? item.name : undefined}
                    >
                      <span className="text-lg">{item.icon}</span>
                      {!isCollapsed && (
                        <>
                          <span className="ml-3">{item.name}</span>
                          {active && (
                            <div className="ml-auto w-2 h-2 bg-white rounded-full" />
                          )}
                        </>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-var-color">
          {!isCollapsed && (
            <div className="text-xs text-var-muted text-center">
              © 2024 XAI 아파트 커뮤니티
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;