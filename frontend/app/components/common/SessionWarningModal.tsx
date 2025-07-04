import { useAuth } from "~/contexts/AuthContext";
import { SESSION_MESSAGES } from "~/lib/constants";

interface SessionWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SessionWarningModal({ isOpen, onClose }: SessionWarningModalProps) {
  const { extendSession, logout, getSessionInfo } = useAuth();

  if (!isOpen) return null;

  const sessionInfo = getSessionInfo();

  const handleExtendSession = () => {
    const success = extendSession();
    if (success) {
      onClose();
    } else {
      // 세션 연장 실패 시 로그아웃
      logout();
    }
  };

  const handleLogoutNow = () => {
    logout();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="text-center">
          {/* 아이콘 */}
          <div className="text-6xl mb-4">⏰</div>
          
          {/* 제목 */}
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {SESSION_MESSAGES.WARNING_TITLE}
          </h3>
          
          {/* 메시지 */}
          <p className="text-gray-600 mb-2 whitespace-pre-line">
            {SESSION_MESSAGES.WARNING_MESSAGE}
          </p>
          
          {/* 세션 정보 */}
          <div className="bg-gray-50 rounded-lg p-3 mb-6 text-sm">
            <div className="flex justify-between items-center mb-1">
              <span className="text-gray-600">남은 시간:</span>
              <span className="font-medium text-orange-600">
                {Math.floor(sessionInfo.timeRemaining * 60)}분
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">토큰 갱신:</span>
              <span className="font-medium text-blue-600">
                {sessionInfo.refreshCount}/{sessionInfo.maxRefreshCount}회
              </span>
            </div>
          </div>
          
          {/* 버튼들 */}
          <div className="flex gap-3">
            <button
              onClick={handleLogoutNow}
              className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              {SESSION_MESSAGES.LOGOUT_NOW}
            </button>
            <button
              onClick={handleExtendSession}
              className="flex-1 px-4 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              {SESSION_MESSAGES.EXTEND_SESSION}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}