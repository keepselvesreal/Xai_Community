/**
 * JWT 유틸리티 함수들
 * 토큰 검증, 디코딩, 만료 확인 등의 기능 제공
 */

export interface TokenInfo {
  isValid: boolean;
  isExpired: boolean;
  expiresAt: Date | null;
  userId: string | null;
  email: string | null;
  tokenType: string | null;
  issuedAt: Date | null;
}

/**
 * JWT 토큰 형식이 유효한지 확인
 */
export function validateJWTFormat(token: string | null | undefined): boolean {
  if (!token || typeof token !== 'string') {
    return false;
  }

  const parts = token.split('.');
  return parts.length === 3 && parts.every(part => part.length > 0);
}

/**
 * JWT 페이로드 디코딩
 */
export function decodeJWTPayload(token: string): any {
  if (!validateJWTFormat(token)) {
    throw new Error('Invalid JWT format');
  }

  try {
    const parts = token.split('.');
    const payload = parts[1];
    
    // Base64 디코딩을 위한 패딩 추가
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
    const decodedPayload = atob(paddedPayload);
    
    return JSON.parse(decodedPayload);
  } catch (error) {
    throw new Error('Failed to decode JWT payload');
  }
}

/**
 * 토큰이 만료되었는지 확인
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = decodeJWTPayload(token);
    
    if (!payload.exp) {
      return true; // 만료시간이 없으면 만료된 것으로 간주
    }

    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch (error) {
    return true; // 디코딩 실패 시 만료된 것으로 간주
  }
}

/**
 * 토큰에서 모든 정보를 추출
 */
export function extractTokenInfo(token: string): TokenInfo {
  try {
    if (!validateJWTFormat(token)) {
      return {
        isValid: false,
        isExpired: true,
        expiresAt: null,
        userId: null,
        email: null,
        tokenType: null,
        issuedAt: null,
      };
    }

    const payload = decodeJWTPayload(token);
    const expired = isTokenExpired(token);

    return {
      isValid: true,
      isExpired: expired,
      expiresAt: payload.exp ? new Date(payload.exp * 1000) : null,
      userId: payload.sub || null,
      email: payload.email || null,
      tokenType: payload.type || null,
      issuedAt: payload.iat ? new Date(payload.iat * 1000) : null,
    };
  } catch (error) {
    return {
      isValid: false,
      isExpired: true,
      expiresAt: null,
      userId: null,
      email: null,
      tokenType: null,
      issuedAt: null,
    };
  }
}