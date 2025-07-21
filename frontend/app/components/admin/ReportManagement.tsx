import React, { useState, useEffect } from 'react';
import { apiClient } from '~/lib/api';

interface ReportItem {
  id: string;
  target_type: string;
  target_id: string;
  content: string;
  reporter_id: string;
  created_at: string;
  status: string;
  author?: {
    id?: string;
    name?: string;
    user_handle: string;
    display_name?: string;
    email?: string;
  };
}

interface ReportResponse {
  items: ReportItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const ReportManagement: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [processingReport, setProcessingReport] = useState<string | null>(null);

  // 신고 목록 조회
  const fetchReports = async () => {
    setLoading(true);
    try {
      let targetType: string | undefined;
      if (filter === 'post') targetType = 'post';
      else if (filter === 'comment') targetType = 'comment';

      console.log('🔍 신고 조회 시작 - 필터:', { filter, statusFilter, targetType });

      const response = await apiClient.getReports(
        page,
        20,
        statusFilter !== 'all' ? statusFilter : undefined,
        targetType
      );

      console.log('🔍 API 응답:', response);

      if (!response.success || !response.data) {
        console.error('❌ API 오류:', response.error);
        throw new Error(`신고 목록 조회 실패: ${response.error}`);
      }

      const data: ReportResponse = response.data;
      console.log('🔍 API 응답 데이터:', data);
      console.log('🔍 첫 번째 신고 상세:', data.items[0]);

      setReports(data.items);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('❌ 신고 목록 조회 오류:', error);
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  // 신고 상태 업데이트
  const confirmReport = async (reportId: string) => {
    setProcessingReport(reportId);
    try {
      const response = await apiClient.updateReportStatus(reportId, 'resolved');

      if (!response.success) {
        throw new Error('신고 확인 처리 실패');
      }

      // 목록 새로고침
      await fetchReports();
    } catch (error) {
      console.error('❌ 신고 확인 처리 오류:', error);
    } finally {
      setProcessingReport(null);
    }
  };

  // 타입별 색상 및 텍스트
  const getTagColor = (type: string) => {
    switch (type) {
      case 'post':
        return 'bg-blue-100 text-blue-800';
      case 'comment':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTagText = (type: string) => {
    switch (type) {
      case 'post':
        return '게시글';
      case 'comment':
        return '댓글';
      default:
        return '기타';
    }
  };

  // 상태 텍스트 반환
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
      case 'published':
        return '대기';
      case 'resolved':
        return '확인';
      default:
        return status;
    }
  };

  // 상태별 색상 반환
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
      case 'published':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 신고자 표시명 반환 (등록 문의 관리 참고)
  const getReporterDisplayName = (report: ReportItem) => {
    // reporter_id로 로그인/비로그인 사용자 구분
    const isGuestUser = report.reporter_id.startsWith('guest_report_');
    
    if (!isGuestUser) {
      // 로그인한 사용자: author 정보에서 사용자명 추출
      if (report.author) {
        const displayName = report.author.user_handle || report.author.display_name || report.author.name || '사용자';
        return displayName;
      } else {
        // author 정보가 없는 경우 (백엔드 조인 실패)
        return report.reporter_id; // 임시로 reporter_id 표시
      }
    } else {
      // 비로그인 사용자: '익명' 표시
      return '익명';
    }
  };

  useEffect(() => {
    fetchReports();
  }, [page, filter, statusFilter]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* 필터 */}
        <div className="flex gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">타입</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">전체</option>
              <option value="post">게시글</option>
              <option value="comment">댓글</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">전체</option>
              <option value="pending">대기</option>
              <option value="resolved">확인</option>
            </select>
          </div>
        </div>

      {/* 테이블 */}
      {reports.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          신고가 없습니다.
        </div>
      ) : (
        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">타입</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신고 내용</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신고자</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신고일</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">액션</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  {/* 타입 */}
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTagColor(report.target_type)}`}>
                      {getTagText(report.target_type)}
                    </span>
                  </td>
                  
                  {/* 신고 내용 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-900 max-w-xs truncate">
                      {report.content}
                    </div>
                  </td>
                  
                  {/* 신고자 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-900">
                      {getReporterDisplayName(report)}
                    </div>
                  </td>
                  
                  {/* 신고일 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-500">
                      {new Date(report.created_at).toLocaleDateString('ko-KR')}
                    </div>
                  </td>
                  
                  {/* 상태 */}
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                      {getStatusText(report.status)}
                    </span>
                  </td>
                  
                  {/* 액션 버튼 */}
                  <td className="py-3 px-4">
                    {report.status === 'resolved' ? (
                      <span className="text-sm text-green-600 font-medium">확인완료</span>
                    ) : (
                      <button
                        onClick={() => confirmReport(report.id)}
                        disabled={processingReport === report.id}
                        className={`px-3 py-1 text-sm font-medium rounded-md ${
                          processingReport === report.id
                            ? 'bg-gray-400 text-white cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                      >
                        {processingReport === report.id ? '처리 중...' : '확인'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                총 {reports.length}개의 신고
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm font-medium bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  이전
                </button>
                <span className="px-3 py-1 text-sm font-medium">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm font-medium bg-white border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportManagement;