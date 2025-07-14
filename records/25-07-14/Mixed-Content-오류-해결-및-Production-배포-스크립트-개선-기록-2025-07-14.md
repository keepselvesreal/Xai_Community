# Mixed Content 오류 해결 및 Production 배포 스크립트 개선 기록

**날짜**: 2025년 7월 14일  
**담당자**: Claude & 태수  
**문제 유형**: 보안 정책 위반, API 통신 오류, 배포 환경 문제  

## 📋 목차
1. [문제 상황](#문제-상황)
2. [증상 분석](#증상-분석)
3. [원인 조사](#원인-조사)
4. [해결 과정](#해결-과정)
5. [최종 해결책](#최종-해결책)
6. [주니어 개발자를 위한 학습 포인트](#주니어-개발자를-위한-학습-포인트)
7. [예방 방법](#예방-방법)

---

## 🚨 문제 상황

### 발생한 문제들
1. **Mixed Content 오류**: Production 환경에서 HTTPS 페이지가 HTTP 리소스 요청
2. **API 통신 실패**: 프론트엔드에서 백엔드 API 호출 차단
3. **댓글 표시 안됨**: API 응답은 정상이지만 프론트엔드에서 댓글이 보이지 않음
4. **Production 배포 스크립트 안정성 부족**: Staging과 다른 수준의 에러 처리

### 환경 정보
- **프론트엔드**: Vercel (HTTPS) - `https://xai-community.vercel.app`
- **백엔드**: Google Cloud Run (HTTPS) - `https://xai-community-backend-798170408536.asia-northeast3.run.app`
- **브라우저**: Chrome (Mixed Content 정책 적용)

---

## 🔍 증상 분석

### 브라우저 콘솔 오류
```javascript
Mixed Content: The page at 'https://xai-community.vercel.app/dashboard' 
was loaded over HTTPS, but requested an insecure resource 
'http://xai-community-backend-798170408536.asia-northeast3.run.app/api/posts/?sort_by=created_at&page=1&size=6'. 
This request has been blocked; the content must be served over HTTPS.
```

### 환경변수 상태 (정상)
```javascript
🔍 API_BASE_URL 설정값: https://xai-community-backend-798170408536.asia-northeast3.run.app
🔍 VITE_API_URL 환경변수: https://xai-community-backend-798170408536.asia-northeast3.run.app
🔍 Environment Mode: production
```

### 핵심 모순
- ✅ 환경변수: HTTPS 설정 정상
- ✅ 코드: HTTPS URL 사용
- ❌ 실제 요청: HTTP로 변환되어 차단

---

## 🕵️ 원인 조사

### 1단계: 환경변수 확인
처음에는 Vercel 환경변수가 HTTP로 잘못 설정되었다고 의심했지만, 실제로는 HTTPS로 올바르게 설정되어 있었음.

### 2단계: 코드 변경사항 분석
Commit 300ebce와 현재 코드를 비교하여 API 관련 변경사항을 조사했지만, 직접적인 URL 변경은 없었음.

### 3단계: 실제 네트워크 요청 분석
```bash
curl -I "https://xai-community-backend-798170408536.asia-northeast3.run.app/api/posts?service_type=residential_community&sort_by=created_at&page=1&size=4"
```

**결과**: 백엔드에서 HTTP 307 리다이렉트 발생!
```
HTTP/2 307 
location: http://xai-community-backend-798170408536.asia-northeast3.run.app/api/posts/?service_type=residential_community&sort_by=created_at&page=1&size=4
```

### 🎯 진짜 원인 발견
**Trailing Slash 문제로 인한 HTTP 리다이렉트**

1. 프론트엔드: `/api/posts?...` (trailing slash 없음)
2. 백엔드: `/api/posts/?...` (trailing slash 필요)
3. 백엔드가 자동으로 307 리다이렉트 수행
4. 리다이렉트 URL이 HTTP로 생성됨 (Cloud Run 설정 이슈)
5. 브라우저가 Mixed Content 정책으로 차단

---

## 🔧 해결 과정

### 1단계: Production 배포 스크립트 개선
먼저 staging 스크립트의 개선사항을 production에 적용:

**개선사항:**
- 디버그 모드 추가 (`set -x`)
- 로컬 `.env.prod` 파일 지원
- 상세한 에러 처리 및 진단
- 빌드/배포 실패 시 종합적인 디버깅 정보

**변경 파일:** `scripts/deployment/backend/deploy-production.sh`

### 2단계: Mixed Content 오류 해결
Trailing slash 추가로 불필요한 리다이렉트 제거:

**변경 전:**
```javascript
const endpoint = `/api/posts${query ? `?${query}` : ''}`;
```

**변경 후:**
```javascript
const endpoint = `/api/posts/${query ? `?${query}` : ''}`;
```

**변경 파일:** `frontend/app/lib/api.ts`

---

## ✅ 최종 해결책

### 코드 수정
```javascript
// frontend/app/lib/api.ts
// Line 703
const endpoint = `/api/posts/${query ? `?${query}` : ''}`;
```

### 커밋 기록
```bash
commit 3df57b5
fix: API 엔드포인트에 trailing slash 추가 - Mixed Content 오류 해결
- /api/posts에 trailing slash 추가하여 HTTP 리다이렉트 방지
- 백엔드 307 리다이렉트로 인한 HTTPS→HTTP 변환 문제 해결
```

### 결과
- ✅ Mixed Content 오류 해결
- ✅ API 통신 정상화
- ✅ 댓글 표시 정상화
- ✅ Production 배포 스크립트 안정성 향상

---

## 🎓 주니어 개발자를 위한 학습 포인트

### 1. Mixed Content란?
**정의**: HTTPS 페이지에서 HTTP 리소스를 요청할 때 발생하는 보안 정책 위반

**브라우저 동작:**
- HTTPS 페이지의 보안을 보장하기 위해 HTTP 요청을 차단
- 사용자의 데이터 보안을 위한 필수 정책

### 2. HTTP 307 리다이렉트
**의미**: "Temporary Redirect" - 요청된 리소스가 일시적으로 다른 위치에 있음

**문제점:**
```
요청: https://api.example.com/posts
리다이렉트: http://api.example.com/posts/
결과: Mixed Content 오류
```

### 3. Trailing Slash의 중요성
**Trailing Slash가 있는 경우**: `/api/posts/`
**Trailing Slash가 없는 경우**: `/api/posts`

**차이점:**
- 일부 웹 서버는 이 둘을 다른 엔드포인트로 인식
- 자동 리다이렉트가 발생할 수 있음
- 리다이렉트 과정에서 프로토콜이 변경될 수 있음

### 4. 디버깅 접근법
1. **브라우저 개발자 도구 확인**
   - Console 탭에서 오류 메시지 확인
   - Network 탭에서 실제 요청 분석

2. **환경변수 검증**
   - 설정된 값과 실제 사용되는 값 비교
   - 빌드 시점과 런타임의 차이 확인

3. **cURL로 백엔드 직접 테스트**
   ```bash
   curl -I "https://your-api.com/endpoint"
   ```

4. **단계별 원인 제거**
   - 환경변수 → 코드 → 네트워크 → 서버 설정 순으로 확인

### 5. Cloud Run 특성
- 자동 HTTPS 지원
- Trailing slash 처리 방식이 특별함
- 리다이렉트 시 프로토콜 변경 가능성

---

## 🛡️ 예방 방법

### 1. API 엔드포인트 설계 원칙
```javascript
// 좋은 예시: 일관된 trailing slash 사용
const endpoints = {
  posts: '/api/posts/',
  comments: '/api/comments/',
  users: '/api/users/'
};

// 나쁜 예시: 혼재된 형태
const endpoints = {
  posts: '/api/posts',    // trailing slash 없음
  comments: '/api/comments/', // trailing slash 있음
  users: '/api/users'     // trailing slash 없음
};
```

### 2. 환경별 테스트 강화
```javascript
// 환경별 API URL 검증
const validateApiUrl = (url) => {
  if (!url.startsWith('https://')) {
    throw new Error('API URL must use HTTPS in production');
  }
  // trailing slash 일관성 체크
  // CORS 헤더 체크
  // 리다이렉트 체크
};
```

### 3. 배포 전 체크리스트
- [ ] Mixed Content 정책 준수
- [ ] HTTPS 통신 확인
- [ ] Trailing slash 일관성
- [ ] 환경변수 정확성
- [ ] 리다이렉트 체인 최소화

### 4. 모니터링 및 알림
```javascript
// API 요청 실패 시 상세 로깅
const apiErrorHandler = (error, url) => {
  console.error('API Error Details:', {
    url,
    error: error.message,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    protocol: window.location.protocol
  });
  
  // 운영팀에 알림 전송
  if (error.message.includes('Mixed Content')) {
    reportMixedContentError(url);
  }
};
```

### 5. 문서화
- API 엔드포인트 명세에 trailing slash 정책 명시
- 환경별 설정 가이드 작성
- 트러블슈팅 가이드 유지보수

---

## 📊 성과 및 교훈

### 해결된 문제들
1. ✅ Mixed Content 보안 오류 해결
2. ✅ API 통신 정상화
3. ✅ 사용자 경험 개선 (댓글 표시)
4. ✅ 배포 스크립트 안정성 향상

### 핵심 교훈
1. **작은 차이가 큰 문제를 만든다**: Trailing slash 하나의 차이
2. **브라우저 보안 정책의 중요성**: Mixed Content는 타협할 수 없는 보안 기준
3. **체계적인 디버깅의 힘**: 환경변수부터 네트워크까지 단계별 접근
4. **Cloud 서비스의 특성 이해**: Cloud Run의 리다이렉트 동작 패턴

### 앞으로의 개선 방향
1. **자동화된 API 검증**: CI/CD 파이프라인에 Mixed Content 체크 추가
2. **모니터링 강화**: Production 환경의 API 오류 실시간 감지
3. **문서화 개선**: API 설계 가이드라인 업데이트

---

**작성자**: Claude & 태수  
**검토일**: 2025년 7월 14일  
**상태**: 해결 완료 ✅

---

> 💡 **주니어 개발자 팁**: 웹 보안은 타협할 수 없는 영역입니다. Mixed Content 오류가 발생하면 무조건 HTTPS로 해결해야 합니다. 임시방편으로 HTTP를 허용하는 설정은 절대 프로덕션에 적용하지 마세요!