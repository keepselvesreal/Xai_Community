/**
 * 성능 측정 유틸리티
 * 추천/비추천 버튼 반응 속도 측정용
 */

export interface PerformanceMeasurement {
  startTime: number;
  endTime: number;
  duration: number;
  operation: string;
  metadata?: Record<string, any>;
}

export class PerformanceMeasurer {
  private measurements: PerformanceMeasurement[] = [];
  private activeOperations: Map<string, number> = new Map();

  /**
   * 성능 측정 시작
   */
  start(operation: string, metadata?: Record<string, any>): void {
    const startTime = performance.now();
    this.activeOperations.set(operation, startTime);
    
    console.log(`⏱️ 측정 시작: ${operation}`, metadata);
  }

  /**
   * 성능 측정 종료
   */
  end(operation: string, metadata?: Record<string, any>): PerformanceMeasurement | null {
    const endTime = performance.now();
    const startTime = this.activeOperations.get(operation);

    if (!startTime) {
      console.warn(`⚠️ 측정 시작되지 않은 작업: ${operation}`);
      return null;
    }

    const duration = endTime - startTime;
    const measurement: PerformanceMeasurement = {
      startTime,
      endTime,
      duration,
      operation,
      metadata
    };

    this.measurements.push(measurement);
    this.activeOperations.delete(operation);

    console.log(`✅ 측정 완료: ${operation} - ${duration.toFixed(2)}ms`, metadata);
    return measurement;
  }

  /**
   * 특정 작업의 통계 조회
   */
  getStats(operation: string): {
    count: number;
    averageDuration: number;
    minDuration: number;
    maxDuration: number;
    measurements: PerformanceMeasurement[];
  } {
    const operationMeasurements = this.measurements.filter(m => m.operation === operation);
    
    if (operationMeasurements.length === 0) {
      return {
        count: 0,
        averageDuration: 0,
        minDuration: 0,
        maxDuration: 0,
        measurements: []
      };
    }

    const durations = operationMeasurements.map(m => m.duration);
    
    return {
      count: operationMeasurements.length,
      averageDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      measurements: operationMeasurements
    };
  }

  /**
   * 모든 측정 데이터 조회
   */
  getAllMeasurements(): PerformanceMeasurement[] {
    return [...this.measurements];
  }

  /**
   * 측정 데이터 초기화
   */
  clear(): void {
    this.measurements = [];
    this.activeOperations.clear();
  }

  /**
   * 성능 보고서 출력
   */
  printReport(): void {
    const operations = [...new Set(this.measurements.map(m => m.operation))];
    
    console.log('\n📊 성능 측정 보고서');
    console.log('==================');
    
    operations.forEach(operation => {
      const stats = this.getStats(operation);
      console.log(`\n🔍 ${operation}:`);
      console.log(`  - 측정 횟수: ${stats.count}회`);
      console.log(`  - 평균 시간: ${stats.averageDuration.toFixed(2)}ms`);
      console.log(`  - 최소 시간: ${stats.minDuration.toFixed(2)}ms`);
      console.log(`  - 최대 시간: ${stats.maxDuration.toFixed(2)}ms`);
    });
  }
}

// 전역 성능 측정기 인스턴스
export const performanceMeasurer = new PerformanceMeasurer();

/**
 * 반응 버튼 클릭 성능 측정용 데코레이터
 */
export function measureReactionPerformance<T extends (...args: any[]) => Promise<any>>(
  operation: string,
  fn: T
): T {
  return (async (...args: any[]) => {
    const operationId = `${operation}_${Date.now()}`;
    performanceMeasurer.start(operationId, { args });
    
    try {
      const result = await fn(...args);
      performanceMeasurer.end(operationId, { success: true });
      return result;
    } catch (error) {
      performanceMeasurer.end(operationId, { success: false, error: error.message });
      throw error;
    }
  }) as T;
}