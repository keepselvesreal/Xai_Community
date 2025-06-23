import { Link, useLocation } from "@remix-run/react";
import { cn } from "~/lib/utils";
import { NAV_ITEMS } from "~/lib/constants";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isAuthenticated?: boolean;
}

const Sidebar = ({ isOpen = true, onClose, isAuthenticated = false }: SidebarProps) => {
  const location = useLocation();

  const filteredNavItems = NAV_ITEMS.filter(item => {
    if (item.requiresAuth && !isAuthenticated) return false;
    if (item.requiresGuest && isAuthenticated) return false;
    return true;
  });

  // 섹션별로 그룹화
  const groupedItems = filteredNavItems.reduce((acc, item) => {
    if (!acc[item.section]) {
      acc[item.section] = [];
    }
    acc[item.section].push(item);
    return acc;
  }, {} as Record<string, typeof NAV_ITEMS>);

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
        className={cn(
          "fixed left-0 top-0 z-50 h-screen w-64 transform bg-white border-r border-gray-200 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🚀</span>
            <h1 className="text-lg font-semibold text-white">FastAPI UI</h1>
          </div>
          
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

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-8">
          {Object.entries(groupedItems).map(([section, items]) => (
            <div key={section}>
              <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {section}
              </h3>
              <div className="space-y-1">
                {items.map((item) => {
                  const isActive = location.pathname === item.path || 
                    (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
                  
                  return (
                    <Link
                      key={item.id}
                      to={item.path}
                      onClick={onClose}
                      className={cn(
                        "flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                        isActive
                          ? "bg-blue-50 text-blue-700 border-r-2 border-blue-600"
                          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                      )}
                    >
                      <span className="mr-3 text-lg">{item.icon}</span>
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            FastAPI UI Dashboard v1.0.0
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;