import React, { useState, useEffect } from 'react';
import { apiClient } from '~/lib/api';

interface SuggestionItem {
  id: string;
  title: string;
  content: string;
  author_id: string;
  author?: {
    id?: string;
    name?: string;
    user_handle: string;
    display_name?: string;
    email?: string;
  };
  created_at: string;
  status: string;
  metadata: {
    type: string;
  };
}

interface SuggestionResponse {
  items: SuggestionItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const SuggestionManagement: React.FC = () => {
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  // 건의 목록 조회
  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      
      console.log('🔍 건의 조회 시작');
      console.log('🔍 필터:', { page, statusFilter });

      // 건의사항만 서버에서 필터링해서 가져오기
      const response = await apiClient.getInquiries(
        page,
        10,
        'suggestions',
        statusFilter !== 'all' ? statusFilter : undefined
      );
      
      console.log('🔍 API 응답:', response);

      if (!response.success || !response.data) {
        console.error('❌ API 오류:', response.error);
        throw new Error(`건의 목록 조회 실패: ${response.error}`);
      }

      const data: SuggestionResponse = response.data;
      console.log('🔍 API 응답 데이터:', data);
      
      // 서버에서 이미 필터링된 데이터를 그대로 사용
      console.log('🔍 건의 목록:', data.items);
      setSuggestions(data.items);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('❌ 건의 목록 조회 오류:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  // 상태 변경 처리
  const handleStatusChange = async (suggestion: SuggestionItem, newStatus: string) => {
    try {
      setProcessingIds(prev => new Set(prev).add(suggestion.id));

      const response = await apiClient.updateInquiryStatus(suggestion.id, newStatus);

      if (!response.success) {
        throw new Error('상태 변경 실패');
      }

      // 목록 새로고침
      await fetchSuggestions();
    } catch (error) {
      console.error('상태 변경 오류:', error);
      alert('상태 변경 중 오류가 발생했습니다.');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestion.id);
        return newSet;
      });
    }
  };

  // 상태 텍스트 반환
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '대기';
      case 'resolved':
        return '완료';
      case 'rejected':
        return '반려';
      case 'published':
        return '대기';
      default:
        return status;
    }
  };

  // 상태 색상 반환
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
      case 'published':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 건의자 표시명 반환
  const getAuthorDisplayName = (suggestion: SuggestionItem) => {
    // 로그인/비로그인 사용자 구분
    const isGuestUser = suggestion.author_id.startsWith('guest_inquiry_');
    
    if (!isGuestUser) {
      // 로그인한 사용자
      if (suggestion.author) {
        return suggestion.author.user_handle || suggestion.author.display_name || suggestion.author.name || '사용자';
      } else {
        return suggestion.author_id;
      }
    } else {
      // 비로그인 사용자
      try {
        const contentData = JSON.parse(suggestion.content || '{}');
        return contentData.name || '익명 사용자';
      } catch {
        return '익명 사용자';
      }
    }
  };

  // 실제 내용 반환
  const getActualContent = (suggestion: SuggestionItem) => {
    // 건의는 content 필드를 직접 사용
    return suggestion.content;
  };

  useEffect(() => {
    fetchSuggestions();
  }, [page, statusFilter]);

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
      <div className="mb-6">
        {/* 필터 */}
        <div className="flex gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">전체</option>
              <option value="pending">대기</option>
              <option value="resolved">완료</option>
            </select>
          </div>
        </div>
      </div>

      {/* 테이블 */}
      {suggestions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          건의 사항이 없습니다.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-900">건의 내용</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">건의자</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">작성일</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">상태</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">액션</th>
              </tr>
            </thead>
            <tbody>
              {suggestions.map((suggestion) => (
                <tr key={suggestion.id} className="border-b border-gray-100 hover:bg-gray-50">
                  {/* 건의 내용 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-900 max-w-md">
                      <div className="line-clamp-2">
                        {getActualContent(suggestion)}
                      </div>
                    </div>
                  </td>
                  
                  {/* 건의자 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-900">
                      {getAuthorDisplayName(suggestion)}
                    </div>
                  </td>
                  
                  {/* 작성일 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-500">
                      {new Date(suggestion.created_at).toLocaleDateString('ko-KR')}
                    </div>
                  </td>
                  
                  {/* 상태 */}
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      getStatusColor(suggestion.status)
                    }`}>
                      {getStatusText(suggestion.status)}
                    </span>
                  </td>
                  
                  {/* 액션 버튼 */}
                  <td className="py-3 px-4">
                    {suggestion.status === 'resolved' ? (
                      <span className="text-sm text-green-600 font-medium">완료</span>
                    ) : (
                      <button
                        onClick={() => handleStatusChange(suggestion, 'resolved')}
                        disabled={processingIds.has(suggestion.id)}
                        className={`px-3 py-1 text-sm font-medium rounded-md ${
                          processingIds.has(suggestion.id)
                            ? 'bg-gray-400 text-white cursor-not-allowed'
                            : 'bg-green-600 text-white hover:bg-green-700'
                        } transition-colors`}
                      >
                        {processingIds.has(suggestion.id) ? '처리중...' : '완료'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-6">
          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page <= 1}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              이전
            </button>
            <span className="px-3 py-2 text-sm text-gray-500">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuggestionManagement;