import { useState } from "react";
import { cn } from "~/lib/utils";
import Button from "~/components/ui/Button";
import type { User } from "~/types";

interface HeaderProps {
  title: string;
  subtitle?: string;
  user?: User | null;
  onMenuClick?: () => void;
  onLogout?: () => void;
  className?: string;
}

const Header = ({ 
  title, 
  subtitle, 
  user, 
  onMenuClick, 
  onLogout,
  className 
}: HeaderProps) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className={cn("bg-white border-b border-gray-200 px-6 py-4", className)}>
      <div className="flex items-center justify-between">
        {/* Left side - Title and mobile menu */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Page title */}
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Right side - User info and actions */}
        <div className="flex items-center space-x-4">
          {user ? (
            <div className="relative">
              {/* User info */}
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
              >
                <span className="text-lg">👤</span>
                <span className="hidden sm:block text-sm font-medium">
                  {user.display_name || user.email}
                </span>
                <svg 
                  className={cn(
                    "h-4 w-4 transition-transform",
                    showUserMenu && "transform rotate-180"
                  )} 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* User dropdown menu */}
              {showUserMenu && (
                <>
                  {/* Backdrop */}
                  <div 
                    className="fixed inset-0 z-10"
                    onClick={() => setShowUserMenu(false)}
                  />
                  
                  {/* Menu */}
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <p className="text-sm font-medium text-gray-900">
                        {user.display_name || '사용자'}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                    
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        onLogout?.();
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      로그아웃
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                로그인
              </Button>
              <Button size="sm">
                회원가입
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;