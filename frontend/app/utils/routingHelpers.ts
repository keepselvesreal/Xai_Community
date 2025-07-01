/**
 * 라우팅 헬퍼 유틸리티
 * 
 * 이 파일의 함수들을 사용하여 일관된 라우팅 패턴을 유지하세요.
 */

import { RoutingPatternGenerator, getNavigationUrl, type PageType } from '~/types/routingTypes';

/**
 * ListPageConfig에서 사용할 표준 네비게이션 핸들러
 */
export function createStandardNavigationHandler(
  navigate: (url: string) => void,
  metadataType: string
) {
  return (item: { slug?: string; id: string }) => {
    const slug = item.slug || item.id;
    const url = getNavigationUrl(metadataType, slug);
    
    console.log(`🚀 Navigating to: ${url}`);
    navigate(url);
  };
}

/**
 * 새로운 페이지 타입 추가 시 사용할 템플릿 생성기
 */
export function generateNewPageTemplate(pageName: string) {
  const pattern = RoutingPatternGenerator.generatePattern(pageName);
  
  return {
    // 1. 라우팅 파일 경로
    listPagePath: `/app/routes/${pageName}.tsx`,
    detailPagePath: `/app/routes/${pattern.fileName}`,
    
    // 2. 필요한 코드 스니펫
    listPageCode: `// ${pageName}.tsx
import { type MetaFunction } from "@remix-run/node";
import { ListPage } from "~/components/common/ListPage";
import { ${pageName}Config } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "${pageName} | XAI 아파트 커뮤니티" },
    { name: "description", content: "${pageName} 페이지" },
  ];
};

export default function ${pageName.charAt(0).toUpperCase() + pageName.slice(1)}() {
  const { user, logout } = useAuth();
  
  return (
    <ListPage
      config={${pageName}Config}
      user={user}
      onLogout={logout}
    />
  );
}`,

    detailPageCode: `// ${pattern.fileName}
import { useState, useEffect } from "react";
import { type MetaFunction } from "@remix-run/node";
import { useParams, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";

export const meta: MetaFunction = () => {
  return [
    { title: "${pageName} 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "${pageName} 상세 정보" },
  ];
};

export default function ${pageName.charAt(0).toUpperCase() + pageName.slice(1)}Detail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  
  const [item, setItem] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);

  const loadItem = async () => {
    if (!slug) return;
    
    console.log('🔍 Loading ${pageName} with slug:', slug);
    setIsLoading(true);
    
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        setItem(response.data);
      } else {
        setIsNotFound(true);
        showError('${pageName}을 찾을 수 없습니다');
      }
    } catch (error) {
      console.error('🚨 Error loading ${pageName}:', error);
      setIsNotFound(true);
      showError('${pageName}을 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadItem();
  }, [slug]);

  // 로딩/에러 상태 처리...
  // 실제 렌더링 로직...
  
  return (
    <AppLayout user={user} onLogout={logout}>
      {/* ${pageName} 상세 내용 */}
    </AppLayout>
  );
}`,

    // 3. pageConfigs.tsx에 추가할 설정
    configCode: `// pageConfigs.tsx에 추가
export const ${pageName}Config: ListPageConfig<YourItemType> = {
  title: '${pageName}',
  writeButtonText: '✏️ ${pageName} 작성',
  writeButtonLink: '/${pageName}/write',
  searchPlaceholder: '${pageName} 검색...',
  
  apiEndpoint: '/api/posts',
  apiFilters: {
    service: 'residential_community',
    metadata_type: '${pageName}',
    sortBy: 'created_at'
  },
  
  categories: [
    { value: 'all', label: '전체' },
    // 카테고리 추가...
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    // 정렬 옵션 추가...
  ],
  
  cardLayout: 'list', // 또는 'grid'
  
  renderCard: (item) => <YourCardRenderer item={item} />,
  filterFn: your${pageName}FilterFunction,
  sortFn: your${pageName}SortFunction
};`,

    // 4. 메타데이터 타입 매핑 추가 지시사항
    metadataMapping: `// routingTypes.ts의 METADATA_TYPE_TO_PAGE_TYPE에 추가:
'${pageName}': '${pageName}' as PageType`
  };
}

/**
 * ESLint 규칙 생성기 (선택사항)
 */
export function generateRoutingESLintRules() {
  return {
    // 라우팅 파일명 패턴 검증을 위한 ESLint 규칙
    rules: {
      'filename-pattern': [
        'error',
        {
          'routes/*.tsx': '^([a-z-]+)\\.tsx$|^([a-z-]+)-post\\.\\$slug\\.tsx$'
        }
      ]
    }
  };
}

/**
 * 개발자 가이드 출력
 */
export function printRoutingGuide(pageName: string) {
  const template = generateNewPageTemplate(pageName);
  
  console.log(`
🎯 새로운 페이지 타입 추가 가이드: ${pageName}

📁 1. 파일 생성:
   - ${template.listPagePath}
   - ${template.detailPagePath}

📝 2. routingTypes.ts 업데이트:
   - METADATA_TYPE_TO_PAGE_TYPE에 '${pageName}' 추가

⚙️ 3. pageConfigs.tsx에 설정 추가:
   - ${pageName}Config 생성

🧪 4. 테스트:
   - /${pageName} (목록)
   - /${pageName}-post/test-slug (상세)

✅ 패턴 준수 체크:
   - 목록: /${pageName}
   - 상세: /${pageName}-post/{slug}
   - 파일: ${template.detailPagePath}
  `);
}

/**
 * 타입 안전성을 위한 URL 빌더
 */
export class TypeSafeUrlBuilder {
  static listPage(pageType: PageType): string {
    return RoutingPatternGenerator.generateListUrl(pageType);
  }
  
  static detailPage(pageType: PageType, slug: string): string {
    return RoutingPatternGenerator.generateDetailUrl(pageType, slug);
  }
  
  static writePage(pageType: PageType): string {
    return `${RoutingPatternGenerator.generateListUrl(pageType)}/write`;
  }
}