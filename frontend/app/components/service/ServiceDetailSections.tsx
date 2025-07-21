import React from 'react';
import { useNotification } from '~/contexts/NotificationContext';
import CommentSection from '~/components/comment/CommentSection';
import type { Service } from '~/types/service-types';
import type { Comment } from '~/types';

interface ServiceSectionProps {
  service: Service;
}

interface ServiceActionsSectionProps extends ServiceSectionProps {
  isLiked: boolean;
  onLike: () => void;
  onInquiry: () => void;
}

// 숫자 포맷팅 유틸리티
const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

// 별점 렌더링 유틸리티
const renderStars = (rating: number): React.ReactElement[] => {
  return Array.from({ length: 5 }, (_, i) => {
    const starNumber = i + 1;
    // 소수점이 있으면 올림 처리 (3.5 → 4개 별 표시)
    const isActive = starNumber <= Math.ceil(rating);
    return (
      <span 
        key={i} 
        className={`text-lg ${isActive ? "text-yellow-400" : "text-gray-300"}`}
      >
        ★
      </span>
    );
  });
};

/**
 * 서비스 메타 정보 (평점을 제목에 표시)
 * 평점 정보를 제목 옆에 표시하도록 반환
 */
export const ServiceMetaSection: React.FC<ServiceSectionProps> = ({ service }) => {
  return (
    <span className="flex items-center gap-1 ml-2">
      {renderStars(service.rating || 0)}
      <span className="text-gray-700 font-medium ml-1">
        {service.rating || 0}
      </span>
    </span>
  );
};

/**
 * 서비스 소개 섹션 (참조 디자인 스타일 - 글 안의 섹션으로 통합)
 * company.description 내용만 표시, mock 데이터 완전 제거
 */
export const ServiceIntroSection: React.FC<ServiceSectionProps> = ({ service }) => {
  // company.description 내용만 사용
  const companyDescription = service.company?.description || "";
  
  // company.description이 있을 때만 섹션 표시
  if (!companyDescription) {
    return null;
  }

  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        🏢 업체 소개 및 서비스
      </h2>
      
      {/* 업체 소개 - company.description만 표시 */}
      <div className="text-gray-700 leading-relaxed">
        <p className="whitespace-pre-wrap">{companyDescription}</p>
      </div>
    </div>
  );
};

/**
 * 서비스 가격 섹션 (참조 디자인 스타일 - 글 안의 섹션으로 통합)
 */
