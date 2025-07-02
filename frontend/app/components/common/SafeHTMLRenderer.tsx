import { useMemo, useEffect, useRef, useState } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import type { ContentType } from '~/types';

interface SafeHTMLRendererProps {
  content: string;
  contentType: ContentType;
  className?: string;
}

/**
 * HTML 콘텐츠를 안전하게 렌더링하는 컴포넌트
 * XSS 공격을 방지하고 허용된 태그와 속성만 렌더링합니다.
 */
export default function SafeHTMLRenderer({ 
  content, 
  contentType, 
  className = "" 
}: SafeHTMLRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isChartLoading, setIsChartLoading] = useState(contentType === 'interactive_chart');
  
  const sanitizedHTML = useMemo(() => {
    if (!content) return '';
    
    // 콘텐츠 타입별 허용 설정
    const config = getContentTypeConfig(contentType);
    
    // DOMPurify로 HTML 정리
    const cleaned = DOMPurify.sanitize(content, config);
    
    return cleaned;
  }, [content, contentType]);

  // 인터랙티브 차트를 위한 스크립트 실행
  useEffect(() => {
    if (!containerRef.current || !sanitizedHTML || contentType !== 'interactive_chart') {
      return;
    }

    const executeChartScripts = async () => {
      try {
        // Chart.js 라이브러리 로드
        await loadScript('https://cdn.jsdelivr.net/npm/chart.js');
        await loadScript('https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom');

        // 차트 설정 추출
        const chartConfigMatch = sanitizedHTML.match(/const chartConfig = ({[\s\S]*?});/);
        if (!chartConfigMatch) {
          console.warn('Chart config not found in content');
          return;
        }

        // 차트 설정 파싱
        const configCode = chartConfigMatch[1];
        const chartConfig = new Function('return ' + configCode)();

        // 데이터 타입에 따라 차트 타입 자동 감지
        const dataset = chartConfig.data?.datasets?.[0];
        if (dataset && Array.isArray(dataset.backgroundColor) && dataset.backgroundColor.length > 1) {
          // 여러 색상이 있으면 pie 또는 doughnut 차트로 추정
          chartConfig.type = 'pie';
        }

        // 캔버스 요소 찾기
        const canvas = containerRef.current!.querySelector('#interactiveChart') as HTMLCanvasElement;
        if (!canvas) {
          console.warn('Canvas element not found');
          return;
        }

        // Chart.js로 차트 생성
        const ctx = canvas.getContext('2d');
        if (ctx && (window as any).Chart) {
          const Chart = (window as any).Chart;
          
          // 기존 차트가 있다면 제거
          Chart.getChart(canvas)?.destroy();

          // 차트 타입에 따른 옵션 조정
          const chartOptions: any = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              ...chartConfig.plugins,
              legend: {
                display: true,
                position: 'bottom'
              }
            }
          };

          // pie 차트가 아닌 경우에만 줌/팬 기능 추가
          if (chartConfig.type !== 'pie' && chartConfig.type !== 'doughnut') {
            chartOptions.plugins.zoom = {
              zoom: {
                wheel: { enabled: true },
                pinch: { enabled: true },
                mode: 'xy',
              },
              pan: {
                enabled: true,
                mode: 'xy',
              }
            };
            chartOptions.interaction = {
              intersect: false,
              mode: 'index'
            };
            chartOptions.scales = chartConfig.scales;
          }

          const chart = new Chart(ctx, {
            type: chartConfig.type,
            data: chartConfig.data,
            options: chartOptions
          });

          // 전역 함수 추가
          (window as any).resetZoom = () => chart.resetZoom?.();
          (window as any).downloadChart = () => {
            const link = document.createElement('a');
            link.download = 'chart.png';
            link.href = chart.toBase64Image();
            link.click();
          };

          // 차트 로딩 완료
          setIsChartLoading(false);
        }
      } catch (error) {
        console.error('Chart initialization failed:', error);
        setIsChartLoading(false);
      }
    };

    executeChartScripts();

    // 정리 함수
    return () => {
      if (containerRef.current) {
        const canvas = containerRef.current.querySelector('#interactiveChart') as HTMLCanvasElement;
        if (canvas && (window as any).Chart) {
          (window as any).Chart.getChart(canvas)?.destroy();
        }
      }
    };
  }, [sanitizedHTML, contentType]);

  // 스크립트 로드 헬퍼 함수
  const loadScript = (src: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);
    });
  };

  // 콘텐츠가 없으면 빈 div 반환
  if (!sanitizedHTML) {
    return <div className={className} />;
  }

  return (
    <div 
      ref={containerRef}
      className={`safe-html-content ${className} ${getContentTypeClass(contentType)} ${contentType === 'interactive_chart' ? 'relative' : ''}`}
    >
      {/* 차트 로딩 중 표시 */}
      {isChartLoading && contentType === 'interactive_chart' && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-gray-600">차트를 로딩 중입니다...</p>
          </div>
        </div>
      )}
      
      {/* HTML 콘텐츠 */}
      <div dangerouslySetInnerHTML={{ __html: sanitizedHTML }} />
    </div>
  );
}

