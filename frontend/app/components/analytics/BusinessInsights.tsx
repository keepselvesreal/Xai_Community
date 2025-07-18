import React from 'react';
import type { BusinessInsights as BusinessInsightsType } from '~/types/analytics';
import { MetricCard } from './MetricCard';
import { TrendChart } from './TrendChart';

interface BusinessInsightsProps {
  data: BusinessInsightsType;
  className?: string;
}

export function BusinessInsights({ data, className = '' }: BusinessInsightsProps) {
  // 페이지별 성과 차트 데이터
  const pagePerformanceData = {
    labels: data.pageTypePerformance.map(page => page.displayName),
    datasets: [
      {
        label: '게시글 수',
        data: data.pageTypePerformance.map(page => page.totalPosts),
        backgroundColor: '#3B82F6'
      },
      {
        label: '조회수',
        data: data.pageTypePerformance.map(page => page.totalViews),
        backgroundColor: '#10B981'
      }
    ]
  };

  // 성장률 차트 데이터
  const growthRateData = {
    labels: data.pageTypePerformance.map(page => page.displayName),
    datasets: [{
      label: '성장률 (%)',
      data: data.pageTypePerformance.map(page => page.growthRate),
      backgroundColor: data.pageTypePerformance.map(page => 
        page.growthRate > 20 ? '#10B981' : page.growthRate > 10 ? '#F59E0B' : '#EF4444'
      )
    }]
  };

  // 트렌드 차트 데이터
  const trendsData = {
    labels: data.trends.data.map(item => {
      const date = new Date(item.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }),
    datasets: [
      {
        label: '새 게시글',
        data: data.trends.data.map(item => item.posts),
        backgroundColor: '#3B82F6'
      },
      {
        label: '새 댓글',
        data: data.trends.data.map(item => item.comments),
        backgroundColor: '#10B981'
      },
      {
        label: '신규 사용자',
        data: data.trends.data.map(item => item.newUsers),
        backgroundColor: '#F59E0B'
      },
      {
        label: '활성 사용자',
        data: data.trends.data.map(item => item.activeUsers),
        backgroundColor: '#EF4444'
      }
    ]
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <span className="text-2xl mr-2">💡</span>
          비즈니스 인사이트
        </h2>
        <div className="text-sm text-gray-500">
          전환율 및 성장 지표 분석
        </div>
      </div>

      {/* 서비스 성과 지표 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="총 서비스"
          value={data.servicePerformance.totalServices}
          icon="🏢"
          color="blue"
          format="number"
        />
        <MetricCard
          title="총 문의"
          value={data.servicePerformance.totalInquiries}
          icon="📞"
          color="green"
          format="number"
        />
        <MetricCard
          title="총 후기"
          value={data.servicePerformance.totalReviews}
          icon="⭐"
          color="yellow"
          format="number"
        />
        <MetricCard
          title="평균 평점"
          value={data.servicePerformance.avgRating}
          icon="🌟"
          color="purple"
          format="number"
        />
        <MetricCard
          title="전환율"
          value={data.servicePerformance.conversionRate}
          icon="📈"
          color="green"
          format="percentage"
        />
      </div>

      {/* 사용자 여정 분석 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">사용자 여정 분석</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl mb-2">👤</div>
            <div className="text-2xl font-bold text-blue-600">
              {data.userJourney.visitorToSignup.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">방문자 → 가입 전환율</div>
            <div className="text-xs text-gray-500 mt-1">
              방문자 중 회원가입하는 비율
            </div>
          </div>

          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl mb-2">✍️</div>
            <div className="text-2xl font-bold text-green-600">
              {data.userJourney.signupToFirstPost.toFixed(1)}일
            </div>
            <div className="text-sm text-gray-600">가입 → 첫 게시글</div>
            <div className="text-xs text-gray-500 mt-1">
              가입 후 첫 게시글까지 평균 일수
            </div>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-3xl mb-2">💬</div>
            <div className="text-2xl font-bold text-purple-600">
              {data.userJourney.postEngagementRate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">게시글 참여율</div>
            <div className="text-xs text-gray-500 mt-1">
              게시글에 반응(댓글/좋아요)하는 비율
            </div>
          </div>
        </div>
      </div>

      {/* 페이지별 성과 비교 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendChart
          title="페이지별 게시글 & 조회수"
          data={pagePerformanceData}
          type="bar"
          height={300}
        />

        <TrendChart
          title="페이지별 성장률"
          data={growthRateData}
          type="bar"
          height={300}
        />
      </div>

      {/* 페이지별 상세 성과 테이블 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">페이지별 상세 성과</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  페이지 타입
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  게시글 수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  총 조회수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  평균 참여도
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  성장률
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.pageTypePerformance.map((page, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900">{page.displayName}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {page.totalPosts.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {page.totalViews.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {page.avgEngagement.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      page.growthRate > 20 
                        ? 'bg-green-100 text-green-800'
                        : page.growthRate > 10 
                        ? 'bg-yellow-100 text-yellow-800'
                        : page.growthRate > 0
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {page.growthRate > 0 ? '+' : ''}{page.growthRate.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 시간대별 트렌드 */}
      <TrendChart
        title="일별 활동 트렌드"
        data={trendsData}
        type="line"
        height={350}
      />

      {/* 핵심 인사이트 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="text-xl mr-2">🧠</span>
          핵심 인사이트
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">🎯 높은 성과 영역</h4>
            <ul className="space-y-1 text-sm text-gray-700">
              {data.pageTypePerformance
                .filter(page => page.growthRate > 20)
                .map((page, index) => (
                  <li key={index} className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    {page.displayName}: {page.growthRate.toFixed(1)}% 성장
                  </li>
                ))}
              {data.pageTypePerformance.filter(page => page.growthRate > 20).length === 0 && (
                <li className="text-gray-500">현재 20% 이상 성장하는 영역이 없습니다.</li>
              )}
            </ul>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-2">⚠️ 개선 필요 영역</h4>
            <ul className="space-y-1 text-sm text-gray-700">
              {data.pageTypePerformance
                .filter(page => page.growthRate < 10)
                .map((page, index) => (
                  <li key={index} className="flex items-center">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    {page.displayName}: {page.growthRate.toFixed(1)}% 성장 (개선 필요)
                  </li>
                ))}
              {data.pageTypePerformance.filter(page => page.growthRate < 10).length === 0 && (
                <li className="text-gray-500">모든 영역이 양호한 성장세를 보이고 있습니다.</li>
              )}
            </ul>
          </div>
        </div>

        {/* 액션 아이템 */}
        <div className="mt-6 p-4 bg-white rounded-lg border border-indigo-200">
          <h4 className="font-medium text-gray-900 mb-2">📋 추천 액션 아이템</h4>
          <ul className="space-y-1 text-sm text-gray-700">
            <li className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              서비스 전환율 {data.servicePerformance.conversionRate.toFixed(1)}% - 
              {data.servicePerformance.conversionRate > 15 ? ' 우수한 수준입니다' : ' 개선 여지가 있습니다'}
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              첫 게시글까지 평균 {data.userJourney.signupToFirstPost.toFixed(1)}일 - 
              {data.userJourney.signupToFirstPost < 5 ? ' 빠른 참여 유도' : ' 온보딩 프로세스 개선 권장'}
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              게시글 참여율 {data.userJourney.postEngagementRate.toFixed(1)}% - 
              {data.userJourney.postEngagementRate > 40 ? ' 활발한 커뮤니티' : ' 참여 유도 활동 필요'}
            </li>
          </ul>
        </div>
      </div>

      {/* 서비스별 성과 요약 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">서비스 성과 요약</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {((data.servicePerformance.totalInquiries / data.servicePerformance.totalServices) || 0).toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">서비스당 평균 문의</div>
          </div>
          
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {((data.servicePerformance.totalReviews / data.servicePerformance.totalInquiries) * 100 || 0).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">문의 → 후기 전환율</div>
          </div>
          
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {data.servicePerformance.avgRating.toFixed(1)}/5.0
            </div>
            <div className="text-sm text-gray-600">평균 서비스 만족도</div>
          </div>
          
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {(data.servicePerformance.totalReviews / data.servicePerformance.totalServices || 0).toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">서비스당 평균 후기</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BusinessInsights;