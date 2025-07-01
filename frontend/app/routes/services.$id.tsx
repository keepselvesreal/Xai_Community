import { useState } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "서비스 상세 정보" },
  ];
};

export const loader: LoaderFunction = async ({ params }) => {
  const { id } = params;
  
  if (!id) {
    throw new Response("서비스 ID가 필요합니다", { status: 400 });
  }

  // MongoDB ObjectId 형식 검증 (24자리 16진수)
  const isValidObjectId = /^[0-9a-fA-F]{24}$/.test(id);
  if (!isValidObjectId && isNaN(parseInt(id))) {
    throw new Response("잘못된 서비스 ID 형식입니다", { status: 400 });
  }
  
  try {
    // 실제 API에서 특정 서비스 데이터 조회
    const { apiClient } = await import('~/lib/api');
    console.log('Attempting to fetch service with ID:', id);
    const response = await apiClient.getPost(id as string);
    console.log('API response:', response);
    
    if (response.success && response.data) {
      // Post 데이터를 ServicePost 형식으로 변환
      const { parseServicePost, convertServicePostToMockService } = await import('~/types/service-types');
      
      try {
        const servicePost = parseServicePost(response.data.content);
        const category = response.data.metadata?.category || '이사';
        
        // MockService 형식으로 변환하여 기존 UI와 호환되도록 함
        const service = convertServicePostToMockService(
          servicePost,
          parseInt(id as string) || 1,
          category
        );
        
        // 실제 Post ID를 저장
        service.postId = response.data.id;
        
        return json({ service, fromApi: true });
      } catch (parseError) {
        console.error('Failed to parse service content:', parseError);
        throw new Error('Invalid service data format');
      }
    } else {
      throw new Error('Service not found in API');
    }
  } catch (error) {
    console.error('Error loading service from API:', error);
    
    // Fallback: Mock 서비스 데이터
    const fallbackServices = [
      {
        id: 1,
        name: '빠른이사 서비스',
        category: '이사',
        rating: 4.8,
        description: '빠르고 안전한 이사 서비스를 제공합니다.',
        services: [
          { name: '원룸 이사', price: '150,000원', description: '원룸 이사 서비스' },
          { name: '투룸 이사', price: '250,000원', originalPrice: '300,000원', description: '투룸 이사 서비스' }
        ],
        contact: {
          phone: '02-3456-7890',
          hours: '평일 08:00-20:00',
          address: '서울시 강남구 xx동',
          email: 'quick@moving.com'
        },
        reviews: [
          { author: '박상준', rating: 5, text: '정말 꼼꼼하게 이사해주셨어요. 만족합니다!' }
        ]
      },
      {
        id: 2,
        name: '청준 청소 대행',
        category: '청소',
        rating: 4.4,
        description: '아파트 전문 청소 서비스를 제공합니다.',
        services: [
          { name: '의류 청소', price: '35,000원', description: '의류 전문 청소' }
        ],
        contact: {
          phone: '02-8765-4321',
          hours: '평일 09:00-18:00',
          address: '서울시 송파구 xx동',
          email: 'clean@service.com'
        },
        reviews: [
          { author: '정현우', rating: 4, text: '청소가 깔끔하고 만족스러웠습니다.' }
        ]
      },
      {
        id: 3,
        name: '시원한 에어컨 서비스',
        category: '에어컨',
        rating: 4.7,
        description: '에어컨 전문 설치, 수리, 청소 서비스를 제공합니다.',
        services: [
          { name: '에어컨 청소', price: '80,000원', description: '에어컨 전문 청소' },
          { name: '에어컨 설치', price: '120,000원', originalPrice: '150,000원', description: '에어컨 설치 서비스' }
        ],
        contact: {
          phone: '02-9876-5432',
          hours: '평일 09:00-18:00',
          address: '서울시 마포구 xx동',
          email: 'cool@aircon.com'
        },
        reviews: [
          { author: '이민정', rating: 5, text: '에어컨 청소를 정말 깨끗하게 해주셨어요.' }
        ]
      }
    ];
    
    const service = fallbackServices.find(s => s.id === parseInt(id as string));
    
    if (!service) {
      throw new Response("서비스를 찾을 수 없습니다", { status: 404 });
    }

    return json({ service, fromApi: false });
  }
};

export default function ServiceDetail() {
  const { service } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [reviewText, setReviewText] = useState("");
  const [isLiked, setIsLiked] = useState(false);

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
                      {item.originalPrice && (
                        <div className="text-gray-400 line-through text-sm">{item.originalPrice}</div>
                      )}
                      <div className="text-red-500 font-bold text-lg">{item.price}</div>
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