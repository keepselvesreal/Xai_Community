/**
 * 프론트엔드 성능 측정 유틸리티
 * 기존 병렬 로딩 vs 완전 통합 Aggregation 비교
 */

import { apiClient } from '~/lib/api';

interface PerformanceTestResult {
  method: 'separate' | 'complete';
  loadTime: number;
  success: boolean;
  error?: string;
  timestamp: string;
  dataSize?: number;
}

interface PerformanceTestSummary {
  separate: {
    tests: PerformanceTestResult[];
    average: number;
    min: number;
    max: number;
    median: number;
    successRate: number;
  };
  complete: {
    tests: PerformanceTestResult[];
    average: number;
    min: number;
    max: number;
    median: number;
    successRate: number;
  };
  improvement: {
    averageImprovement: number;
    medianImprovement: number;
    absoluteTimeSaved: number;
  };
}

export class PerformanceTester {
  private testResults: PerformanceTestResult[] = [];

  /**
   * 기존 병렬 로딩 방식 테스트
   */
  async testSeparateLoading(slug: string): Promise<PerformanceTestResult> {
    const startTime = performance.now();
    
    try {
      // 🚀 병렬 로딩: 게시글과 댓글을 동시에 호출
      const [postResult, commentsResult] = await Promise.all([
        apiClient.getPost(slug),
        apiClient.getComments(slug)
      ]);
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // 데이터 크기 계산 (대략적)
      const postSize = JSON.stringify(postResult.data || {}).length;
      const commentsSize = JSON.stringify(commentsResult.data || {}).length;
      const totalSize = postSize + commentsSize;
      
      const success = postResult.success && commentsResult.success;
      
      const result: PerformanceTestResult = {
        method: 'separate',
        loadTime: duration,
        success,
        timestamp: new Date().toISOString(),
        dataSize: totalSize,
        error: success ? undefined : (postResult.error || commentsResult.error)
      };
      
      this.testResults.push(result);
      return result;
      
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      const result: PerformanceTestResult = {
        method: 'separate',
        loadTime: duration,
        success: false,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      this.testResults.push(result);
      return result;
    }
  }

  /**
   * 완전 통합 Aggregation 방식 테스트
   */
  async testCompleteLoading(slug: string): Promise<PerformanceTestResult> {
    const startTime = performance.now();
    
    try {
      // 🚀 완전 통합 Aggregation: 단일 API 호출로 모든 데이터 조회
      const result = await apiClient.getPostComplete(slug);
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // 데이터 크기 계산 (대략적)
      const dataSize = JSON.stringify(result.data || {}).length;
      
      const testResult: PerformanceTestResult = {
        method: 'complete',
        loadTime: duration,
        success: result.success,
        timestamp: new Date().toISOString(),
        dataSize,
        error: result.success ? undefined : result.error
      };
      
      this.testResults.push(testResult);
      return testResult;
      
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      const testResult: PerformanceTestResult = {
        method: 'complete',
        loadTime: duration,
        success: false,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      
      this.testResults.push(testResult);
      return testResult;
    }
  }

  /**
   * 연속 성능 테스트 실행
   */
  async runComparisonTest(slug: string, rounds: number = 10): Promise<PerformanceTestSummary> {
    console.log(`🚀 성능 비교 테스트 시작 - ${rounds}회 실행`);
    
    const separateResults: PerformanceTestResult[] = [];
    const completeResults: PerformanceTestResult[] = [];
    
    for (let i = 0; i < rounds; i++) {
      console.log(`🔄 Round ${i + 1}/${rounds}`);
      
      // 기존 방식 테스트
      const separateResult = await this.testSeparateLoading(slug);
      separateResults.push(separateResult);
      console.log(`   기존 방식: ${separateResult.loadTime.toFixed(2)}ms ${separateResult.success ? '✅' : '❌'}`);
      
      // 잠깐 대기
      await this.sleep(100);
      
      // 완전 통합 방식 테스트
      const completeResult = await this.testCompleteLoading(slug);
      completeResults.push(completeResult);
      console.log(`   완전 통합: ${completeResult.loadTime.toFixed(2)}ms ${completeResult.success ? '✅' : '❌'}`);
      
      // 라운드 간 대기
      await this.sleep(200);
    }
    
    // 통계 계산
    const summary = this.calculateSummary(separateResults, completeResults);
    
    console.log('📊 성능 비교 테스트 완료');
    console.log(`   기존 방식 평균: ${summary.separate.average.toFixed(2)}ms`);
    console.log(`   완전 통합 평균: ${summary.complete.average.toFixed(2)}ms`);
    console.log(`   성능 개선: ${summary.improvement.averageImprovement.toFixed(1)}%`);
    
    return summary;
  }

  /**
   * 통계 계산
   */
  private calculateSummary(
    separateResults: PerformanceTestResult[], 
    completeResults: PerformanceTestResult[]
  ): PerformanceTestSummary {
    const separateSuccessful = separateResults.filter(r => r.success);
    const completeSuccessful = completeResults.filter(r => r.success);
    
    const separateTimes = separateSuccessful.map(r => r.loadTime);
    const completeTimes = completeSuccessful.map(r => r.loadTime);
    
    const separateStats = this.calculateStats(separateTimes);
    const completeStats = this.calculateStats(completeTimes);
    
    const averageImprovement = separateStats.average > 0 
      ? ((separateStats.average - completeStats.average) / separateStats.average) * 100 
      : 0;
    
    const medianImprovement = separateStats.median > 0 
      ? ((separateStats.median - completeStats.median) / separateStats.median) * 100 
      : 0;
    
    return {
      separate: {
        tests: separateResults,
        ...separateStats,
        successRate: (separateSuccessful.length / separateResults.length) * 100
      },
      complete: {
        tests: completeResults,
        ...completeStats,
        successRate: (completeSuccessful.length / completeResults.length) * 100
      },
      improvement: {
        averageImprovement,
        medianImprovement,
        absoluteTimeSaved: separateStats.average - completeStats.average
      }
    };
  }

  /**
   * 기본 통계 계산
   */
  private calculateStats(times: number[]) {
    if (times.length === 0) {
      return { average: 0, min: 0, max: 0, median: 0 };
    }
    
    const sorted = [...times].sort((a, b) => a - b);
    const average = times.reduce((sum, time) => sum + time, 0) / times.length;
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    const median = sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];
    
    return { average, min, max, median };
  }

  /**
   * 대기 함수
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 결과를 CSV 형태로 내보내기
   */
  exportToCSV(summary: PerformanceTestSummary): string {
    const headers = [
      'Method',
      'Round',
      'LoadTime(ms)',
      'Success',
      'DataSize(bytes)',
      'Timestamp',
      'Error'
    ];
    
    const rows: string[] = [headers.join(',')];
    
    // 기존 방식 결과
    summary.separate.tests.forEach((test, index) => {
      rows.push([
        'separate',
        String(index + 1),
        test.loadTime.toFixed(2),
        String(test.success),
        String(test.dataSize || ''),
        test.timestamp,
        test.error || ''
      ].join(','));
    });
    
    // 완전 통합 방식 결과
    summary.complete.tests.forEach((test, index) => {
      rows.push([
        'complete',
        String(index + 1),
        test.loadTime.toFixed(2),
        String(test.success),
        String(test.dataSize || ''),
        test.timestamp,
        test.error || ''
      ].join(','));
    });
    
    return rows.join('\n');
  }

  /**
   * 결과 초기화
   */
  clearResults(): void {
    this.testResults = [];
  }
}

// 싱글톤 인스턴스
export const performanceTester = new PerformanceTester();