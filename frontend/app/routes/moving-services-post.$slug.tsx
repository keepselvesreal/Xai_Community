import { useState, useEffect } from "react";
import { type MetaFunction } from "@remix-run/node";
import { useParams, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import { convertPostToService } from "~/types/service-types";
import type { Service } from "~/types/service-types";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "서비스 상세 정보" },
  ];
};


export default function ServiceDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  
  const [service, setService] = useState<Service | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [reviewText, setReviewText] = useState("");
  const [isLiked, setIsLiked] = useState(false);

  const loadService = async () => {
    if (!slug) return;
    
    console.log('🔍 Loading service with slug:', slug);
    setIsLoading(true);
    
    try {
      // 게시판과 동일하게 slug로 API 호출
      const response = await apiClient.getPost(slug);
      console.log('📡 API response:', response);
      
      if (response.success && response.data) {
        console.log('📦 Raw post data:', response.data);
        
        // Post 데이터를 Service로 변환
        const serviceData = convertPostToService(response.data);
        if (serviceData) {
          console.log('✅ Service conversion successful:', serviceData.name);
          setService(serviceData);
        } else {
          console.error('❌ Service conversion failed');
          setIsNotFound(true);
          showError('서비스 데이터 변환에 실패했습니다');
        }
      } else {
        console.error('❌ API call failed');
        setIsNotFound(true);
        showError('서비스를 찾을 수 없습니다');
      }
    } catch (error) {
      console.error('🚨 Error loading service:', error);
      setIsNotFound(true);
      showError('서비스를 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadService();
  }, [slug]);

  // 로딩 상태
  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4">⏳</div>
            <p className="text-var-secondary">서비스 정보를 불러오는 중...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  // 404 상태
  if (isNotFound || !service) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4">❌</div>
            <h3 className="text-xl font-semibold text-red-600 mb-2">서비스를 찾을 수 없습니다</h3>
            <p className="text-var-secondary mb-4">요청하신 서비스가 존재하지 않거나 삭제되었을 수 있습니다.</p>
            <button
              onClick={() => navigate('/services')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              서비스 목록으로 돌아가기
            </button>
          </div>
        </div>
      </AppLayout>
    );
  }

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  const handleBackClick = () => {
    navigate('/services');
  };

  const handleInquiry = () => {
    window.open(`tel:${service.contact.phone}`);
  };

  const handleLike = () => {
    setIsLiked(!isLiked);
  };

  const handleReviewSubmit = () => {
    if (reviewText.trim()) {
      // 리뷰 제출 로직 (실제로는 API 호출)
      alert('후기가 등록되었습니다!');
      setReviewText('');
    }
  };

  return (
    <AppLayout 
      title="서비스 상세" 
      subtitle="업체 정보 및 서비스 안내"
      user={user}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex items-center justify-between mb-6">
          <button 
            onClick={handleBackClick}
            className="flex items-center gap-2 text-var-muted hover:text-var-primary transition-colors"
          >
            ← 목록으로
          </button>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => window.open(`mailto:${service.contact.email}`)}
              className="px-4 py-2 border border-var-color rounded-lg text-var-secondary hover:border-accent-primary hover:text-accent-primary transition-colors"
            >
              문의하기
            </button>
            <button 
              onClick={handleLike}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isLiked 
                  ? 'bg-red-500 text-white' 
                  : 'bg-var-card border border-var-color text-var-secondary hover:bg-red-50 hover:text-red-500'
              }`}
            >
              찜하기 ❤️
            </button>
          </div>
        </div>

        {/* 서비스 헤더 */}
        <div className="bg-green-100 rounded-2xl p-8 mb-8">
          <div className="text-center text-white">
            <h1 className="text-3xl font-bold mb-2 text-green-800">{service.name}</h1>
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="text-green-700">{service.category} •</span>
              <div className="flex items-center gap-1">
                {renderStars(service.rating)}
                <span className="text-green-700">{service.rating}</span>
              </div>
            </div>
            <p className="text-green-700 max-w-2xl mx-auto">{service.description}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 왼쪽 컬럼 - 서비스 및 가격 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 서비스 및 가격 */}
            <div className="bg-var-card rounded-2xl p-6 border border-var-color">
              <h2 className="text-xl font-bold text-var-primary mb-4 flex items-center gap-2">
                🔧 서비스 및 가격
              </h2>
              <div className="space-y-4">
                {service.services.map((item: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-start p-4 bg-var-section rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium text-var-primary mb-1">{item.name}</h3>
                      <p className="text-var-secondary text-sm">{item.description}</p>
                    </div>
                    <div className="text-right ml-4">
                      {item.specialPrice && (
                        <div className="text-gray-400 line-through text-sm">{item.price.toLocaleString()}원</div>
                      )}
                      <div className="text-red-500 font-bold text-lg">
                        {item.specialPrice ? item.specialPrice.toLocaleString() : item.price.toLocaleString()}원
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 후기 섹션 */}
            <div className="bg-var-card rounded-2xl p-6 border border-var-color">
              <h2 className="text-xl font-bold text-var-primary mb-4">후기 {service.reviews.length}개</h2>
              
              {/* 평점 표시 */}
              <div className="mb-6 p-4 bg-var-section rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm text-var-muted">평점:</span>
                  <div className="flex items-center gap-1">
                    {renderStars(service.rating)}
                  </div>
                </div>
              </div>

              {/* 기존 후기 목록 */}
              <div className="space-y-4 mb-6">
                {service.reviews.map((review: any, idx: number) => (
                  <div key={idx} className="border-b border-var-light last:border-b-0 pb-4 last:pb-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-var-primary">{review.author}</span>
                      <div className="flex items-center gap-1">
                        {renderStars(review.rating)}
                      </div>
                    </div>
                    <p className="text-var-secondary">{review.text}</p>
                  </div>
                ))}
              </div>

              {/* 후기 작성 */}
              <div className="border-t border-var-light pt-6">
                <h3 className="font-medium text-var-primary mb-3">후기 작성</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-var-muted">평점:</span>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: 5 }, (_, i) => (
                        <button key={i} className="text-yellow-400 hover:text-yellow-500">
                          ⭐
                        </button>
                      ))}
                    </div>
                  </div>
                  <textarea
                    value={reviewText}
                    onChange={(e) => setReviewText(e.target.value)}
                    placeholder="후기를 작성해주세요..."
                    className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                    rows={4}
                  />
                  <button 
                    onClick={handleReviewSubmit}
                    className="bg-green-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-green-700 transition-colors"
                  >
                    후기 작성
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 오른쪽 컬럼 - 연락처 정보 */}
          <div className="space-y-6">
            <div className="bg-var-card rounded-2xl p-6 border border-var-color">
              <h2 className="text-xl font-bold text-var-primary mb-4 flex items-center gap-2">
                📞 연락처 정보
              </h2>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span className="text-red-500 text-xl">📞</span>
                  <div>
                    <div className="font-medium text-var-primary">{service.contact.phone}</div>
                    <div className="text-var-muted text-sm">전화 문의</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className="text-orange-500 text-xl">⏰</span>
                  <div>
                    <div className="font-medium text-var-primary">{service.contact.hours}</div>
                    <div className="text-var-muted text-sm">운영 시간</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className="text-red-500 text-xl">📍</span>
                  <div>
                    <div className="font-medium text-var-primary">{service.contact.address}</div>
                    <div className="text-var-muted text-sm">사업장 위치</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <span className="text-blue-500 text-xl">📧</span>
                  <div>
                    <div className="font-medium text-var-primary">{service.contact.email}</div>
                    <div className="text-var-muted text-sm">이메일 문의</div>
                  </div>
                </div>
              </div>
              
              <button 
                onClick={handleInquiry}
                className="w-full mt-6 bg-green-600 text-white py-3 rounded-xl font-medium hover:bg-green-700 transition-colors"
              >
                전화 상담 신청
              </button>
            </div>

            {/* 주의사항 */}
            <div className="bg-gray-50 rounded-2xl p-6">
              <h3 className="font-medium text-var-primary mb-3">📋 이용 안내</h3>
              <div className="text-sm text-var-secondary space-y-2">
                <p>• 정확한 견적은 현장 상담 후 제공됩니다.</p>
                <p>• 시공 일정은 업체와 협의하여 결정됩니다.</p>
                <p>• A/S 및 하자보수는 업체 정책에 따릅니다.</p>
                <p>• 계약 전 상세 조건을 반드시 확인하세요.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}