export const ServicePriceSection: React.FC<ServiceSectionProps> = ({ service }) => {
  const services = service.services || [];

  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        💰 서비스 및 가격
      </h2>
      
      <div className="space-y-3">
        {services.map((serviceItem, index) => (
          <div 
            key={index} 
            className="flex justify-between items-start p-4 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 mb-1">
                {serviceItem.name}
              </h4>
              {serviceItem.description && (
                <p className="text-gray-600 text-sm">
                  {serviceItem.description}
                </p>
              )}
            </div>
            <div className="text-right ml-4">
              {serviceItem.specialPrice && (
                <div className="text-gray-400 line-through text-sm mb-1">
                  {formatNumber(parseInt(serviceItem.price))}원
                </div>
              )}
              <div className={`font-bold text-lg ${
                serviceItem.specialPrice ? 'text-red-500' : 'text-gray-900'
              }`}>
                {formatNumber(
                  parseInt(serviceItem.specialPrice || serviceItem.price)
                )}원
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
        <p className="text-sm text-yellow-800 flex items-center gap-2">
          <span>💡</span>
          <span>정확한 견적은 현장 상담 후 제공됩니다.</span>
        </p>
      </div>
    </div>
  );
};

/**
 * 서비스 연락처 섹션 (참조 디자인 스타일 - 글 안의 섹션으로 통합)
 */
export const ServiceContactSection: React.FC<ServiceSectionProps> = ({ service }) => {
  const contact = service.contact;

  return (
    <div className="mb-6 border-t border-gray-200 pt-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        📞 연락처 정보
      </h2>
      
      {/* 연락처 정보 통합 카드 - 참조 디자인과 동일 */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
        <div className="space-y-4">
          {/* 회사 위치 */}
          {contact.address && (
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-red-500 rounded-full">
                <span className="text-white text-lg">📍</span>
              </div>
              <div className="flex-1">
                <div className="font-semibold text-gray-900 mb-1">회사 위치</div>
                <div className="text-red-600 text-sm font-semibold">{contact.address}</div>
              </div>
            </div>
          )}
          
          {contact.address && <div className="h-px bg-gray-200 mx-2"></div>}
          
          {/* 회사 웹사이트 */}
          {contact.website && (
            <>
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 bg-blue-500 rounded-full">
                  <span className="text-white text-lg">🌐</span>
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 mb-1">회사 웹사이트</div>
                  <a 
                    href={contact.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 text-sm underline"
                  >
                    {contact.website}
                  </a>
                </div>
              </div>
              <div className="h-px bg-gray-200 mx-2"></div>
            </>
          )}
          
          {/* 전화번호 */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-green-500 rounded-full">
              <span className="text-white text-lg">📞</span>
            </div>
            <div className="flex-1">
              <div className="font-semibold text-gray-900 mb-1">전화 문의</div>
              <a 
                href={`tel:${contact.phone}`}
                className="text-green-600 text-base font-bold"
              >
                {contact.phone}
              </a>
            </div>
          </div>
          
          {contact.email && <div className="h-px bg-gray-200 mx-2"></div>}
          
          {/* 이메일 */}
          {contact.email && (
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-purple-500 rounded-full">
                <span className="text-white text-lg">📧</span>
              </div>
              <div className="flex-1">
                <div className="font-semibold text-gray-900 mb-1">이메일 문의</div>
                <a 
                  href={`mailto:${contact.email}`}
                  className="text-purple-600 text-base font-bold"
                >
                  {contact.email}
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* 운영 시간 */}
      <div className="text-center mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-lg font-semibold text-yellow-800">
          업무 시간: {contact.hours}
        </div>
      </div>
    </div>
  );
};

/**
 * 서비스 문의 섹션 (참조 디자인 기반)
 * subtype: 'service_inquiry'를 사용한 댓글 시스템
 */
export const ServiceInquirySection: React.FC<{
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
  onCommentReaction?: () => void;
}> = ({ postSlug, comments, onCommentAdded, onCommentReaction }) => {
  // 문의 댓글만 필터링 (subtype이 service_inquiry인 것들)
  const inquiryComments = comments.filter(
    comment => comment.metadata?.subtype === 'service_inquiry'
  );

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* 문의 섹션 - HTML 프로토타입 스타일 */}
        <div className="p-6">
          <div className="text-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center justify-center gap-2">
              <span>💬</span>
              <span>문의 ({inquiryComments.length}개)</span>
            </h3>
          </div>
          
          <CommentSection
            postSlug={postSlug}
            comments={inquiryComments}
            onCommentAdded={onCommentAdded}
            onCommentReaction={onCommentReaction}
            pageType="moving_services"
            subtype="service_inquiry"
          />
        </div>
      </div>
    </div>
  );
};

/**
 * 서비스 후기 섹션 (참조 디자인 기반)
 * subtype: 'service_review'를 사용한 댓글 시스템
 */
export const ServiceReviewSection: React.FC<{
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
  onCommentReaction?: () => void;
  averageRating?: number;
}> = ({ postSlug, comments, onCommentAdded, onCommentReaction, averageRating = 0 }) => {
  // 후기 댓글만 필터링 (subtype이 service_review인 것들)
  const reviewComments = comments.filter(
    comment => comment.metadata?.subtype === 'service_review'
  );

  // 실제 후기 댓글들의 평균 별점 계산
  const calculateAverageRating = () => {
    const ratingsFromComments = reviewComments
      .filter(comment => comment.metadata?.rating)
      .map(comment => Number(comment.metadata.rating));
    
    if (ratingsFromComments.length === 0) return 0;
    
    const sum = ratingsFromComments.reduce((acc, rating) => acc + rating, 0);
    return Math.round((sum / ratingsFromComments.length) * 10) / 10; // 소수점 1자리까지
  };

  const actualAverageRating = calculateAverageRating();
  
  // 실시간 별점 업데이트 로그
  console.log('🌟 ServiceReviewSection 별점 상태:', {
    reviewCommentsCount: reviewComments.length,
    calculatedRating: actualAverageRating,
    serviceAverageRating: averageRating,
    ratingsFromComments: reviewComments.map(c => c.metadata?.rating)
  });

  // 별점 렌더링 (로컬 함수)
  const renderReviewStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => {
      const starNumber = i + 1;
      // 소수점이 있으면 올림 처리 (3.5 → 4개 별 표시)
      const isActive = starNumber <= Math.ceil(rating);
      return (
        <span 
          key={i} 
          className={`text-lg ${isActive ? "text-yellow-400" : "text-gray-300"}`}
        >
          ★
        </span>
      );
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* 후기 섹션 - HTML 프로토타입 스타일 */}
        <div className="p-6">
          <div className="text-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center justify-center gap-2">
              <span>🌟</span>
              <span>후기 ({reviewComments.length}개)</span>
            </h3>
          </div>
          
          {/* 평점 요약 - 숫자만 표시 */}
          {actualAverageRating > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
              <div className="flex items-center justify-center gap-2">
                <span className="text-sm text-gray-600">평점:</span>
                <span className="text-gray-900 font-semibold text-lg">{actualAverageRating}점</span>
              </div>
            </div>
          )}
          
          <CommentSection
            postSlug={postSlug}
            comments={reviewComments}
            onCommentAdded={onCommentAdded}
            onCommentReaction={onCommentReaction}
            pageType="moving_services"
            subtype="service_review"
          />
        </div>
      </div>
    </div>
  );
};

/**
 * 고정 북마크 버튼
 * 화면 우측에 고정되어 표시되는 북마크 버튼
 */
export const FixedBookmarkButton: React.FC<{
  isBookmarked: boolean;
  onToggle: () => void;
}> = ({ isBookmarked, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      aria-label={isBookmarked ? '북마크 해제' : '북마크 추가'}
      className={`fixed top-1/2 right-5 transform -translate-y-1/2 z-50 p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110 ${
        isBookmarked
          ? 'bg-blue-100 border-2 border-blue-300 text-blue-700'
          : 'bg-white border-2 border-gray-200 text-gray-600 hover:bg-gray-50'
      }`}
      style={{ fontSize: '24px' }}
    >
      <span>🔖</span>
    </button>
  );
};

// 모든 섹션을 포함하는 유틸리티 함수 (참조 디자인 적용 - company.description만 표시)
export const createServiceDetailSections = (
  service: Service,
  isLiked: boolean,
  onLike: () => void,
  onInquiry: () => void,
  // 문의/후기 섹션을 위한 추가 props
  postSlug?: string,
  comments?: Comment[],
  onCommentAdded?: () => void,
  onCommentReaction?: () => void,
  // 신고 기능을 위한 추가 props
  onReportClick?: () => void
) => {
  return {
    beforeContent: [
      <ServiceIntroSection key="intro" service={service} />,
      <ServicePriceSection key="price" service={service} />,
      <ServiceContactSection key="contact" service={service} />,
    ],
    afterContent: [],
    afterReactions: onReportClick ? [
      <div key="report-button" className="flex justify-end mt-2">
        <button
          onClick={onReportClick}
          className="text-gray-500 hover:text-red-600 text-sm transition-colors"
        >
          신고
        </button>
      </div>
    ] : [],
    serviceMeta: <ServiceMetaSection key="meta" service={service} />,
    // 문의와 후기 섹션을 별도 컨테이너로 반환 (참조 디자인과 동일)
    customSections: postSlug && comments && onCommentAdded ? [
      <ServiceInquirySection 
        key="inquiry"
        postSlug={postSlug}
        comments={comments}
        onCommentAdded={onCommentAdded}
        onCommentReaction={onCommentReaction}
      />,
      <ServiceReviewSection 
        key="review"
        postSlug={postSlug}
        comments={comments}
        onCommentAdded={onCommentAdded}
        onCommentReaction={onCommentReaction}
        averageRating={service.rating}
      />
    ] : undefined,
  };
};