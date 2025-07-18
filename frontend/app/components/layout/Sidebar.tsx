import { Link, useLocation } from "@remix-run/react";
import { useState } from "react";
import { useTheme } from "~/contexts/ThemeContext";

const navigationItems = [
  { 
    id: 'board', 
    name: '게시판', 
    path: '/board',
    section: 'main'
  },
  { 
    id: 'info', 
    name: '정보', 
    path: '/info',
    section: 'main'
  },
  { 
    id: 'services', 
    name: '입주 업체 서비스', 
    path: '/services',
    section: 'main'
  },
  { 
    id: 'tips', 
    name: '전문가 꿀정보', 
    path: '/tips',
    section: 'main'
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  onToggleCollapse?: () => void;
  isCollapsed?: boolean;
}

const Sidebar = ({ isOpen = true, onClose, onToggleCollapse, isCollapsed = false }: SidebarProps) => {
  const location = useLocation();

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
        className="fixed left-0 top-[120px] z-50 h-[calc(100vh-120px)] w-[280px] bg-white border-r border-[#e5e5e7] shadow-[2px_0_8px_rgba(0,0,0,0.1)] flex flex-col lg:block"
      >

        {/* Navigation */}
        <nav className="flex-1 pt-10 pb-0 px-0 overflow-y-auto flex flex-col justify-start bg-gradient-to-b from-[rgba(107,142,35,0.02)] to-transparent">
          <div className="px-4 flex flex-col justify-start gap-4">
            {navigationItems.map((item) => {
              const active = isActive(item.path);
              
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  onClick={() => {
                    console.log(`🔗 Sidebar: ${item.name}(${item.path}) 클릭됨`);
                    // 모바일에서만 사이드바 닫기
                    if (window.innerWidth < 1024 && onClose) {
                      onClose();
                    }
                  }}
                  className={`flex items-center justify-center px-5 py-[18px] m-0 text-[#595959] no-underline rounded-xl text-lg font-semibold transition-all duration-200 relative text-center border-b border-black/10 min-h-[52px] ${
                    active
                      ? 'bg-gradient-to-br from-[#6B8E23] to-[#556B2F] text-white'
                      : 'hover:bg-[#F0F8E8] hover:text-[#6B8E23]'
                  }`}
                  title={item.name}
                >
                  <span>{item.name}</span>
                  {active && (
                    <div className="ml-auto w-2 h-2 bg-white rounded-full absolute right-5" />
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Menu Toggle Area - bottom: 80px로 푸터와 간격 늘림 */}
        <div className="absolute bottom-[80px] left-0 w-full h-[50px] bg-transparent flex items-center justify-center z-[1001]">
          <button
            onClick={onToggleCollapse}
            className="px-4 py-2 bg-gradient-to-br from-[#6B8E23] to-[#556B2F] border border-[#556B2F] rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 shadow-[0_2px_8px_rgba(107,142,35,0.2)] hover:bg-gradient-to-br hover:from-[#556B2F] hover:to-[#6B8E23] hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(107,142,35,0.3)]"
          >
            메뉴 숨김
          </button>
        </div>

        {/* Footer - 맨 하단에 위치 */}
        <div className="absolute bottom-0 left-0 w-full p-6 border-t border-[#e5e5e7] text-center bg-white">
          <div className="text-[11px] text-[#86868b]">
            © 2024 XAI 아파트 커뮤니티
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;