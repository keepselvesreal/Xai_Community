# 정보 페이지 콘텐츠 생성 시스템 문서

**날짜**: 2025년 7월 1일  
**작성자**: Claude Code Assistant  
**목적**: 정보 페이지 콘텐츠 자동 생성 시스템의 구현 및 처리 과정 문서화

## 1. 시스템 개요

### 1.1 목적
관리자가 부동산 정보 페이지의 콘텐츠를 체계적으로 생성할 수 있도록 하는 스크립트 기반 시스템입니다.

### 1.2 특징
- **TDD 기반 개발**: 테스트 우선 개발 방법론 적용
- **4가지 콘텐츠 타입 지원**: 인터렉티브 차트, AI 글, 데이터 시각화, 혼합 콘텐츠
- **HTML 안전 렌더링**: XSS 공격 방지 및 스크립트 실행 지원
- **자동 메타데이터 생성**: SEO 및 분류를 위한 메타데이터 자동 생성

## 2. 아키텍처

### 2.1 전체 구조
```
backend/
├── scripts/info_content/           # 콘텐츠 생성 스크립트
│   ├── base_creator.py            # 기본 생성기 클래스
│   ├── content_types.py           # 데이터 타입 정의
│   └── creators/                  # 콘텐츠 타입별 생성기
│       ├── interactive_creator.py # 인터렉티브 차트
│       ├── ai_article_creator.py  # AI 글 생성기
│       ├── data_viz_creator.py    # 데이터 시각화
│       └── mixed_creator.py       # 혼합 콘텐츠
├── models/
│   └── post.py                    # Post 모델 (정보 저장)
└── services/
    └── post_services.py           # Post 서비스 로직

frontend/
├── app/components/common/
│   └── SafeHTMLRenderer.tsx       # HTML 안전 렌더링
├── app/types/
│   └── index.ts                   # 타입 정의
└── app/routes/
    └── property-info.$slug.tsx    # 상세 페이지
```

### 2.2 콘텐츠 타입 시스템

#### ContentType Enum
```python
class ContentType(str, Enum):
    INTERACTIVE_CHART = "interactive_chart"    # Chart.js 기반 인터렉티브 차트
    AI_ARTICLE = "ai_article"                  # AI가 생성한 글
    DATA_VISUALIZATION = "data_visualization"  # SVG/정적 데이터 시각화
    MIXED_CONTENT = "mixed_content"            # 혼합형 콘텐츠
```

#### InfoCategory Enum
```python
class InfoCategory(str, Enum):
    MARKET_ANALYSIS = "market_analysis"        # 시세 분석
    LEGAL_INFO = "legal_info"                  # 법률 정보
    MOVE_IN_GUIDE = "move_in_guide"           # 입주 가이드
    INVESTMENT_TREND = "investment_trend"      # 투자 동향
```

## 3. 콘텐츠 생성 과정

### 3.1 BaseContentCreator 클래스
모든 콘텐츠 생성기의 공통 기능을 제공합니다.

**주요 기능**:
- 슬러그 생성 (`generate_slug`)
- 메타데이터 생성 (`create_metadata`)
- 콘텐츠 유효성 검사 (`validate_content`)
- 기본 태그 제공 (`get_default_tags`)

**메타데이터 구조**:
```python
{
    "type": "property_information",
    "category": str,              # InfoCategory 값
    "content_type": str,          # ContentType 값
    "tags": List[str],           # 최대 3개 태그
    "summary": str,              # 콘텐츠 요약
    "data_source": str,          # 데이터 출처
    "chart_config": Dict,        # 차트 설정 (차트 타입만)
    "seo_keywords": List[str],   # SEO 키워드
    "difficulty_level": str      # 난이도 레벨
}
```

### 3.2 InteractiveChartCreator
Chart.js 기반 인터렉티브 차트를 생성합니다.

**생성 과정**:
1. 카테고리별 기본 제목/데이터 소스 설정
2. 차트 설정 생성 (`_generate_chart_config`)
3. HTML 콘텐츠 생성 (`_generate_interactive_content`)
4. 메타데이터 및 InfoContent 객체 생성

