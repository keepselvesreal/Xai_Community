/**
 * 게시판 상세 페이지 성능 비교 테스트
 * 
 * 비교 대상:
 * 1. 기존 방식: 개별 API 호출 (게시글 + 댓글 별도 조회)
 * 2. Full 엔드포인트: /api/posts/{slug}/full (Aggregation 방식)
 * 3. Aggregated 엔드포인트: /api/posts/{slug}/aggregated (게시글 + 작성자만)
 */

const API_BASE_URL = 'https://xai-community-backend-798170408536.asia-northeast3.run.app';
const TEST_SLUG = 'test-post-performance'; // 테스트용 게시글 슬러그
const TEST_ITERATIONS = 10; // 각 방식당 측정 횟수

class PerformanceTest {
    constructor() {
        this.results = {
            separate: [],
            full: [],
            aggregated: []
        };
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async measureTime(fn) {
        const start = performance.now();
        await fn();
        const end = performance.now();
        return end - start;
    }

    async fetchWithRetry(url, options = {}, retries = 3) {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                if (i === retries - 1) throw error;
                await this.delay(1000 * (i + 1)); // 점진적 지연
            }
        }
    }

    /**
     * 방식 1: 기존 개별 API 호출
     */
    async testSeparateAPIs() {
        console.log('🔄 방식 1: 개별 API 호출 테스트 시작');
        
        for (let i = 0; i < TEST_ITERATIONS; i++) {
            const time = await this.measureTime(async () => {
                try {
                    // 병렬로 게시글과 댓글 조회
                    const [postResponse, commentsResponse] = await Promise.all([
                        this.fetchWithRetry(`${API_BASE_URL}/api/posts/${TEST_SLUG}`),
                        this.fetchWithRetry(`${API_BASE_URL}/api/posts/${TEST_SLUG}/comments`)
                    ]);
                    
                    // 데이터 검증
                    if (!postResponse.id || !commentsResponse.data) {
                        throw new Error('Invalid response data');
                    }
                } catch (error) {
                    console.error(`개별 API 호출 테스트 ${i + 1} 실패:`, error);
                    throw error;
                }
            });
            
            this.results.separate.push(time);
            console.log(`  테스트 ${i + 1}: ${time.toFixed(2)}ms`);
            
            // 서버 부하 방지를 위한 간격
            await this.delay(100);
        }
    }

    /**
     * 방식 2: Full Aggregation 엔드포인트
     */
    async testFullEndpoint() {
        console.log('🔄 방식 2: Full Aggregation 엔드포인트 테스트 시작');
        
        for (let i = 0; i < TEST_ITERATIONS; i++) {
            const time = await this.measureTime(async () => {
                try {
                    const response = await this.fetchWithRetry(`${API_BASE_URL}/api/posts/${TEST_SLUG}/full`);
                    
                    // 데이터 검증
                    if (!response.data || !response.data.id) {
                        throw new Error('Invalid response data');
                    }
                } catch (error) {
                    console.error(`Full 엔드포인트 테스트 ${i + 1} 실패:`, error);
                    throw error;
                }
            });
            
            this.results.full.push(time);
            console.log(`  테스트 ${i + 1}: ${time.toFixed(2)}ms`);
            
            await this.delay(100);
        }
    }

    /**
     * 방식 3: Aggregated 엔드포인트 (게시글 + 작성자만)
     */
    async testAggregatedEndpoint() {
        console.log('🔄 방식 3: Aggregated 엔드포인트 테스트 시작');
        
        for (let i = 0; i < TEST_ITERATIONS; i++) {
            const time = await this.measureTime(async () => {
                try {
                    const response = await this.fetchWithRetry(`${API_BASE_URL}/api/posts/${TEST_SLUG}/aggregated`);
                    
                    // 데이터 검증
                    if (!response.data || !response.data.id) {
                        throw new Error('Invalid response data');
                    }
                } catch (error) {
                    console.error(`Aggregated 엔드포인트 테스트 ${i + 1} 실패:`, error);
                    throw error;
                }
            });
            
            this.results.aggregated.push(time);
            console.log(`  테스트 ${i + 1}: ${time.toFixed(2)}ms`);
            
            await this.delay(100);
        }
    }

    /**
     * 통계 계산
     */
    calculateStats(times) {
        const sorted = times.sort((a, b) => a - b);
        const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
        const median = sorted[Math.floor(times.length / 2)];
        const min = sorted[0];
        const max = sorted[sorted.length - 1];
        const stdDev = Math.sqrt(
            times.reduce((sum, time) => sum + Math.pow(time - avg, 2), 0) / times.length
        );

        return {
            avg: parseFloat(avg.toFixed(2)),
            median: parseFloat(median.toFixed(2)),
            min: parseFloat(min.toFixed(2)),
            max: parseFloat(max.toFixed(2)),
            stdDev: parseFloat(stdDev.toFixed(2))
        };
    }

    /**
     * 결과 출력
     */
    printResults() {
        console.log('\n📊 성능 테스트 결과 요약');
        console.log('=' * 50);
        
        const separateStats = this.calculateStats(this.results.separate);
        const fullStats = this.calculateStats(this.results.full);
        const aggregatedStats = this.calculateStats(this.results.aggregated);
        
        console.log('\n🔹 개별 API 호출 (기존 방식)');
        console.log(`평균: ${separateStats.avg}ms`);
        console.log(`중간값: ${separateStats.median}ms`);
        console.log(`최소: ${separateStats.min}ms`);
        console.log(`최대: ${separateStats.max}ms`);
        console.log(`표준편차: ${separateStats.stdDev}ms`);
        
        console.log('\n🔹 Full Aggregation 엔드포인트');
        console.log(`평균: ${fullStats.avg}ms`);
        console.log(`중간값: ${fullStats.median}ms`);
        console.log(`최소: ${fullStats.min}ms`);
        console.log(`최대: ${fullStats.max}ms`);
        console.log(`표준편차: ${fullStats.stdDev}ms`);
        
        console.log('\n🔹 Aggregated 엔드포인트 (게시글+작성자)');
        console.log(`평균: ${aggregatedStats.avg}ms`);
        console.log(`중간값: ${aggregatedStats.median}ms`);
        console.log(`최소: ${aggregatedStats.min}ms`);
        console.log(`최대: ${aggregatedStats.max}ms`);
        console.log(`표준편차: ${aggregatedStats.stdDev}ms`);
        
        console.log('\n📈 성능 비교');
        console.log('=' * 50);
        
        const baselineAvg = separateStats.avg;
        const fullImprovement = ((baselineAvg - fullStats.avg) / baselineAvg * 100).toFixed(1);
        const aggregatedImprovement = ((baselineAvg - aggregatedStats.avg) / baselineAvg * 100).toFixed(1);
        
        console.log(`Full 엔드포인트: ${fullImprovement}% ${fullImprovement > 0 ? '개선' : '저하'}`);
        console.log(`Aggregated 엔드포인트: ${aggregatedImprovement}% ${aggregatedImprovement > 0 ? '개선' : '저하'}`);
        
        // 추천 사항
        console.log('\n🎯 추천 사항');
        console.log('=' * 50);
        
        if (fullStats.avg < separateStats.avg && fullStats.avg < aggregatedStats.avg) {
            console.log('✅ Full Aggregation 엔드포인트가 가장 빠름');
            console.log('   - 게시글과 댓글을 모두 필요로 하는 상세 페이지에 적합');
        } else if (aggregatedStats.avg < separateStats.avg) {
            console.log('✅ Aggregated 엔드포인트가 기존 방식보다 빠름');
            console.log('   - 댓글 로딩을 지연시키고 게시글 내용을 먼저 표시하는 방식에 적합');
        } else {
            console.log('⚠️ 기존 방식이 여전히 경쟁력 있음');
            console.log('   - 네트워크 병렬성의 장점이 서버 측 최적화를 상쇄');
        }

        return {
            separate: separateStats,
            full: fullStats,
            aggregated: aggregatedStats,
            improvements: {
                full: fullImprovement,
                aggregated: aggregatedImprovement
            }
        };
    }

    /**
     * 전체 테스트 실행
     */
    async runAll() {
        console.log(`🚀 게시판 상세 페이지 성능 테스트 시작`);
        console.log(`📋 테스트 설정: ${TEST_ITERATIONS}회 반복, 대상 게시글: ${TEST_SLUG}`);
        console.log(`🌐 API 서버: ${API_BASE_URL}`);
        
        try {
            // 1. 개별 API 호출 테스트
            await this.testSeparateAPIs();
            console.log('✅ 개별 API 호출 테스트 완료\n');
            
            // 2. Full 엔드포인트 테스트
            await this.testFullEndpoint();
            console.log('✅ Full 엔드포인트 테스트 완료\n');
            
            // 3. Aggregated 엔드포인트 테스트
            await this.testAggregatedEndpoint();
            console.log('✅ Aggregated 엔드포인트 테스트 완료\n');
            
            // 4. 결과 출력
            return this.printResults();
            
        } catch (error) {
            console.error('❌ 테스트 실행 중 오류 발생:', error);
            throw error;
        }
    }
}

// 브라우저 환경에서 실행
if (typeof window !== 'undefined') {
    // 전역 함수로 노출
    window.runPerformanceTest = async () => {
        const test = new PerformanceTest();
        return await test.runAll();
    };
    
    console.log('🎯 성능 테스트 준비 완료');
    console.log('📝 실행 방법: runPerformanceTest()');
}

// Node.js 환경에서 실행
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceTest;
}