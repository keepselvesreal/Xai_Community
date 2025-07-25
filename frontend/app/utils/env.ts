/**
 * 환경변수 검증 및 관리 유틸리티
 * 
 * 작업 시간: 2025-07-25 16:30 (KST)
 * 작업 버전: v1.0.0
 * 
 * 주요 컴포넌트들:
 * - getRequiredEnv: 필수 환경변수 검증 및 오류 처리
 * - getNodeEnv: VITE_NODE_ENV 타입 안전성 검증
 * 
 * 함수 정보:
 * - getRequiredEnv (Line 25-32): 환경변수 존재 여부 검증, 누락 시 명확한 오류 메시지 제공
 * - getNodeEnv (Line 40-48): 환경값 타입 검증, development/production/staging 만 허용
 * 
 * 관련 파일:
 * - frontend/app/root.tsx: Sentry 환경 설정에서 사용
 * - frontend/app/entry.client.tsx: 클라이언트 환경 설정에서 사용
 * - frontend/app/components/monitoring/UnifiedMonitoringDashboard.tsx: 모니터링 환경 판단에서 사용
 */

/**
 * 필수 환경변수를 가져오고 검증합니다.
 * 환경변수가 설정되지 않은 경우 명확한 오류 메시지와 함께 예외를 발생시킵니다.
 * 
 * @param key - 확인할 환경변수 키 (예: 'VITE_NODE_ENV')
 * @returns 환경변수 값 (문자열)
 * @throws Error - 환경변수가 설정되지 않은 경우
 */
export function getRequiredEnv(key: string): string {
  const value = import.meta.env[key];
  if (!value) {
    throw new Error(
      `❌ 필수 환경변수 ${key}가 설정되지 않았습니다. Vercel 환경변수 또는 환경변수 파일에서 설정해주세요.`
    );
  }
  return value;
}

/**
 * VITE_NODE_ENV 환경변수를 타입 안전하게 가져옵니다.
 * 허용된 값(development, production, staging) 외의 값이 설정된 경우 예외를 발생시킵니다.
 * 
 * @returns 검증된 환경 값
 * @throws Error - 환경변수가 누락되거나 허용되지 않은 값인 경우
 */
export function getNodeEnv(): 'development' | 'production' | 'staging' {
  const env = getRequiredEnv('VITE_NODE_ENV');
  
  const allowedValues = ['development', 'production', 'staging'] as const;
  if (!allowedValues.includes(env as any)) {
    throw new Error(
      `❌ VITE_NODE_ENV는 'development', 'production', 'staging' 중 하나여야 합니다. 현재값: ${env}`
    );
  }
  
  return env as 'development' | 'production' | 'staging';
}

/**
 * 서버 사이드와 클라이언트 사이드 환경 설정값이 일치하는지 검증합니다.
 * 모든 환경(development, staging, production)에서 두 값이 일치해야 합니다.
 * 
 * @param serverEnv - 서버 사이드에서 전달받은 환경값
 * @param clientEnv - 클라이언트 사이드 환경값
 * @throws Error - 환경값이 일치하지 않는 경우
 */
export function validateEnvironmentMatch(
  serverEnv: string, 
  clientEnv: 'development' | 'production' | 'staging'
): void {
  if (serverEnv !== clientEnv) {
    const errorMessage = [
      '❌ 서버와 클라이언트 환경 설정값이 일치하지 않습니다!',
      '',
      `🔧 서버 환경:       ${serverEnv}`,
      `🌐 클라이언트 환경: ${clientEnv}`,
      '',
      '📋 해결 방법:',
      '1. VITE_NODE_ENV 환경변수가 양쪽에서 동일한지 확인',
      '2. 환경변수 파일 또는 배포 설정에서 값 확인',
      '',
      '💡 환경별 설정 예시:',
      '• 개발환경: VITE_NODE_ENV=development',
      '• 스테이징: VITE_NODE_ENV=staging', 
      '• 프로덕션: VITE_NODE_ENV=production'
    ].join('\n');
    
    console.error(errorMessage);
    throw new Error(errorMessage);
  }
}

/**
 * 환경 설정값이 올바른지 전체적으로 검증합니다.
 * 
 * @param serverEnv - 백엔드에서 전달받은 환경값
 * @returns 검증된 클라이언트 환경값
 */
export function validateAndGetEnvironment(serverEnv?: string): 'development' | 'production' | 'staging' {
  // 1. 클라이언트 환경변수 검증
  const clientEnv = getNodeEnv();
  
  // 2. 서버 환경변수 존재 확인
  if (!serverEnv) {
    throw new Error('❌ 서버에서 환경 정보를 받지 못했습니다. VITE_NODE_ENV 환경변수를 확인해주세요.');
  }
  
  // 3. 서버-클라이언트 환경값 일치 검증
  validateEnvironmentMatch(serverEnv, clientEnv);
  
  return clientEnv;
}