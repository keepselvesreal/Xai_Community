import { useTheme } from "~/contexts/ThemeContext";
import { useAuth } from "~/contexts/AuthContext";

interface TopNavbarProps {
  user?: any; // 하위 호환성을 위해 유지하지만 사용하지 않음
  onLogout?: () => void; // 하위 호환성을 위해 유지하지만 사용하지 않음
}

const TopNavbar = ({ user: propUser, onLogout: propOnLogout }: TopNavbarProps) => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isAuthenticated } = useAuth(); // AuthContext에서 직접 가져옴

  return (
    <nav className="fixed top-0 left-0 w-[280px] h-[120px] bg-gradient-to-br from-[#6B8E23] to-[#556B2F] flex flex-col justify-center items-center px-5 py-4 z-[1002] shadow-lg border-b border-white/10">
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
        {isAuthenticated && user ? (
          <>
            <a
              href="/mypage"
              className="text-white text-sm font-medium px-4 py-2.5 bg-white/10 rounded-lg border border-white/20 cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px text-center"
            >
              회원정보
            </a>
            <button
              onClick={() => {
                console.log('TopNavbar: Logout button clicked');
                logout(); // AuthContext의 logout 함수 직접 사용
              }}
              className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px"
            >
              로그아웃
            </button>
          </>
        ) : (
          <a
            href="/auth/login"
            className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-white/20 hover:-translate-y-px text-center"
          >
            로그인
          </a>
        )}
      </div>
    </nav>
  );
};

export default TopNavbar;