**차트 데이터 예시** (계약 유형별 분포):
```javascript
{
  "labels": ["전세", "월세", "매매", "단기임대"],
  "datasets": [{
    "label": "계약 유형별 비율",
    "data": [45, 35, 15, 5],
    "backgroundColor": [
      "rgba(255, 99, 132, 0.8)",
      "rgba(54, 162, 235, 0.8)",
      "rgba(255, 205, 86, 0.8)",
      "rgba(75, 192, 192, 0.8)"
    ]
  }]
}
```

**생성된 HTML 구조**:
```html
<div class="interactive-chart-container">
  <div class="chart-header">
    <h2>계약 유형별 분포 현황</h2>
    <p class="chart-description">부동산 계약 유형별 비율을 시각화한 차트입니다.</p>
  </div>
  
  <div class="chart-controls">
    <button onclick="resetZoom()">줌 리셋</button>
    <button onclick="downloadChart()">차트 다운로드</button>
  </div>
  
  <div class="chart-wrapper">
    <canvas id="interactiveChart" width="800" height="400"></canvas>
  </div>
  
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
  <script>
    const chartConfig = {...};
    const chart = new Chart(ctx, chartConfig);
  </script>
</div>
```

### 3.3 AI Article Creator
웹 스크래핑 데이터 기반 AI 생성 글을 작성합니다.

**생성 과정**:
1. 카테고리별 기본 데이터 소스 설정
2. 구조화된 HTML 글 생성
3. SEO 키워드 자동 추출
4. 읽기 난이도 설정

### 3.4 DataVisualizationCreator
SVG 기반 정적 데이터 시각화를 생성합니다.

**특징**:
- D3.js 스타일 SVG 그래프
- 반응형 디자인
- 접근성 고려 (alt 텍스트, ARIA 라벨)

### 3.5 MixedContentCreator
텍스트와 시각화를 결합한 혼합 콘텐츠를 생성합니다.

## 4. 프론트엔드 렌더링 시스템

### 4.1 SafeHTMLRenderer 컴포넌트
HTML 콘텐츠를 안전하게 렌더링하고 스크립트를 실행합니다.

**주요 기능**:
- **XSS 방지**: DOMPurify를 통한 HTML 정리
- **스크립트 실행**: Chart.js 등 허용된 스크립트 실행
- **콘텐츠 타입별 설정**: 타입에 따른 허용 태그/속성 조정
- **차트 자동 감지**: 데이터 구조에 따른 차트 타입 자동 결정

**보안 설정**:
```typescript
// 기본 허용 태그
ALLOWED_TAGS: [
  'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li', 'br', 'strong', 'em', 'u', 'b', 'i',
  'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
  'blockquote', 'code', 'pre'
]

// 인터렉티브 차트 추가 허용
ALLOWED_TAGS: [...base, 'canvas', 'script', 'style', 'button']
ALLOWED_ATTR: [...base, 'onclick', 'onchange', 'data-*']
```

### 4.2 차트 렌더링 과정
1. **HTML 삽입**: `dangerouslySetInnerHTML`로 HTML 삽입
2. **스크립트 로드**: Chart.js 라이브러리 동적 로드
3. **설정 추출**: HTML에서 차트 설정 정규식으로 추출
4. **타입 감지**: 데이터 구조 분석으로 차트 타입 결정
5. **차트 생성**: Chart.js 인스턴스 생성 및 렌더링

**차트 타입 자동 감지 로직**:
```typescript
const dataset = chartConfig.data?.datasets?.[0];
if (dataset && Array.isArray(dataset.backgroundColor) && dataset.backgroundColor.length > 1) {
  // 여러 색상 = 파이 차트
  chartConfig.type = 'pie';
}
```

### 4.3 안전성 검증 시스템
```typescript
export function validateContentSafety(content: string): {
  isSafe: boolean;
  warnings: string[];
}
```

