/**
 * Phase 4 프론트엔드 성능 측정 도구
 * 게시판 상세 페이지 최적화 전후 비교
 */

// 백엔드 성능 기준점 (Phase 3 결과)
const BACKEND_BENCHMARKS = {
  aggregated: 36.61, // ms
  parallel: 137.57,  // ms
  complete: 68.22    // ms
};

// 테스트할 게시글 URL
const TEST_POST_URL = 'http://localhost:5173/board/686c6cd040839f99492cab46-25-07-08-글쓰기';

/**
 * 프론트엔드 성능 지표 측정
 */
async function measureFrontendPerformance(page) {
  // Navigation Timing API 사용
  const performanceMetrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      // 페이지 로드 완료 확인
      if (document.readyState === 'complete') {
        measureAndResolve();
      } else {
        window.addEventListener('load', measureAndResolve);
      }
      
      function measureAndResolve() {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');
        
        // Core Web Vitals 측정
        const fcp = paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0;
        const lcp = performance.getEntriesByType('largest-contentful-paint')[0]?.startTime || 0;
        
        resolve({
          // 기본 타이밍
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          
          // Core Web Vitals
          firstContentfulPaint: fcp,
          largestContentfulPaint: lcp,
          
          // 전체 로딩 시간
          totalLoadTime: navigation.loadEventEnd - navigation.fetchStart,
          
          // DNS + Connection + Response
          networkTime: navigation.responseEnd - navigation.fetchStart,
          
          // DOM 처리 시간
          domProcessingTime: navigation.domComplete - navigation.domLoading,
          
          // 현재 타임스탬프
          timestamp: Date.now()
        });
      }
    });
  });
  
  return performanceMetrics;
}

/**
 * API 응답 시간 측정 (프론트엔드에서)
 */
async function measureAPIResponseTimes(page) {
  return await page.evaluate(() => {
    return new Promise((resolve) => {
      const apiTimes = [];
      
      // Performance Observer로 API 호출 감지
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name.includes('/api/posts/')) {
            apiTimes.push({
              url: entry.name,
              duration: entry.duration,
              startTime: entry.startTime,
              responseEnd: entry.responseEnd
            });
          }
        }
      });
      
      observer.observe({ entryTypes: ['resource'] });
      
      // 5초 후 결과 반환
      setTimeout(() => {
        observer.disconnect();
        resolve(apiTimes);
      }, 5000);
    });
  });
}

/**
 * 단일 테스트 실행
 */
