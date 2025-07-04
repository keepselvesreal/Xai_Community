import { useState } from "react";
import { useAuth } from "~/contexts/AuthContext";
import apiClient from "~/lib/api";

export default function SessionDebugInfo() {
  const [isOpen, setIsOpen] = useState(false);
  const { getSessionInfo, extendSession } = useAuth();

  if (process.env.NODE_ENV !== 'development') {
    return null; // 프로덕션에서는 숨김
  }

  const sessionInfo = getSessionInfo();

  const handleForceExpire = () => {
    // 강제로 세션 만료시키기 (테스트용)
    if (typeof window !== 'undefined') {
      // 8시간 전 시간으로 설정
      const pastTime = new Date(Date.now() - 8.5 * 60 * 60 * 1000).toISOString();
      localStorage.setItem('loginTime', pastTime);
      console.log('강제로 세션 만료 설정:', pastTime);
    }
  };

  const handleForceRefreshLimit = () => {
    // 강제로 갱신 제한 도달
    if (typeof window !== 'undefined') {
      localStorage.setItem('refreshCount', '16');
      console.log('강제로 갱신 제한 도달 설정');
    }
  };

  const handleClearSession = () => {
    // 세션 데이터 초기화
    if (typeof window !== 'undefined') {
      localStorage.removeItem('loginTime');
      localStorage.removeItem('refreshCount');
      console.log('세션 데이터 초기화');
    }
  };

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors shadow-lg"
      >
        Debug Session
      </button>

      {isOpen && (
        <div className="absolute bottom-12 left-0 bg-white border border-gray-300 rounded-lg p-4 shadow-xl w-80">
          <h3 className="font-bold text-gray-900 mb-3">세션 디버그 정보</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">로그인 시간:</span>
              <span className="font-mono text-xs">
                {sessionInfo.loginTime ? new Date(sessionInfo.loginTime).toLocaleString() : '없음'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">갱신 횟수:</span>
              <span className="font-medium">
                {sessionInfo.refreshCount}/{sessionInfo.maxRefreshCount}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">남은 시간:</span>
              <span className="font-medium text-orange-600">
                {sessionInfo.timeRemaining.toFixed(2)}시간
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">세션 만료:</span>
              <span className={`font-medium ${sessionInfo.isExpired ? 'text-red-600' : 'text-green-600'}`}>
                {sessionInfo.isExpired ? '만료됨' : '유효함'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">경고 표시:</span>
              <span className={`font-medium ${sessionInfo.showWarning ? 'text-orange-600' : 'text-gray-400'}`}>
                {sessionInfo.showWarning ? '표시됨' : '없음'}
              </span>
            </div>
          </div>

          <div className="border-t mt-3 pt-3 space-y-2">
            <button
              onClick={extendSession}
              className="w-full bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
            >
              세션 연장
            </button>
            
            <button
              onClick={handleForceExpire}
              className="w-full bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600"
            >
              강제 시간 만료
            </button>
            
            <button
              onClick={handleForceRefreshLimit}
              className="w-full bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600"
            >
              강제 갱신 제한
            </button>
            
            <button
              onClick={handleClearSession}
              className="w-full bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
            >
              세션 초기화
            </button>
          </div>
        </div>
      )}
    </div>
  );
}