# 라우팅 패턴 가이드

## 개요

이 가이드는 일관된 라우팅 패턴을 유지하기 위한 규칙과 도구를 제공합니다.

## 라우팅 패턴

### 표준 패턴
모든 페이지는 다음 패턴을 따라야 합니다:

```
목록 페이지: /{pageName}.tsx → /{pageName}
상세 페이지: /{pageName}-post.$slug.tsx → /{pageName}-post/{slug}
```

### 예시
```
게시판:
- 목록: /board (board.tsx)
- 상세: /board-post/{slug} (board-post.$slug.tsx)

서비스:
- 목록: /services (services.tsx)
- 상세: /moving-services-post/{slug} (moving-services-post.$slug.tsx)

팁:
- 목록: /tips (tips.tsx)
- 상세: /tips-post/{slug} (tips-post.$slug.tsx)
```

## 새로운 페이지 타입 추가

### 1. 타입 정의 추가

`/app/types/routingTypes.ts`에서:

```typescript
// PageType에 새로운 타입 추가
export type PageType = 'board' | 'services' | 'tips' | 'notices' | 'events' | 'YOUR_NEW_PAGE';

// ROUTING_PATTERNS에 패턴 추가
export const ROUTING_PATTERNS: Record<PageType, RoutePattern> = {
  // ... 기존 패턴들
  YOUR_NEW_PAGE: {
    listRoute: '/your-new-page',
    detailRoute: '/your-new-page-post', 
    fileName: 'your-new-page-post.$slug.tsx'
  }
};

// 메타데이터 타입 매핑 추가
export const METADATA_TYPE_TO_PAGE_TYPE: Record<string, PageType> = {
  // ... 기존 매핑들
  'your-new-page': 'YOUR_NEW_PAGE'
};
```

### 2. 라우팅 파일 생성

#### 목록 페이지: `/app/routes/your-new-page.tsx`
```typescript
import { type MetaFunction } from "@remix-run/node";
import { ListPage } from "~/components/common/ListPage";
import { yourNewPageConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "새 페이지 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새 페이지" },
  ];
};

export default function YourNewPage() {
  const { user, logout } = useAuth();
  
  return (
    <ListPage
      config={yourNewPageConfig}
      user={user}
      onLogout={logout}
    />
  );
}
```

#### 상세 페이지: `/app/routes/your-new-page-post.$slug.tsx`
```typescript
import { useState, useEffect } from "react";
import { type MetaFunction } from "@remix-run/node";
import { useParams, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";

export const meta: MetaFunction = () => {
  return [
    { title: "새 페이지 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새 페이지 상세 정보" },
  ];
};

export default function YourNewPageDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  
  const [item, setItem] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);

  const loadItem = async () => {
    if (!slug) return;
    
    console.log('🔍 Loading item with slug:', slug);
    setIsLoading(true);
    
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        setItem(response.data);
      } else {
        setIsNotFound(true);
        showError('항목을 찾을 수 없습니다');
      }
    } catch (error) {
      console.error('🚨 Error loading item:', error);
      setIsNotFound(true);
      showError('항목을 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadItem();
  }, [slug]);

  // 로딩/에러/렌더링 로직...
  
  return (
    <AppLayout user={user} onLogout={logout}>
      {/* 상세 페이지 내용 */}
    </AppLayout>
  );
}
```

### 3. 페이지 설정 추가

`/app/config/pageConfigs.tsx`에 설정 추가:

```typescript
export const yourNewPageConfig: ListPageConfig<YourItemType> = {
  title: '새 페이지',
  writeButtonText: '✏️ 작성하기',
  writeButtonLink: '/your-new-page/write',
  searchPlaceholder: '검색...',
  
  apiEndpoint: '/api/posts',
  apiFilters: {
    service: 'residential_community',
    metadata_type: 'your-new-page',
    sortBy: 'created_at'
  },
  
  categories: [
    { value: 'all', label: '전체' },
    // 추가 카테고리...
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    // 추가 정렬 옵션...
  ],
  
  cardLayout: 'list', // 또는 'grid'
  
  renderCard: (item) => <YourCardRenderer item={item} />,
  filterFn: yourFilterFunction,
  sortFn: yourSortFunction
};
```

## 자동화 도구 사용

### 헬퍼 함수로 템플릿 생성

```typescript
import { generateNewPageTemplate, printRoutingGuide } from '~/utils/routingHelpers';

// 새 페이지 타입에 대한 템플릿 생성
const template = generateNewPageTemplate('events');

// 개발자 가이드 출력
printRoutingGuide('events');
```

### 타입 안전한 URL 생성

```typescript
import { TypeSafeUrlBuilder } from '~/utils/routingHelpers';

// 타입 안전한 URL 생성
const listUrl = TypeSafeUrlBuilder.listPage('board'); // '/board'
const detailUrl = TypeSafeUrlBuilder.detailPage('services', 'some-slug'); // '/moving-services-post/some-slug'
const writeUrl = TypeSafeUrlBuilder.writePage('tips'); // '/tips/write'
```

## 네비게이션 사용

### ListPage에서 자동 처리

`ListPage` 컴포넌트는 자동으로 타입 안전한 네비게이션을 처리합니다:

```typescript
// config.apiFilters.metadata_type을 기반으로 자동 라우팅
<ListPage
  config={yourConfig} // metadata_type: 'your-page-type'
  user={user}
  onLogout={logout}
/>
```

### 수동 네비게이션

```typescript
import { getNavigationUrl } from '~/types/routingTypes';

// 메타데이터 타입으로 URL 생성
const url = getNavigationUrl('board', 'some-slug'); // '/board-post/some-slug'
navigate(url);
```

## 검증 및 디버깅

### 패턴 검증

```typescript
import { validateRoutingPattern } from '~/types/routingTypes';

const isValid = validateRoutingPattern('events'); // boolean
```

### 개발자 도구

콘솔에서 라우팅 가이드 출력:

```typescript
import { printRoutingGuide } from '~/utils/routingHelpers';

printRoutingGuide('new-page-type');
```

## 체크리스트

새 페이지 타입 추가 시:

- [ ] `routingTypes.ts`에 PageType 추가
- [ ] `ROUTING_PATTERNS`에 패턴 추가  
- [ ] `METADATA_TYPE_TO_PAGE_TYPE`에 매핑 추가
- [ ] 목록 페이지 파일 생성 (`{pageName}.tsx`)
- [ ] 상세 페이지 파일 생성 (`{pageName}-post.$slug.tsx`)
- [ ] `pageConfigs.tsx`에 설정 추가
- [ ] 카드 렌더러 및 필터/정렬 함수 구현
- [ ] 테스트: 목록 → 상세 페이지 네비게이션 확인

## 마이그레이션

기존 페이지를 새 패턴으로 마이그레이션:

1. **라우팅 파일 이름 변경**
2. **네비게이션 URL 업데이트** 
3. **타입 정의 추가**
4. **기존 하드코딩된 URL을 헬퍼 함수로 대체**

이 가이드를 따르면 일관성 있고 확장 가능한 라우팅 시스템을 유지할 수 있습니다.