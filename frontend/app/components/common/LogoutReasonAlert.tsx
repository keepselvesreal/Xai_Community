import { useEffect } from "react";
import { 
  SESSION_EXPIRY_REASONS, 
  SESSION_MESSAGES 
} from "~/lib/constants";

interface LogoutReasonAlertProps {
  onReasonFound?: (reason: string, message: string) => void;
}

export default function LogoutReasonAlert({ onReasonFound }: LogoutReasonAlertProps) {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const logoutReason = localStorage.getItem('logoutReason');
      
      if (logoutReason && logoutReason !== SESSION_EXPIRY_REASONS.MANUAL_LOGOUT) {
        console.log('LogoutReasonAlert: Found logout reason:', logoutReason);
        
        let message = '';
        switch (logoutReason) {
          case SESSION_EXPIRY_REASONS.TIME_LIMIT:
            message = SESSION_MESSAGES.EXPIRED_TIME_LIMIT;
            break;
          case SESSION_EXPIRY_REASONS.REFRESH_LIMIT:
            message = SESSION_MESSAGES.EXPIRED_REFRESH_LIMIT;
            break;
          case SESSION_EXPIRY_REASONS.TOKEN_INVALID:
            message = SESSION_MESSAGES.EXPIRED_TOKEN_INVALID;
            break;
          default:
            message = SESSION_MESSAGES.EXPIRED_TOKEN_INVALID;
        }
        
        // 알림 표시
        if (onReasonFound) {
          onReasonFound(logoutReason, message);
        }
        
        // 로그아웃 사유 제거 (한 번만 표시)
        localStorage.removeItem('logoutReason');
      }
    }
  }, [onReasonFound]);

  return null; // UI 렌더링 없음
}