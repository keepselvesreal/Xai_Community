import { type MetaFunction } from "@remix-run/node";
import { useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import Card from "~/components/ui/Card";
import Button from "~/components/ui/Button";
import InquiryManagement from "~/components/admin/InquiryManagement";
import ReportManagement from "~/components/admin/ReportManagement";
import SuggestionManagement from "~/components/admin/SuggestionManagement";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "대시보드 | FastAPI UI" },
    { name: "description", content: "FastAPI 개발 현황 및 API 테스트" },
  ];
};


export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // 섹션으로 스크롤하는 함수
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 관리자 도구 섹션 */}
      {(() => {
        console.log('🔍 대시보드 사용자 정보:', user);
        console.log('🔍 대시보드 is_admin 체크:', user?.is_admin);
        console.log('🔍 대시보드 user?.email:', user?.email);
        
        // 임시로 ktsfrank@naver.com 또는 is_admin 체크
        const isAdmin = user?.is_admin || user?.email === 'ktsfrank@naver.com' || user?.email === "admin@example.com" || user?.role === "admin";
        console.log('🔍 대시보드 최종 관리자 체크:', isAdmin);
        
        return isAdmin && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🔧 관리자 도구</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div 
                className="cursor-pointer transform hover:scale-105 transition-transform"
                onClick={() => navigate('/admin/monitoring')}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <Card.Content className="text-center py-4">
                    <div className="text-3xl mb-2">🖥️</div>
                    <div className="font-semibold text-gray-900">시스템 모니터링</div>
                    <div className="text-sm text-gray-500 mt-1">성능 및 에러 추적</div>
                  </Card.Content>
                </Card>
              </div>
              <div 
                className="cursor-pointer transform hover:scale-105 transition-transform"
                onClick={() => navigate('/analytics')}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <Card.Content className="text-center py-4">
                    <div className="text-3xl mb-2">📊</div>
                    <div className="font-semibold text-gray-900">사용자 분석</div>
                    <div className="text-sm text-gray-500 mt-1">커뮤니티 분석</div>
                  </Card.Content>
                </Card>
              </div>
              <div 
                className="cursor-pointer transform hover:scale-105 transition-transform"
                onClick={() => navigate('/admin/alerts')}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <Card.Content className="text-center py-4">
                    <div className="text-3xl mb-2">🚨</div>
                    <div className="font-semibold text-gray-900">알림 관리</div>
                    <div className="text-sm text-gray-500 mt-1">지능형 알림 시스템 설정</div>
                  </Card.Content>
                </Card>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 바로 가기 섹션 (관리자 전용) */}
      {(() => {
        const isAdmin = user?.is_admin || user?.email === 'ktsfrank@naver.com' || user?.email === "admin@example.com" || user?.role === "admin";
        return isAdmin && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🚀 바로 가기</h2>
            <div className="flex flex-wrap gap-4">
              <Button 
                variant="outline" 
                onClick={() => scrollToSection('inquiry-management')}
                className="flex items-center gap-2"
              >
                👑 등록 문의 관리
              </Button>
              <Button 
                variant="outline" 
                onClick={() => scrollToSection('report-management')}
                className="flex items-center gap-2"
              >
                🔴 신고 관리
              </Button>
              <Button 
                variant="outline" 
                onClick={() => scrollToSection('suggestion-management')}
                className="flex items-center gap-2"
              >
                💡 건의 관리
              </Button>
            </div>
          </div>
        );
      })()}

      {/* 등록 문의 관리 섹션 (관리자 전용) */}
      {(() => {
        const isAdmin = user?.is_admin || user?.email === 'ktsfrank@naver.com' || user?.email === "admin@example.com" || user?.role === "admin";
        return isAdmin && (
          <div id="inquiry-management" className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">👑 등록 문의 관리</h2>
            <InquiryManagement />
          </div>
        );
      })()}

      {/* 신고 관리 섹션 (관리자 전용) */}
      {(() => {
        const isAdmin = user?.is_admin || user?.email === 'ktsfrank@naver.com' || user?.email === "admin@example.com" || user?.role === "admin";
        return isAdmin && (
          <div id="report-management" className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🔴 신고 관리</h2>
            <ReportManagement />
          </div>
        );
      })()}

      {/* 건의 관리 섹션 (관리자 전용) */}
      {(() => {
        const isAdmin = user?.is_admin || user?.email === 'ktsfrank@naver.com' || user?.email === "admin@example.com" || user?.role === "admin";
        return isAdmin && (
          <div id="suggestion-management" className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">💡 건의 관리</h2>
            <SuggestionManagement />
          </div>
        );
      })()}


    </AppLayout>
  );
}