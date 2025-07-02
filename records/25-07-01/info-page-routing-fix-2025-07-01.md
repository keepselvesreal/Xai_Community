# 정보 페이지 라우팅 문제 해결 기록

**날짜**: 2025년 7월 1일
**작성자**: Claude Code Assistant
**문제**: 정보 페이지에서 글을 클릭했을 때 상세 페이지가 나타나지 않는 문제

## 1. 문제 현상

- 정보 페이지 목록에서 글을 클릭할 때 "정보를 찾을 수 없습니다" 페이지가 표시됨
- URL 패턴이 다른 페이지와 다르게 구성됨
  - 기대값: `postid-slug` 형태
  - 실제값: `slug-postid` 형태 (예: `계약-유형별-분포-line-차트-9f2f4f17`)

## 2. 문제 원인 분석

### 2.1 라우팅 패턴 불일치
- 기존 페이지들의 라우팅 패턴:
  - 게시판: `board-post.$slug.tsx` → `/board-post/{slug}`
  - 서비스: `moving-services-post.$slug.tsx` → `/moving-services-post/{slug}`  
  - 팁: `expert-tips.$slug.tsx` → `/expert-tips/{slug}`
- 정보 페이지: `info.$slug.tsx` → `/info/{slug}` (일관성 없음)

### 2.2 라우팅 시스템 미등록
- `routingTypes.ts`에서 정보 페이지가 `PageType`에 포함되지 않음
- `METADATA_TYPE_TO_PAGE_TYPE` 매핑에서 `property_information` 타입이 누락됨

### 2.3 API 호출 방식 차이
- 게시판: `apiClient.getPost(slug)` → `/api/posts/{slug}` (개별 조회)
- 정보 페이지: 목록 API + slug 파라미터로 검색 (비효율적)

## 3. 해결 과정

### 3.1 라우팅 타입 시스템 업데이트

#### `routingTypes.ts` 수정
```typescript
// PageType에 info 추가
export type PageType = 'board' | 'services' | 'tips' | 'info' | 'notices' | 'events';

// 라우팅 패턴 추가
info: {
  listRoute: '/info',
  detailRoute: '/property-info',
  fileName: 'property-info.$slug.tsx'
},

// 메타데이터 타입 매핑 추가
export const METADATA_TYPE_TO_PAGE_TYPE: Record<string, PageType> = {
  'board': 'board',
  'moving services': 'services',
  'expert_tips': 'tips',
  'property_information': 'info',  // 추가
  'notices': 'notices',
  'events': 'events'
} as const;
```

### 3.2 라우트 파일 이름 변경
```bash
# 일관된 패턴을 위해 파일명 변경
mv info.$slug.tsx → property-info.$slug.tsx
```

### 3.3 API 호출 방식 통일
**기존 코드** (목록 API 사용):
```javascript
const response = await apiClient.request(`/api/posts`, {
  method: 'GET',
  params: {
    service: 'residential_community',
    metadata_type: 'property_information',
    slug: slug,
    page: 1,
    size: 1
  }
});
```

**수정된 코드** (개별 조회 API 사용):
```javascript
const response = await apiClient.getPost(slug);

if (response.success && response.data) {
  const post = response.data;
  
  // property_information 타입인지 확인
  if (post.metadata?.type !== 'property_information') {
    return json<LoaderData>({ 
      infoItem: null, 
      error: "정보를 찾을 수 없습니다." 
    }, { status: 404 });
  }
  
  const infoItem = convertPostToInfoItem(post);
  return json<LoaderData>({ infoItem });
}
```

### 3.4 컴포넌트 라우팅 처리 개선

#### InfoCardRenderer 수정
- 직접 라우팅 처리 제거
- ListPage의 통합 라우팅 시스템 사용

**기존**:
```javascript
onClick={(e) => {
  e.preventDefault();
  e.stopPropagation();
  navigate(`/property-info/${info.slug}`);
}}
```

**수정**:
```javascript
// InfoCardRenderer에서 직접 클릭 처리 제거
// ItemCard 컴포넌트가 ListPage의 handleItemClick을 통해 처리
```

## 4. 해결 결과

### 4.1 라우팅 플로우
1. 사용자가 정보 카드 클릭
2. `ItemCard` → `ListPage.handleItemClick` 호출
3. `getNavigationUrl('property_information', slug)` 실행
4. `METADATA_TYPE_TO_PAGE_TYPE['property_information']` → `'info'`
5. `RoutingPatternGenerator.generateDetailUrl('info', slug)`
6. 최종 URL: `/property-info/{slug}`

### 4.2 검증
- 백엔드 API 테스트: ✅ 성공
  ```bash
  curl "http://localhost:8000/api/posts/계약-유형별-분포-line-차트-9f2f4f17"
  # → 200 OK, 올바른 데이터 반환
  ```
- 프론트엔드 라우팅 테스트: ✅ 성공
  ```bash
  curl "http://localhost:5173/property-info/계약-유형별-분포-line-차트-9f2f4f17"
  # → 200 OK, 올바른 메타 태그 생성
  ```

## 5. 학습 포인트

### 5.1 일관성의 중요성
- 모든 페이지가 동일한 라우팅 패턴을 따라야 함
- 새로운 페이지 추가 시 기존 시스템에 맞춰 등록 필요

### 5.2 타입 안전성
- TypeScript 타입 시스템을 활용한 라우팅 안전성 확보
- 컴파일 타임에 오류 감지 가능

### 5.3 중앙화된 라우팅 관리
- `routingTypes.ts`를 통한 중앙화된 라우팅 패턴 관리
- `getNavigationUrl` 함수를 통한 일관된 URL 생성

## 6. 향후 개선 사항

1. **라우팅 자동 생성**: 새로운 페이지 타입 추가 시 자동으로 라우팅 패턴 생성
2. **타입 검증 강화**: 런타임에서도 라우팅 타입 검증
3. **테스트 자동화**: 모든 라우팅 패턴에 대한 자동화된 테스트

## 7. 관련 파일

### 수정된 파일들
- `/app/types/routingTypes.ts`
- `/app/routes/property-info.$slug.tsx` (이름 변경)
- `/app/config/pageConfigs.tsx`

### 테스트 확인 사항
- [x] 정보 목록 페이지에서 카드 클릭 시 상세 페이지 이동
- [x] URL 패턴 일관성 (`/property-info/{slug}`)
- [x] 백엔드 API 연동 정상 작동
- [x] 메타 태그 올바른 생성

---

**해결 완료**: 2025년 7월 1일 21:10 (KST)