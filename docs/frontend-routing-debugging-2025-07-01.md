# 프론트엔드 라우팅 디버깅 및 해결 과정 (2025-07-01)

## 문제 개요

서비스 페이지에서 서비스 카드 클릭 시 상세 페이지로 이동하지 않는 문제가 발생했습니다. 게시판 페이지는 정상 작동하지만 서비스 페이지에서만 네비게이션이 작동하지 않았습니다.

## 초기 상황

- **게시판**: 카드 클릭 → 상세 페이지 이동 ✅
- **서비스**: 카드 클릭 → 페이지 이동 안됨 ❌
- 두 페이지 모두 동일한 API 사용 (`metadata.type`만 다름)
- 동일한 `ListPage` 컴포넌트 사용

## 문제 해결 과정

### 1단계: 사용자 클릭 이벤트 분석

**문제**: 서비스 카드 클릭 시 이벤트가 전혀 감지되지 않음
**원인**: 게시판과 서비스의 카드 렌더러 구조 차이

```typescript
// 게시판 (PostCardRenderer) - 자체 클릭 핸들러 보유
<div onClick={(e) => navigate(`/posts/${post.slug}`)}>

// 서비스 (ServiceCardRenderer) - 클릭 핸들러 없음
<div className="..."> // onClick 없음
```

**해결**: 서비스 카드에 클릭 핸들러 추가

### 2단계: navigate 함수 작동 확인

**문제**: 클릭 이벤트는 감지되지만 `navigate` 함수가 작동하지 않음
**확인한 내용**:
- `useNavigate()` 올바르게 임포트됨 ✅
- 클릭 로그 출력됨 ✅
- URL 변경되지 않음 ❌

**디버깅**: 강제 페이지 이동으로 라우팅 파일 존재 여부 확인

### 3단계: 라우팅 파일 구조 분석

**핵심 발견**: 게시판과 서비스의 라우팅 구조 차이

#### 게시판 구조
```
/app/routes/
├── board.tsx                  // 목록 페이지 (/board)
└── posts.$slug.tsx           // 상세 페이지 (/posts/{slug})
```

#### 서비스 구조 (문제 발생)
```
/app/routes/
├── services.tsx              // 목록 페이지 (/services)
└── services.$id.tsx          // 상세 페이지 (/services/{id})
```

**문제점**:
1. **파라미터 불일치**: 파일명은 `$id`인데 코드에서 `slug` 사용
2. **Nested Routing 충돌**: `/services/{id}`가 `/services` 하위로 인식되어 라우팅 충돌

### 4단계: 파라미터 통일 시도

**시도 1**: `services.$id.tsx` → `services.$slug.tsx`로 변경
**결과**: 여전히 페이지 이동 안됨

**시도 2**: 코드에서 `id` 파라미터 사용으로 통일
**결과**: 여전히 페이지 이동 안됨

### 5단계: 최종 해결책 - 완전 분리된 라우팅

**해결책**: 게시판과 동일하게 **완전히 다른 경로** 사용

#### 최종 구조
```
/app/routes/
├── services.tsx                    // 목록 페이지 (/services)
└── service-detail.$slug.tsx        // 상세 페이지 (/service-detail/{slug})
```

**변경 사항**:
1. **라우팅 파일**: `services.$id.tsx` → `service-detail.$slug.tsx`
2. **URL 경로**: `/services/{id}` → `/service-detail/{slug}`
3. **파라미터**: `id` → `slug` 통일

## 핵심 학습 내용

### API vs 프론트엔드 라우팅의 독립성

**중요한 깨달음**: API 엔드포인트와 프론트엔드 라우팅은 완전히 독립적입니다.

#### API 레벨 (백엔드)
```typescript
// 두 페이지 모두 동일한 API 사용
apiClient.getPost(slug) // → GET /api/posts/{slug}
```