**검증 항목**:
- 위험한 스크립트 패턴 (javascript:, eval, setTimeout 등)
- 허용되지 않은 외부 도메인
- XSS 공격 벡터

**허용된 외부 도메인**:
- cdn.jsdelivr.net
- cdnjs.cloudflare.com
- unpkg.com
- d3js.org

## 5. 사용 방법

### 5.1 콘텐츠 생성 스크립트 실행
```python
# 인터렉티브 차트 생성
from scripts.info_content.creators.interactive_creator import InteractiveChartCreator

creator = InteractiveChartCreator()
content = await creator.create_content(
    category=InfoCategory.LEGAL_INFO,
    chart_type="pie",
    title="계약 유형별 분포 분석"
)

# 데이터베이스 저장
post_service = PostService()
await post_service.create_post(content.to_post_dict())
```

### 5.2 프론트엔드에서 확인
1. 정보 페이지 접속: `http://localhost:5173/info`
2. 생성된 글 클릭
3. 상세 페이지에서 콘텐츠 확인: `http://localhost:5173/property-info/{slug}`

## 6. 데이터 플로우

### 6.1 생성 플로우
```
관리자 요청 → ContentCreator → InfoContent 객체 → PostService → MongoDB
```

### 6.2 조회 플로우
```
사용자 요청 → Remix Loader → API 호출 → Post 변환 → InfoItem → SafeHTMLRenderer
```

### 6.3 렌더링 플로우
```
HTML 콘텐츠 → DOMPurify 정리 → DOM 삽입 → 스크립트 실행 → 차트 렌더링
```

## 7. 기술 스택

### 7.1 백엔드
- **Python 3.9+**: 기본 런타임
- **FastAPI**: API 프레임워크
- **Beanie**: MongoDB ODM
- **Pydantic**: 데이터 검증

### 7.2 프론트엔드
- **React 18**: UI 라이브러리
- **Remix**: 풀스택 프레임워크
- **TypeScript**: 타입 안전성
- **DOMPurify**: HTML 정리
- **Chart.js**: 차트 라이브러리

## 8. 보안 고려사항

### 8.1 XSS 방지
- DOMPurify를 통한 HTML 정리
- 허용된 태그/속성만 렌더링
- 외부 리소스 도메인 화이트리스트

### 8.2 스크립트 정책
- 허용된 라이브러리만 로드 (Chart.js, D3.js 등)
- eval, setTimeout 등 위험한 함수 차단
- CSP (Content Security Policy) 적용 권장

### 8.3 데이터 검증
- Pydantic을 통한 백엔드 데이터 검증
- TypeScript를 통한 프론트엔드 타입 안전성
- API 응답 스키마 검증

## 9. 성능 최적화

### 9.1 차트 렌더링
- 라이브러리 중복 로드 방지
- 차트 인스턴스 메모리 정리
- 로딩 상태 표시

### 9.2 콘텐츠 생성
- 비동기 처리
- 데이터베이스 인덱스 최적화
- 캐싱 전략

## 10. 테스트 전략

### 10.1 백엔드 테스트
- 콘텐츠 생성기 단위 테스트
- API 엔드포인트 통합 테스트
- 데이터 검증 테스트

### 10.2 프론트엔드 테스트
- SafeHTMLRenderer 컴포넌트 테스트
- 차트 렌더링 테스트
- 라우팅 테스트

### 10.3 보안 테스트
- XSS 공격 시나리오 테스트
- 허용되지 않은 스크립트 차단 테스트
- 외부 리소스 로드 테스트

## 11. 향후 개선 계획

### 11.1 기능 확장
- 더 많은 차트 타입 지원
- 실시간 데이터 연동
- 사용자 인터랙션 분석

### 11.2 성능 개선
- 서버사이드 렌더링 최적화
- 이미지 레이지 로딩
- CDN 활용

### 11.3 사용자 경험
- 차트 편집 인터페이스
- 모바일 최적화
- 접근성 개선

---

**문서 작성 완료**: 2025년 7월 1일  
**최종 검토**: Claude Code Assistant  
**버전**: 1.0