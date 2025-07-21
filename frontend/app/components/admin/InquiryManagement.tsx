import React, { useState, useEffect } from 'react';
import { apiClient } from '~/lib/api';

interface InquiryItem {
  id: string;
  title: string;
  content: string;
  author_id: string;
  author?: {
    name?: string;
    user_handle: string;
    display_name?: string;
  };
  created_at: string;
  status: string;
  metadata: {
    type: string;
  };
}

interface InquiryResponse {
  items: InquiryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const InquiryManagement: React.FC = () => {
  const [inquiries, setInquiries] = useState<InquiryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [grantingPermission, setGrantingPermission] = useState<string | null>(null);

  // 등록 문의만 필터링하는 함수
  const getInquiryTypeParam = () => {
    if (filter === 'moving-services') return 'moving-services-register-inquiry';
    if (filter === 'expert-tips') return 'expert-tips-register-inquiry';
    return null;
  };

  // 문의 목록 조회
  const fetchInquiries = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
      });

      const inquiryType = getInquiryTypeParam();
      if (inquiryType) {
        params.append('inquiry_type', inquiryType);
      }

      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      console.log('🔍 문의 조회 시작 - params:', params.toString());
      console.log('🔍 필터:', { filter, statusFilter, inquiryType });

      const response = await apiClient.getInquiries(
        page,
        20,
        inquiryType || undefined,
        statusFilter !== 'all' ? statusFilter : undefined
      );
      console.log('🔍 API 응답:', response);

      if (!response.success || !response.data) {
        console.error('❌ API 오류:', response.error);
        throw new Error(`문의 목록 조회 실패: ${response.error}`);
      }

      const data: InquiryResponse = response.data;
      console.log('🔍 API 응답 데이터:', data);
      
      // 등록 문의만 필터링 (클라이언트 사이드에서 추가 필터링)
      const registrationInquiries = data.items.filter(item => 
        item.metadata?.type === 'moving-services-register-inquiry' || 
        item.metadata?.type === 'expert-tips-register-inquiry'
      );

      console.log('🔍 필터링된 등록 문의:', registrationInquiries);
      setInquiries(registrationInquiries);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('❌ 문의 목록 조회 오류:', error);
      setInquiries([]);
    } finally {
      setLoading(false);
    }
  };

  // 권한 부여 함수
  const grantPermission = async (inquiry: InquiryItem) => {
    try {
      setGrantingPermission(inquiry.id);

      // 문의 타입에 따라 부여할 권한 결정
      const isMovingServices = inquiry.metadata?.type === 'moving-services-register-inquiry';
      const permissionData = {
        can_write_moving_services: isMovingServices || undefined,
        can_write_expert_tips: !isMovingServices || undefined,
      };

      // 사용자 권한 부여 API 호출
      const response = await apiClient.updateUserPermissions(inquiry.author_id, permissionData);

      if (!response.success) {
        throw new Error('권한 부여 실패');
      }

      // 문의 상태를 resolved로 변경
      const statusResponse = await apiClient.updateInquiryStatus(inquiry.id, 'resolved');

      if (!statusResponse.success) {
        throw new Error('문의 상태 업데이트 실패');
      }

      // 목록 새로고침
      await fetchInquiries();
      
      alert('권한이 성공적으로 부여되었습니다.');
    } catch (error) {
      console.error('권한 부여 오류:', error);
      alert('권한 부여 중 오류가 발생했습니다.');
    } finally {
      setGrantingPermission(null);
    }
  };

  // 태그 색상 반환
  const getTagColor = (type: string) => {
    switch (type) {
      case 'moving-services-register-inquiry':
        return 'bg-green-100 text-green-800';
      case 'expert-tips-register-inquiry':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 태그 텍스트 반환
  const getTagText = (type: string) => {
    switch (type) {
      case 'moving-services-register-inquiry':
        return '입주 업체 서비스';
      case 'expert-tips-register-inquiry':
        return '전문가 꿀정보';
      default:
        return '기타';
    }
  };

  // 상태 텍스트 반환
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '대기';
      case 'resolved':
        return '승인';
      case 'rejected':
        return '거부';
      default:
        return status;
    }
  };

  // 작성자 표시명 반환 (비로그인: JSON에서 name 추출, 로그인: 사용자 정보)
  const getAuthorDisplayName = (inquiry: InquiryItem) => {
    // 로그인한 사용자인 경우 사용자 정보 표시
    if (inquiry.author && inquiry.author.user_handle && inquiry.author.user_handle !== '익명') {
      return inquiry.author.display_name || inquiry.author.name || inquiry.author.user_handle;
    }
    
    // 비로그인 사용자인 경우 등록 문의 JSON에서 name 필드 추출
    try {
      const contentData = JSON.parse(inquiry.content || '{}');
      return contentData.name || '알 수 없음';
    } catch {
      return '알 수 없음';
    }
  };

  useEffect(() => {
    fetchInquiries();
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
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">등록 문의 관리</h3>
        
        {/* 필터 */}
        <div className="flex gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">문의 유형</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">전체</option>
              <option value="moving-services">입주 업체 서비스</option>
              <option value="expert-tips">전문가 꿀정보</option>
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
              <option value="resolved">승인</option>
              <option value="rejected">거부</option>
            </select>
          </div>
        </div>
      </div>

      {/* 테이블 */}
      {inquiries.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          등록 문의가 없습니다.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-900">유형</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">제목</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">작성자</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">작성일</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">상태</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">액션</th>
              </tr>
            </thead>
            <tbody>
              {inquiries.map((inquiry) => (
                <tr key={inquiry.id} className="border-b border-gray-100 hover:bg-gray-50">
                  {/* 유형 태그 */}
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTagColor(inquiry.metadata?.type)}`}>
                      {getTagText(inquiry.metadata?.type)}
                    </span>
                  </td>
                  
                  {/* 제목 */}
                  <td className="py-3 px-4">
                    <div className="font-medium text-gray-900 truncate max-w-xs">
                      {inquiry.title}
                    </div>
                  </td>
                  
                  {/* 작성자 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-900">
                      {getAuthorDisplayName(inquiry)}
                    </div>
                  </td>
                  
                  {/* 작성일 */}
                  <td className="py-3 px-4">
                    <div className="text-sm text-gray-500">
                      {new Date(inquiry.created_at).toLocaleDateString('ko-KR')}
                    </div>
                  </td>
                  
                  {/* 상태 */}
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      inquiry.status === 'resolved' ? 'bg-green-100 text-green-800' :
                      inquiry.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {getStatusText(inquiry.status)}
                    </span>
                  </td>
                  
                  {/* 액션 버튼 */}
                  <td className="py-3 px-4">
                    {inquiry.status === 'resolved' ? (
                      <span className="text-sm text-green-600 font-medium">승인</span>
                    ) : (
                      <button
                        onClick={() => grantPermission(inquiry)}
                        disabled={grantingPermission === inquiry.id}
                        className={`px-3 py-1 text-sm font-medium rounded-md ${
                          grantingPermission === inquiry.id
                            ? 'bg-gray-400 text-white cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        } transition-colors`}
                      >
                        {grantingPermission === inquiry.id ? '처리중...' : '권한 부여'}
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

export default InquiryManagement;