#### 프론트엔드 라우팅 (프론트엔드)
```typescript
// 게시판
/posts/{slug} → posts.$slug.tsx

// 서비스  
/service-detail/{slug} → service-detail.$slug.tsx
```

**핵심**: 서로 다른 프론트엔드 URL이 동일한 백엔드 API를 호출할 수 있습니다.

### Remix 라우팅 원리

1. **파일 기반 라우팅**: 파일명이 URL 경로를 결정
2. **Nested Routing**: 동일한 prefix를 가진 경로는 상하위 관계로 인식
3. **파라미터 매칭**: `$` prefix로 동적 파라미터 정의

## 권장 라우팅 구조 개선안

현재 구조의 일관성을 위해 다음과 같이 통일하는 것을 권장합니다:

### 제안된 구조
```
/app/routes/
├── board.tsx                      // 목록: /board
├── board-post.$slug.tsx           // 상세: /board-post/{slug}
├── services.tsx                   // 목록: /services  
└── moving-services-post.$slug.tsx // 상세: /moving-services-post/{slug}
```

### 장점
1. **명확한 구분**: 각 도메인의 상세 페이지가 명확히 구분됨
2. **확장성**: 추가 기능별 라우팅 쉽게 확장 가능
3. **일관성**: 모든 상세 페이지가 동일한 패턴 (`{domain}-post.$slug.tsx`)

## 구현 코드 변경사항

### 1. 라우팅 파일 변경
```bash
# 현재
/routes/posts.$slug.tsx
/routes/service-detail.$slug.tsx

# 권장
/routes/board-post.$slug.tsx  
/routes/moving-services-post.$slug.tsx
```

### 2. 네비게이션 로직 업데이트
```typescript
// ListPage.tsx의 handleItemClick
if (config.apiFilters?.metadata_type === 'moving services') {
  navigate(`/moving-services-post/${targetSlug}`);
} else if (config.apiFilters?.metadata_type === 'board') {
  navigate(`/board-post/${targetSlug}`);
}
```

### 3. 카드 렌더러 업데이트
```typescript
// PostCardRenderer
onClick={() => navigate(`/board-post/${post.slug}`)}

// ServiceCardRenderer  
onClick={() => navigate(`/moving-services-post/${service.slug}`)}
```

## 디버깅 체크리스트

향후 유사한 문제 발생 시 확인할 사항:

1. **클릭 이벤트 감지**
   - [ ] 콘솔에 클릭 로그 출력되는가?
   - [ ] 이벤트 핸들러가 올바르게 연결되었는가?

2. **navigate 함수 작동**
   - [ ] `navigate()` 함수가 호출되는가?
   - [ ] URL이 실제로 변경되는가?

3. **라우팅 파일 존재**
   - [ ] 대상 라우팅 파일이 존재하는가?
   - [ ] 파일명과 URL 패턴이 일치하는가?

4. **파라미터 일치**
   - [ ] 라우팅 파일의 파라미터명과 코드가 일치하는가?
   - [ ] `useParams()`에서 올바른 키를 사용하는가?

5. **Nested Routing 충돌**
   - [ ] 상위/하위 라우팅 충돌이 없는가?
   - [ ] 독립적인 경로 구조를 사용하는가?

## 결론

이번 문제를 통해 **프론트엔드 라우팅의 독립성**과 **Remix의 파일 기반 라우팅 시스템**에 대해 깊이 이해할 수 있었습니다. 

핵심은 **백엔드 API와 프론트엔드 라우팅이 완전히 독립적**이라는 점이며, 사용자 경험과 코드 구조를 고려해 적절한 URL 구조를 설계하는 것이 중요합니다.

## 관련 파일

- `/app/routes/service-detail.$slug.tsx` - 서비스 상세 페이지
- `/app/routes/posts.$slug.tsx` - 게시판 상세 페이지  
- `/app/components/common/ListPage.tsx` - 공통 목록 페이지 컴포넌트
- `/app/config/pageConfigs.tsx` - 페이지별 설정 및 카드 렌더러