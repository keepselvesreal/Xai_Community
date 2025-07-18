import React from 'react';
import type { GA4Analytics as GA4AnalyticsType } from '~/types/analytics';
import { MetricCard } from './MetricCard';
import { TrendChart } from './TrendChart';

interface GA4AnalyticsProps {
  data: GA4AnalyticsType;
  className?: string;
}

export function GA4Analytics({ data, className = '' }: GA4AnalyticsProps) {
  // 시간대별 트래픽 차트 데이터 변환
  const trafficChartData = {
    labels: data.timelineData.map(item => {
      const date = new Date(item.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }),
    datasets: [
      {
        label: '사용자',
        data: data.timelineData.map(item => item.users),
        backgroundColor: '#3B82F6',
        borderColor: '#3B82F6'
      },
      {
        label: '세션',
        data: data.timelineData.map(item => item.sessions),
        backgroundColor: '#10B981',
        borderColor: '#10B981'
      },
      {
        label: '페이지뷰',
        data: data.timelineData.map(item => item.pageViews),
        backgroundColor: '#F59E0B',
        borderColor: '#F59E0B'
      }
    ]
  };

  // 디바이스 타입 차트 데이터
  const deviceChartData = {
    labels: ['데스크톱', '모바일', '태블릿'],
    datasets: [{
      label: '디바이스별 사용자',
      data: [
        data.userSegments.deviceTypes.desktop,
        data.userSegments.deviceTypes.mobile,
        data.userSegments.deviceTypes.tablet
      ],
      backgroundColor: ['#3B82F6', '#10B981', '#F59E0B']
    }]
  };

  // 트래픽 소스 차트 데이터
  const trafficSourceChartData = {
    labels: ['직접 접속', '검색', '추천', '소셜'],
    datasets: [{
      label: '트래픽 소스',
      data: [
        data.userSegments.trafficSources.direct,
        data.userSegments.trafficSources.organic,
        data.userSegments.trafficSources.referral,
        data.userSegments.trafficSources.social
      ],
      backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
    }]
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <span className="text-2xl mr-2">📊</span>
          GA4 사용자 행동 분석
        </h2>
        <div className="text-sm text-gray-500">
          Google Analytics 4 데이터
        </div>
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="총 사용자"
          value={data.totalUsers}
          icon="👥"
          color="blue"
          format="number"
        />
        <MetricCard
          title="신규 사용자"
          value={data.newUsers}
          icon="🆕"
          color="green"
          format="number"
        />
        <MetricCard
          title="세션 수"
          value={data.sessions}
          icon="🔄"
          color="purple"
          format="number"
        />
        <MetricCard
          title="이탈률"
          value={data.bounceRate}
          icon="📤"
          color="red"
          format="percentage"
        />
      </div>

      {/* 시간대별 트래픽 트렌드 */}
      <TrendChart
        title="시간대별 트래픽 트렌드"
        data={trafficChartData}
        type="line"
        height={300}
      />

      {/* 사용자 세그먼트 분석 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 디바이스별 분석 */}
        <TrendChart
          title="디바이스별 사용자"
          data={deviceChartData}
          type="pie"
          height={300}
        />

        {/* 트래픽 소스 분석 */}
        <TrendChart
          title="트래픽 소스"
          data={trafficSourceChartData}
          type="doughnut"
          height={300}
        />
      </div>

      {/* 인기 페이지 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">인기 페이지</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  페이지
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  페이지뷰
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  고유 조회수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  평균 체류시간
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  이탈률
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.topPages.map((page, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{page.title}</div>
                      <div className="text-sm text-gray-500">{page.path}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {page.pageViews.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {page.uniqueViews.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {Math.floor(page.avgTimeOnPage / 60)}:{(page.avgTimeOnPage % 60).toString().padStart(2, '0')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      page.bounceRate < 30 
                        ? 'bg-green-100 text-green-800'
                        : page.bounceRate < 50 
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {page.bounceRate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 커스텀 이벤트 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">커스텀 이벤트</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.customEvents.map((event, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-900">
                  {event.eventName === 'post_create' ? '게시글 작성' :
                   event.eventName === 'post_like' ? '게시글 좋아요' :
                   event.eventName === 'comment_create' ? '댓글 작성' :
                   event.eventName === 'service_inquiry' ? '서비스 문의' :
                   event.eventName}
                </h4>
                <span className="text-xl">
                  {event.eventName === 'post_create' ? '✍️' :
                   event.eventName === 'post_like' ? '👍' :
                   event.eventName === 'comment_create' ? '💬' :
                   event.eventName === 'service_inquiry' ? '📞' :
                   '📊'}
                </span>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-gray-900">
                  {event.eventCount.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">
                  고유 사용자: {event.uniqueUsers.toLocaleString()}명
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 신규 vs 재방문 사용자 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">사용자 유형</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="text-center">
            <div className="text-3xl mb-2">🆕</div>
            <div className="text-2xl font-bold text-green-600">
              {data.userSegments.newVsReturning.newUsers.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">신규 사용자</div>
            <div className="text-xs text-gray-400 mt-1">
              {((data.userSegments.newVsReturning.newUsers / data.totalUsers) * 100).toFixed(1)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🔄</div>
            <div className="text-2xl font-bold text-blue-600">
              {data.userSegments.newVsReturning.returningUsers.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">재방문 사용자</div>
            <div className="text-xs text-gray-400 mt-1">
              {((data.userSegments.newVsReturning.returningUsers / data.totalUsers) * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* GA4 연결 상태 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="text-blue-500 text-xl mr-3">ℹ️</div>
          <div>
            <h4 className="font-medium text-blue-800">GA4 연결 정보</h4>
            <p className="text-blue-600 text-sm mt-1">
              현재 목업 데이터를 표시하고 있습니다. 실제 GA4 데이터 연동을 위해서는 GA4 Reporting API 설정이 필요합니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GA4Analytics;