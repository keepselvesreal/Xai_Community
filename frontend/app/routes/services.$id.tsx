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
  
  // Mock 서비스 데이터 - 실제로는 API에서 가져올 데이터
  const services = [
    {
      id: 1,
      name: '홈스타일 인테리어',
      category: '인테리어 전문업체',
      rating: 4.6,
      description: '아파트 맞춤형 인테리어 전문 업체입니다. 소규모 시공부터 전체 리모델링까지 다양한 서비스를 제공합니다.',
      services: [
        { name: '부분 인테리어', price: '300,000원~', description: '벽지, 바닥재 등 부분 시공' },
        { name: '전체 리모델링', price: '1,200,000원', originalPrice: '1,500,000원', description: '전체 공간 리모델링' },
        { name: '도배/장판', price: '500,000원~', description: '도배, 장판 시공' }
      ],
      contact: {
        phone: '02-2345-6789',
        hours: '평일 09:00-19:00',
        address: '서울시 서초구 xx동',
        email: 'home@style.com'
      },
      reviews: [
        { author: '김민수', rating: 5, text: '꼼꼼하고 정성스럽게 작업해주셔서 만족합니다. 추천합니다!' },
        { author: '이영희', rating: 4, text: '가격 대비 품질이 좋아요. 다음에도 이용할 예정입니다.' },
        { author: '박철수', rating: 5, text: '전문적이고 신속한 작업이 인상적이었습니다.' },
        { author: '최수연', rating: 4, text: '친절한 상담과 합리적인 가격이 좋았어요.' }
      ]
    },
    {
      id: 2,
      name: '클린마스터',
      category: '청소 전문업체',
      rating: 4.8,
      description: '입주 청소 및 이사 청소 전문 업체입니다. 친환경 세제 사용으로 안전하고 깨끗한 청소를 제공합니다.',
      services: [
        { name: '입주 청소', price: '150,000원~', description: '입주 전 전체 청소' },
        { name: '이사 청소', price: '200,000원~', description: '이사 후 청소 서비스' },
        { name: '정기 청소', price: '80,000원~', description: '월 1회 정기 청소' }
      ],
      contact: {
        phone: '02-1234-5678',
        hours: '평일 08:00-18:00',
        address: '서울시 강남구 xx동',
        email: 'clean@master.com'
      },
      reviews: [
        { author: '박상준', rating: 5, text: '정말 깨끗하게 청소해주셨어요. 만족합니다!' },
        { author: '최수진', rating: 5, text: '친절하고 꼼꼼하게 해주시네요. 다음에도 부탁드릴게요.' }
      ]
    },
    {
      id: 3,
      name: '안전한 보안',
      category: '보안 전문업체',
      rating: 4.4,
      description: '디지털 도어락, CCTV 설치 및 보안 시스템 전문 업체입니다. 24시간 A/S 서비스를 제공합니다.',
      services: [
        { name: '디지털 도어락', price: '250,000원~', description: '현관문 디지털 도어락 설치' },
        { name: 'CCTV 설치', price: '400,000원~', description: '실내외 CCTV 설치' },
        { name: '보안 시스템', price: '800,000원~', description: '종합 보안 시스템 구축' }
      ],
      contact: {
        phone: '02-3456-7890',
        hours: '평일 09:00-18:00',
        address: '서울시 송파구 xx동',
        email: 'safe@security.com'
      },
      reviews: [
        { author: '정현우', rating: 4, text: '설치 기술이 좋고 사후 관리도 잘해주세요.' },
        { author: '김소영', rating: 5, text: '빠른 설치와 친절한 설명이 좋았습니다.' }
      ]
    }
  ];

  const service = services.find(s => s.id === parseInt(id as string));
  
  if (!service) {
    throw new Response("서비스를 찾을 수 없습니다", { status: 404 });
  }

  return json({ service });
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