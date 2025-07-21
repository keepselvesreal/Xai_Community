/**
 * JWT 유틸리티 함수들
 */

export function validateJWTFormat(token: string): boolean {
  if (!token || typeof token !== 'string') {
    return false;
  }
  
  const parts = token.split('.');
  return parts.length === 3;
}

export function decodeJWTPayload(token: string): any {
  try {
    if (!validateJWTFormat(token)) {
      return null;
    }
    
    const payload = token.split('.')[1];
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch (error) {
    console.error('JWT 디코딩 실패:', error);
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  try {
    const payload = decodeJWTPayload(token);
    if (!payload || !payload.exp) {
      return true;
    }
    
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch (error) {
    console.error('JWT 만료 확인 실패:', error);
    return true;
  }
}

export function getTokenExpirationTime(token: string): Date | null {
  try {
    const payload = decodeJWTPayload(token);
    if (!payload || !payload.exp) {
      return null;
    }
    
    return new Date(payload.exp * 1000);
  } catch (error) {
    console.error('JWT 만료 시간 확인 실패:', error);
    return null;
  }
}

export function getUserFromToken(token: string): any {
  try {
    const payload = decodeJWTPayload(token);
    if (!payload) {
      return null;
    }
    
    return {
      id: payload.sub,
      email: payload.email,
      user_handle: payload.user_handle,
      display_name: payload.display_name,
      exp: payload.exp,
      iat: payload.iat
    };
  } catch (error) {
    console.error('JWT 사용자 정보 추출 실패:', error);
    return null;
  }
}