async function runSingleTest(page, testName) {
  console.log(`\n🔍 ${testName} 테스트 시작...`);
  
  const startTime = Date.now();
  
  try {
    // 페이지 로드
    await page.goto(TEST_POST_URL, { 
      waitUntil: 'networkidle0',
      timeout: 30000 
    });
    
    // 성능 지표 측정
    const [frontendMetrics, apiTimes] = await Promise.all([
      measureFrontendPerformance(page),
      measureAPIResponseTimes(page)
    ]);
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    return {
      testName,
      success: true,
      totalTime,
      frontendMetrics,
      apiTimes,
      timestamp: new Date().toISOString()
    };
    
  } catch (error) {
    console.error(`❌ ${testName} 실패:`, error.message);
    return {
      testName,
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * 성능 분석 및 보고
 */
function analyzeResults(results) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 Phase 4 프론트엔드 성능 분석 결과');
  console.log('='.repeat(60));
  
  const successfulResults = results.filter(r => r.success);
  
  if (successfulResults.length === 0) {
    console.log('❌ 성공한 테스트가 없습니다.');
    return;
  }
  
  // 평균 계산
  const avgMetrics = {
    totalTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    domContentLoaded: 0,
    loadComplete: 0,
    networkTime: 0,
    domProcessingTime: 0
  };
  
  successfulResults.forEach(result => {
    avgMetrics.totalTime += result.totalTime;
    avgMetrics.firstContentfulPaint += result.frontendMetrics.firstContentfulPaint;
    avgMetrics.largestContentfulPaint += result.frontendMetrics.largestContentfulPaint;
    avgMetrics.domContentLoaded += result.frontendMetrics.domContentLoaded;
    avgMetrics.loadComplete += result.frontendMetrics.loadComplete;
    avgMetrics.networkTime += result.frontendMetrics.networkTime;
    avgMetrics.domProcessingTime += result.frontendMetrics.domProcessingTime;
  });
  
  const count = successfulResults.length;
  Object.keys(avgMetrics).forEach(key => {
    avgMetrics[key] = avgMetrics[key] / count;
  });
  
  // 결과 출력
  console.log(`\n📈 성능 지표 (${count}회 평균):`);
  console.log(`   전체 로딩 시간: ${avgMetrics.totalTime.toFixed(2)}ms`);
  console.log(`   First Contentful Paint: ${avgMetrics.firstContentfulPaint.toFixed(2)}ms`);
  console.log(`   Largest Contentful Paint: ${avgMetrics.largestContentfulPaint.toFixed(2)}ms`);
  console.log(`   DOM Content Loaded: ${avgMetrics.domContentLoaded.toFixed(2)}ms`);
  console.log(`   Load Complete: ${avgMetrics.loadComplete.toFixed(2)}ms`);
  console.log(`   네트워크 시간: ${avgMetrics.networkTime.toFixed(2)}ms`);
  console.log(`   DOM 처리 시간: ${avgMetrics.domProcessingTime.toFixed(2)}ms`);
  
  // 백엔드 성능과 비교
  console.log(`\n🔄 백엔드 API 성능 비교:`);
  console.log(`   Aggregated API: ${BACKEND_BENCHMARKS.aggregated}ms`);
  console.log(`   Parallel API: ${BACKEND_BENCHMARKS.parallel}ms`);
  console.log(`   Complete API: ${BACKEND_BENCHMARKS.complete}ms`);
  
  // Core Web Vitals 평가
  console.log(`\n⚡ Core Web Vitals 평가:`);
  const fcpGood = avgMetrics.firstContentfulPaint < 1800;
  const lcpGood = avgMetrics.largestContentfulPaint < 2500;
  
  console.log(`   FCP: ${fcpGood ? '✅ 좋음' : '⚠️ 개선 필요'} (${avgMetrics.firstContentfulPaint.toFixed(2)}ms)`);
  console.log(`   LCP: ${lcpGood ? '✅ 좋음' : '⚠️ 개선 필요'} (${avgMetrics.largestContentfulPaint.toFixed(2)}ms)`);
  
  return {
    averageMetrics: avgMetrics,
    successfulTests: count,
    totalTests: results.length,
    coreWebVitals: {
      fcp: { value: avgMetrics.firstContentfulPaint, good: fcpGood },
      lcp: { value: avgMetrics.largestContentfulPaint, good: lcpGood }
    }
  };
}

/**
 * 메인 테스트 실행
 */
async function runPerformanceTest() {
  console.log('🚀 Phase 4 프론트엔드 성능 측정 시작');
  console.log(`📍 테스트 URL: ${TEST_POST_URL}`);
  console.log(`📅 테스트 시작: ${new Date().toLocaleString('ko-KR')}`);
  
  // Puppeteer 설정이 없다면 기본 브라우저 API 사용 안내
  console.log('\n⚠️  이 스크립트는 브라우저 환경에서 실행되어야 합니다.');
  console.log('브라우저 개발자 도구 콘솔에서 다음 코드를 실행하세요:\n');
  
  // 브라우저에서 직접 실행할 수 있는 코드 제공
  const browserTestCode = `
// 프론트엔드 성능 측정 (브라우저 콘솔에서 실행)
(async function() {
  console.log('🚀 프론트엔드 성능 측정 시작');
  
  const results = [];
  const iterations = 5;
  
  for (let i = 0; i < iterations; i++) {
    console.log(\`\n📊 테스트 \${i + 1}/\${iterations} 실행 중...\`);
    
    const startTime = performance.now();
    
    // 페이지 새로고침
    await new Promise(resolve => {
      window.location.reload();
      window.addEventListener('load', resolve, { once: true });
    });
    
    const endTime = performance.now();
    
    // 성능 지표 수집
    const navigation = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');
    
    const fcp = paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0;
    const lcp = performance.getEntriesByType('largest-contentful-paint')[0]?.startTime || 0;
    
    results.push({
      iteration: i + 1,
      totalTime: endTime - startTime,
      firstContentfulPaint: fcp,
      largestContentfulPaint: lcp,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      networkTime: navigation.responseEnd - navigation.fetchStart
    });
    
    // 잠시 대기
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // 결과 분석
  const avgMetrics = results.reduce((acc, result) => {
    Object.keys(result).forEach(key => {
      if (key !== 'iteration') {
        acc[key] = (acc[key] || 0) + result[key];
      }
    });
    return acc;
  }, {});
  
  Object.keys(avgMetrics).forEach(key => {
    avgMetrics[key] = avgMetrics[key] / results.length;
  });
  
  console.log('\\n📊 Phase 4 프론트엔드 성능 결과:');
  console.log('평균 전체 로딩 시간:', avgMetrics.totalTime.toFixed(2) + 'ms');
  console.log('평균 FCP:', avgMetrics.firstContentfulPaint.toFixed(2) + 'ms');
  console.log('평균 LCP:', avgMetrics.largestContentfulPaint.toFixed(2) + 'ms');
  console.log('평균 DOM Content Loaded:', avgMetrics.domContentLoaded.toFixed(2) + 'ms');
  console.log('평균 네트워크 시간:', avgMetrics.networkTime.toFixed(2) + 'ms');
  
  return { results, avgMetrics };
})();
`;
  
  console.log(browserTestCode);
  
  return {
    message: '브라우저 콘솔에서 위 코드를 실행하여 성능을 측정하세요.',
    testUrl: TEST_POST_URL,
    browserTestCode
  };
}

// Node.js 환경에서 실행 시
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    runPerformanceTest,
    measureFrontendPerformance,
    analyzeResults,
    BACKEND_BENCHMARKS
  };
}

// 직접 실행 시
if (typeof window === 'undefined') {
  runPerformanceTest().then(result => {
    console.log('\n💾 결과를 저장하려면 브라우저에서 테스트를 실행하세요.');
  });
}