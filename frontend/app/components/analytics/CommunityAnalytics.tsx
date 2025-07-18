import React from 'react';
import type { CommunityAnalytics as CommunityAnalyticsType } from '~/types/analytics';
import { MetricCard } from './MetricCard';
import { TrendChart } from './TrendChart';

interface CommunityAnalyticsProps {
  data: CommunityAnalyticsType;
  className?: string;
}

export function CommunityAnalytics({ data, className = '' }: CommunityAnalyticsProps) {
  // 카테고리별 게시글 차트 데이터
  const postsByCategoryData = {
    labels: data.postAnalytics.postsByCategory.map(item => {
      switch (item.category) {
        case 'board': return '게시판';
        case 'property_information': return '부동산 정보';
        case 'moving_services': return '입주 업체 서비스';
        case 'expert_tips': return '전문가 꿀정보';
        default: return item.category;
      }
    }),
    datasets: [{
      label: '게시글 수',
      data: data.postAnalytics.postsByCategory.map(item => item.count),
      backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
    }]
  };

  // 시간대별 게시글 작성 패턴 차트 데이터
  const postsByTimeData = {
    labels: data.postAnalytics.postsByTime.map(item => `${item.hour}:00`),
    datasets: [{
      label: '게시글 수',
      data: data.postAnalytics.postsByTime.map(item => item.count),
      backgroundColor: '#3B82F6'
    }]
  };

  // 요일별 게시글 작성 패턴 차트 데이터
  const postsByDayData = {
    labels: data.postAnalytics.postsByDayOfWeek.map(item => item.dayOfWeek),
    datasets: [{
      label: '게시글 수',
      data: data.postAnalytics.postsByDayOfWeek.map(item => item.count),
      backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899']
    }]
  };

  // 사용자 참여도 통계
  const engagementStats = data.engagementAnalytics.reactionStats;
  const totalReactions = engagementStats.totalLikes + engagementStats.totalDislikes + engagementStats.totalBookmarks;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <span className="text-2xl mr-2">👥</span>
          커뮤니티 활동 분석
        </h2>
        <div className="text-sm text-gray-500">
          사용자 참여도 및 콘텐츠 성과
        </div>
      </div>

      {/* 전체 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="총 게시글"
          value={data.totalStats.totalPosts}
          icon="📝"
          color="blue"
          format="number"
        />
        <MetricCard
          title="총 댓글"
          value={data.totalStats.totalComments}
          icon="💬"
          color="green"
          format="number"
        />
        <MetricCard
          title="전체 사용자"
          value={data.totalStats.totalUsers}
          icon="👤"
          color="purple"
          format="number"
        />
        <MetricCard
          title="활성 사용자"
          value={data.totalStats.activeUsers}
          icon="⚡"
          color="yellow"
          format="number"
        />
      </div>

      {/* 게시글 분석 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 카테고리별 게시글 */}
        <TrendChart
          title="카테고리별 게시글"
          data={postsByCategoryData}
          type="pie"
          height={300}
        />

        {/* 요일별 작성 패턴 */}
        <TrendChart
          title="요일별 게시글 작성"
          data={postsByDayData}
          type="bar"
          height={300}
        />
      </div>

      {/* 시간대별 작성 패턴 */}
      <TrendChart
        title="시간대별 게시글 작성 패턴"
        data={postsByTimeData}
        type="bar"
        height={300}
      />

      {/* 사용자 참여도 분석 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">사용자 참여도</h3>
        
        {/* 반응 통계 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <div className="text-3xl mb-2">👍</div>
            <div className="text-2xl font-bold text-green-600">
              {engagementStats.totalLikes.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">좋아요</div>
            <div className="text-xs text-gray-400 mt-1">
              {totalReactions > 0 ? ((engagementStats.totalLikes / totalReactions) * 100).toFixed(1) : 0}%
            </div>
          </div>
          
          <div className="bg-red-50 rounded-lg p-4 text-center">
            <div className="text-3xl mb-2">👎</div>
            <div className="text-2xl font-bold text-red-600">
              {engagementStats.totalDislikes.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">싫어요</div>
            <div className="text-xs text-gray-400 mt-1">
              {totalReactions > 0 ? ((engagementStats.totalDislikes / totalReactions) * 100).toFixed(1) : 0}%
            </div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <div className="text-3xl mb-2">📌</div>
            <div className="text-2xl font-bold text-blue-600">
              {engagementStats.totalBookmarks.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">북마크</div>
            <div className="text-xs text-gray-400 mt-1">
              {totalReactions > 0 ? ((engagementStats.totalBookmarks / totalReactions) * 100).toFixed(1) : 0}%
            </div>
          </div>
        </div>

        {/* 댓글 통계 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">댓글 활동</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">총 댓글 수</span>
                <span className="font-semibold">{data.engagementAnalytics.commentStats.totalComments.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">게시글당 평균 댓글</span>
                <span className="font-semibold">{data.engagementAnalytics.commentStats.avgCommentsPerPost.toFixed(1)}개</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-3">사용자 리텐션</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">일일 활성 사용자</span>
                <span className="font-semibold">{data.engagementAnalytics.userRetention.dailyActiveUsers.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">주간 활성 사용자</span>
                <span className="font-semibold">{data.engagementAnalytics.userRetention.weeklyActiveUsers.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">월간 활성 사용자</span>
                <span className="font-semibold">{data.engagementAnalytics.userRetention.monthlyActiveUsers.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 활발한 댓글러 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">활발한 댓글러 TOP 3</h3>
        <div className="space-y-3">
          {data.engagementAnalytics.commentStats.topCommenters.map((commenter, index) => (
            <div key={commenter.userId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold mr-3 ${
                  index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : 'bg-orange-500'
                }`}>
                  {index + 1}
                </div>
                <div>
                  <div className="font-medium text-gray-900">{commenter.userName}</div>
                  <div className="text-sm text-gray-500">사용자 ID: {commenter.userId}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-lg">{commenter.commentCount.toLocaleString()}</div>
                <div className="text-sm text-gray-500">댓글</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 인기 게시글 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">인기 게시글</h3>
        <div className="space-y-4">
          {data.postAnalytics.topPosts.map((post, index) => (
            <div key={post.id} className="border-l-4 border-blue-500 pl-4 py-2">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-1">{post.title}</h4>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className="inline-flex items-center">
                      <span className="text-blue-500 mr-1">📁</span>
                      {post.category === 'board' ? '게시판' :
                       post.category === 'property_information' ? '부동산 정보' :
                       post.category === 'moving_services' ? '입주 업체 서비스' :
                       post.category === 'expert_tips' ? '전문가 꿀정보' :
                       post.category}
                    </span>
                    <span className="inline-flex items-center">
                      <span className="text-gray-400 mr-1">👁</span>
                      {post.viewCount.toLocaleString()}
                    </span>
                    <span className="inline-flex items-center">
                      <span className="text-green-500 mr-1">👍</span>
                      {post.likeCount}
                    </span>
                    <span className="inline-flex items-center">
                      <span className="text-blue-500 mr-1">💬</span>
                      {post.commentCount}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-400 ml-4">
                  {new Date(post.createdAt).toLocaleDateString('ko-KR')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 카테고리별 상세 통계 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">카테고리별 상세 통계</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  카테고리
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  게시글 수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  비율
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.postAnalytics.postsByCategory.map((category, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {category.category === 'board' ? '게시판' :
                       category.category === 'property_information' ? '부동산 정보' :
                       category.category === 'moving_services' ? '입주 업체 서비스' :
                       category.category === 'expert_tips' ? '전문가 꿀정보' :
                       category.category}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {category.count.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full" 
                          style={{ width: `${category.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-900">{category.percentage}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      category.percentage > 30 
                        ? 'bg-green-100 text-green-800'
                        : category.percentage > 20 
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {category.percentage > 30 ? '매우 활발' : category.percentage > 20 ? '활발' : '보통'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default CommunityAnalytics;