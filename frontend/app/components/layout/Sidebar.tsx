import { Link, useLocation } from "@remix-run/react";
import { useState } from "react";
import { useTheme } from "~/contexts/ThemeContext";
import { Send } from "lucide-react";
import InquiryModal from "~/components/common/InquiryModal";
import { useInquiry } from "~/hooks/useInquiry";
import { InquiryType } from "~/types/inquiry";
import Modal from "~/components/ui/Modal";
import Button from "~/components/ui/Button";
import type { User } from "~/types";

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
  user?: User | null;
  onLogout?: () => void;
}

const Sidebar = ({ isOpen = true, onClose, onToggleCollapse, isCollapsed = false, user, onLogout }: SidebarProps) => {
  const location = useLocation();
  const [openModal, setOpenModal] = useState<InquiryType | null>(null);
  const [showInquiryOptions, setShowInquiryOptions] = useState(false);
  const { submitInquiry, getInquiryConfig, isLoading } = useInquiry();
  const { theme, toggleTheme } = useTheme();

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

  // 모달 핸들러 함수들
  const handleSuggestionsClick = () => {
    setOpenModal('suggestions');
  };

  const handleInquiryClick = () => {
    setShowInquiryOptions(true);
  };

  const handleInquiryOptionClick = (type: 'moving-services-register-inquiry' | 'expert-tips-register-inquiry') => {
    setShowInquiryOptions(false);
    setOpenModal(type);
  };

  const handleCloseModal = () => {
    setOpenModal(null);
    setShowInquiryOptions(false);
  };

  const handleSubmit = async (data: any) => {
    try {
      await submitInquiry(data);
      alert('문의가 성공적으로 제출되었습니다!');
    } catch (error) {
      alert('문의 제출 중 오류가 발생했습니다.');
    }
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
        className="fixed left-0 top-0 z-50 h-screen w-[240px] bg-white border-r border-[#e5e5e7] shadow-[2px_0_8px_rgba(0,0,0,0.1)] flex flex-col"
      >
        {/* Top Header - 통합된 상단 영역 */}
        <div className="w-full h-[120px] bg-gradient-to-br from-[#6B8E23] to-[#556B2F] flex flex-col justify-center items-center px-5 py-4 border-b border-white/10">
          {/* Row 1: Brand and Dark Mode Toggle */}
          <div className="flex items-center justify-between w-full mb-4">
            <div className="flex items-center">
              <div className="text-[28px] font-bold text-white tracking-wide drop-shadow-sm">
                Xai
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className="px-2 py-1.5 bg-white/10 border border-white/20 rounded-md text-white text-sm cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
          </div>

          {/* Row 2: User Controls */}
          <div className="flex items-center justify-center w-full gap-3 mb-3">
            {user && onLogout ? (
              <>
                <a
                  href="/mypage"
                  className="text-white text-sm font-medium px-4 py-2.5 bg-white/10 rounded-lg border border-white/20 cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px text-center"
                >
                  회원정보
                </a>
                <button
                  onClick={() => {
                    console.log('Sidebar: Logout button clicked');
                    if (onLogout) {
                      onLogout();
                    }
                  }}
                  className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <a
                  href="/auth/register"
                  className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px text-center"
                >
                  회원가입
                </a>
                <a
                  href="/auth/login"
                  className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px text-center"
                >
                  로그인
                </a>
              </>
            )}
          </div>
        </div>

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
                  className={`flex items-center justify-center px-5 py-[18px] m-0 text-[#595959] no-underline rounded-xl text-base font-semibold transition-all duration-200 relative text-center border-b border-black/10 min-h-[52px] ${
                    active
                      ? 'bg-gradient-to-br from-[#6B8E23] to-[#556B2F] text-white'
                      : 'hover:bg-[#F0F8E8] hover:text-[#6B8E23]'
                  }`}
                  title={item.name}
                >
                  <span>{item.name}</span>
                  {active && (
                    <div className="mr-auto w-2 h-2 bg-white rounded-full absolute left-5" />
                  )}
                </Link>
              );
            })}

            {/* 건의/문의 섹션 */}
            <div className="mt-3 mx-2 p-3 bg-gradient-to-br from-[#6B8E23] to-[rgba(107,142,35,0.9)] rounded-2xl relative">
              {/* 종이비행기 아이콘 */}
              <div className="absolute top-2 left-1/2 transform -translate-x-1/2">
                <Send className="w-5 h-5 text-white" />
              </div>
              
              {/* 버튼 컨테이너 */}
              <div className="flex gap-3 mt-6">
                <button 
                  onClick={handleSuggestionsClick}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-white/20 border border-white/30 rounded-[10px] transition-all duration-150 cursor-pointer backdrop-blur-[10px] text-white text-[13px] font-semibold hover:bg-white/30 hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:border-white/40"
                >
                  건의하기
                </button>
                <button 
                  onClick={handleInquiryClick}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-white/20 border border-white/30 rounded-[10px] transition-all duration-150 cursor-pointer backdrop-blur-[10px] text-white text-[13px] font-semibold hover:bg-white/30 hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:border-white/40"
                >
                  문의하기
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* Menu Toggle Area - 전체 화면 기준 우측 중앙에 대칭적으로 배치 */}
        <button
          onClick={onToggleCollapse}
          className="fixed right-0 top-1/2 transform -translate-y-1/2 z-[1002] bg-gradient-to-bl from-[#ff4757] to-[#ff3742] hover:from-[#ff3742] hover:to-[#ff2f3a] border-none rounded-l-lg py-6 px-1.5 text-white font-bold cursor-pointer transition-all duration-300 shadow-[-2px_0_12px_rgba(255,71,87,0.3)] hover:shadow-[-4px_0_16px_rgba(255,71,87,0.4)] hover:scale-110"
        >
          <div className="flex items-center gap-1">
            <div className="w-0 h-0 border-r-[12px] border-r-white border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent opacity-80"></div>
            <div className="w-1 h-10 bg-white rounded-sm opacity-80"></div>
          </div>
        </button>

        {/* Footer - 맨 하단에 위치, 높이 줄임 */}
        <div className="absolute bottom-0 left-0 w-full p-3 border-t border-[#e5e5e7] text-center bg-white">
          <div className="text-[11px] text-[#86868b]">
            © 2024 XAI 아파트 커뮤니티
          </div>
        </div>
      </aside>

      {/* 문의하기 선택 모달 */}
      {showInquiryOptions && (
        <Modal 
          isOpen={showInquiryOptions} 
          onClose={handleCloseModal} 
          title="문의 종류 선택"
          size="md"
          overlayClassName="z-[9999]"
        >
          <div className="space-y-4">
            <p className="text-gray-600 text-center mb-6">
              원하시는 문의 종류를 선택해 주세요.
            </p>
            
            <div className="space-y-3">
              <Button
                onClick={() => handleInquiryOptionClick('moving-services-register-inquiry')}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white py-4 text-base font-medium"
              >
                입주 서비스 업체 등록 문의
              </Button>
              
              <Button
                onClick={() => handleInquiryOptionClick('expert-tips-register-inquiry')}
                className="w-full bg-green-500 hover:bg-green-600 text-white py-4 text-base font-medium"
              >
                전문가의 꿀정보 등록 문의
              </Button>
            </div>
            
            <div className="flex justify-center mt-6">
              <Button
                onClick={handleCloseModal}
                variant="outline"
                className="px-8"
              >
                취소
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* InquiryModal 컴포넌트들 */}
      {openModal && (
        <div className="relative z-[9999]">
          <InquiryModal
            isOpen={true}
            onClose={handleCloseModal}
            config={getInquiryConfig(openModal)}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      )}
    </>
  );
};

export default Sidebar;