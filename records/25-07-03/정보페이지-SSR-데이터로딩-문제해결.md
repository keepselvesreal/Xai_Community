# 정보페이지 SSR 데이터로딩 문제 해결 과정

**작업 일시**: 2025-07-03  
**작업자**: Claude  
**문제 요약**: 정보 페이지에서 "정보를 불러오는 중입니다" 메시지가 지속적으로 표시되며 데이터가 로딩되지 않는 문제

## 수행한 주요 작업

### 1. 문제 현상 분석
- 전문가 꿀정보 페이지는 정상 동작하지만 정보 페이지만 데이터 로딩 실패
- 두 페이지 모두 동일한 API 구조를 사용하지만 결과가 다름
- SSR(Server-Side Rendering) 환경에서만 문제 발생

### 2. 코드 구조 비교 분석
- **전문가 꿀정보**: 클라이언트 사이드 렌더링만 사용 (정상 동작)
- **정보 페이지**: SSR + 클라이언트 사이드 하이브리드 구조 사용 (문제 발생)
- 동일한 `ListPage` 컴포넌트와 `useListData` 훅 사용

### 3. API 클라이언트 문제 해결
**문제**: SSR 환경에서 localStorage 접근 불가로 토큰 로딩 실패
**해결**: 
```typescript
// SSR 환경에서 토큰 갱신 실패 시에도 요청 계속 진행하도록 수정
if (typeof window === 'undefined') {
  console.log('ApiClient: SSR environment - proceeding without token');
} else {
  this.notifyTokenExpired();
}
```

### 4. API 필터링 설정 최적화
**문제**: 불필요한 `service` 필터로 인한 데이터 누락
**해결**: 모든 페이지 설정에서 `service: 'residential_community'` 필터 제거
```typescript
// Before
apiFilters: {
  service: 'residential_community',
  metadata_type: 'property_information'
}

// After  
apiFilters: {
  metadata_type: 'property_information'
}
```

## 발생한 문제와 해결 시도

### 문제 1: SSR 환경에서 localStorage 접근 불가
**증상**: `typeof window !== 'undefined'` 조건으로 인해 토큰 로드 실패
**시도**: 
1. ❌ Fallback 방식으로 클라이언트 사이드 렌더링 전환 
2. ✅ SSR 환경에서도 토큰 없이 공개 API 호출 허용

### 문제 2: API 필터링 설정 문제
**증상**: `service: 'residential_community'` 필터로 인한 빈 결과
**시도**:
1. ✅ 불필요한 service 필터 제거
2. ✅ metadata_type만으로 필터링하도록 변경

### 문제 3: MongoDB Aggregation ObjectId 변환 오류
**증상**: `admin_user_001` (14자리)를 ObjectId(24자리)로 변환 시 오류
```
Failed to parse objectId 'admin_user_001' in $convert with no onError value: 
Invalid string length for parsing to OID, expected 24 but found 14
```

**시도**:
1. ❌ 안전한 ObjectId 변환 로직 추가 (복잡한 조건문 사용)
2. ✅ 작성자 정보 조인 제거로 임시 해결

## 실용적 해결 방법 제시

### 1. 즉시 적용 가능한 해결책

#### A. ObjectId 변환 문제 완전 해결
```typescript
// 안전한 ObjectId 변환 함수 구현
function safeObjectIdConvert(id: string): any {
  if (typeof id === 'string' && id.length === 24 && /^[0-9a-fA-F]{24}$/.test(id)) {
    return { $toObjectId: id };
  }
  return id; // 문자열 그대로 사용
}
```

#### B. 작성자 정보 별도 조회 방식
```typescript
// 1단계: 게시글만 먼저 조회
const posts = await Post.find(query).limit(pageSize).skip(skip);

// 2단계: 작성자 ID 수집 후 별도 조회
const authorIds = [...new Set(posts.map(p => p.author_id))];
const authors = await User.find({ $or: [
  { _id: { $in: validObjectIds } },
  { _id: { $in: customIds } }
]});

// 3단계: 메모리에서 조인
const postsWithAuthors = posts.map(post => ({
  ...post,
  author: authors.find(a => a._id.toString() === post.author_id)
}));
```

### 2. 중장기 개선 방안

#### A. 일관된 ID 체계 구축
```typescript
// 사용자 생성 시 항상 MongoDB ObjectId 사용
const user = new User({
  _id: new ObjectId(), // 커스텀 ID 대신 ObjectId 사용
  user_handle: 'admin_user_001' // 별도 필드로 관리
});
```

#### B. 하이브리드 렌더링 전략 개선
```typescript
// SSR 실패 시 자동 CSR 전환
export const loader: LoaderFunction = async ({ request }) => {
  try {
    const data = await fetchSSRData();
    return json({ data, isSSR: true });
  } catch (error) {
    // SSR 실패 시 클라이언트에서 로딩하도록 설정
    return json({ data: null, isSSR: false, shouldLoadOnClient: true });
  }
};
```

#### C. 에러 처리 및 모니터링 강화
```typescript
// 구조화된 에러 로깅
class APIErrorLogger {
  static logSSRError(context: string, error: Error, metadata: any) {
    console.error(`[SSR-ERROR][${context}]`, {
      error: error.message,
      stack: error.stack,
      metadata,
      timestamp: new Date().toISOString()
    });
  }
}
```

### 3. 예방적 조치

#### A. 개발 환경 일관성 확보
- 로컬 개발 시에도 Atlas 사용하여 프로덕션 환경과 동일한 데이터 구조 유지
- Docker를 활용한 일관된 개발 환경 구축

#### B. 자동화된 테스트 구축
```typescript
// SSR 데이터 로딩 테스트
describe('SSR Data Loading', () => {
  test('should load info page data in SSR environment', async () => {
    // window 객체 없는 환경에서 테스트
    global.window = undefined;
    const result = await infoLoader({ request: mockRequest });
    expect(result.data).toBeDefined();
  });
});
```

#### C. 성능 모니터링 도구 도입
- SSR vs CSR 로딩 시간 비교 메트릭
- API 응답 시간 모니터링
- 에러율 추적 대시보드

## 결론

이번 문제는 **SSR 환경의 특수성**과 **MongoDB ObjectId 체계 불일치**가 복합적으로 작용한 사례였습니다. 

**핵심 교훈**:
1. SSR과 CSR 환경 차이를 고려한 설계 필요
2. 데이터베이스 ID 체계의 일관성 중요
3. 복잡한 Aggregation보다 단순한 쿼리가 안정적
4. 적절한 fallback 전략 수립 필요

**다음 단계**: ObjectId 변환 문제를 근본적으로 해결하고, 작성자 정보 조회 로직을 안전하게 복원하는 것이 필요합니다.