/**
 * 콘텐츠 타입별 DOMPurify 설정 반환
 */
function getContentTypeConfig(contentType: ContentType) {
  const baseConfig = {
    ALLOWED_TAGS: [
      'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'br', 'strong', 'em', 'u', 'b', 'i',
      'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
      'blockquote', 'code', 'pre'
    ],
    ALLOWED_ATTR: [
      'class', 'id', 'style', 'href', 'src', 'alt', 'title',
      'width', 'height', 'target', 'rel'
    ],
    ALLOW_DATA_ATTR: false,
    KEEP_CONTENT: true
  };

  switch (contentType) {
    case 'interactive_chart':
      return {
        ...baseConfig,
        ALLOWED_TAGS: [
          ...baseConfig.ALLOWED_TAGS,
          'canvas', 'script', 'style', 'button', 'input', 'select', 'option'
        ],
        ALLOWED_ATTR: [
          ...baseConfig.ALLOWED_ATTR,
          'onclick', 'onchange', 'data-*', 'type', 'value', 'name'
        ],
        ALLOW_DATA_ATTR: true,
        ADD_TAGS: ['script'],
        ADD_ATTR: ['onclick', 'onchange']
      };
    
    case 'data_visualization':
      return {
        ...baseConfig,
        ALLOWED_TAGS: [
          ...baseConfig.ALLOWED_TAGS,
          'svg', 'path', 'circle', 'rect', 'line', 'text', 'g', 'defs',
          'pattern', 'gradient', 'stop'
        ],
        ALLOWED_ATTR: [
          ...baseConfig.ALLOWED_ATTR,
          'viewBox', 'xmlns', 'd', 'fill', 'stroke', 'stroke-width',
          'cx', 'cy', 'r', 'x', 'y', 'x1', 'y1', 'x2', 'y2',
          'transform', 'text-anchor'
        ]
      };
    
    case 'mixed_content':
      return {
        ...baseConfig,
        ALLOWED_TAGS: [
          ...baseConfig.ALLOWED_TAGS,
          'canvas', 'svg', 'path', 'circle', 'rect', 'button',
          'script', 'style'
        ],
        ALLOWED_ATTR: [
          ...baseConfig.ALLOWED_ATTR,
          'viewBox', 'xmlns', 'd', 'fill', 'stroke', 'cx', 'cy', 'r',
          'onclick', 'data-*'
        ],
        ALLOW_DATA_ATTR: true
      };
    
    case 'ai_article':
    default:
      return baseConfig;
  }
}

/**
 * 콘텐츠 타입별 CSS 클래스 반환
 */
function getContentTypeClass(contentType: ContentType): string {
  const classMap = {
    'interactive_chart': 'content-interactive',
    'ai_article': 'content-article',
    'data_visualization': 'content-visualization',
    'mixed_content': 'content-mixed'
  };
  
  return classMap[contentType] || 'content-default';
}

/**
 * 콘텐츠 안전성 검증
 */
export function validateContentSafety(content: string): {
  isSafe: boolean;
  warnings: string[];
} {
  const warnings: string[] = [];
  
  // 잠재적으로 위험한 패턴 검사
  const dangerousPatterns = [
    /javascript:/gi,
    /vbscript:/gi,
    /data:text\/html/gi,
    /on\w+\s*=/gi, // onload, onclick 등
    /<script[^>]*>(?!.*chart|.*d3|.*plotly)/gi, // 허용된 라이브러리 외 스크립트
    /eval\s*\(/gi,
    /setTimeout\s*\(/gi,
    /setInterval\s*\(/gi
  ];
  
  for (const pattern of dangerousPatterns) {
    if (pattern.test(content)) {
      warnings.push(`잠재적으로 위험한 패턴 발견: ${pattern.source}`);
    }
  }
  
  // 허용된 외부 리소스 도메인
  const allowedDomains = [
    'cdn.jsdelivr.net',
    'cdnjs.cloudflare.com',
    'unpkg.com',
    'code.jquery.com',
    'd3js.org'
  ];
  
  const externalResourcePattern = /src\s*=\s*["']https?:\/\/([^"'\/]+)/gi;
  let match;
  
  while ((match = externalResourcePattern.exec(content)) !== null) {
    const domain = match[1];
    if (!allowedDomains.some(allowed => domain.includes(allowed))) {
      warnings.push(`허용되지 않은 외부 도메인: ${domain}`);
    }
  }
  
  return {
    isSafe: warnings.length === 0,
    warnings
  };
}