import { useState, useEffect, useRef } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import type { MockService } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 입주 업체 서비스" },
  ];
};

export const loader: LoaderFunction = async () => {
  // Mock 서비스 데이터 - 입주 업체 서비스 기반
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
      stats: {
        views: 156,
        inquiries: 23,
        reviews: 89
      },
      verified: true,
      contact: {
        phone: '02-2345-6789',
        hours: '평일 09:00-19:00',
        address: '서울시 서초구 xx동',
        email: 'home@style.com'
      },
      reviews: [
        { author: '김민수', rating: 5, text: '꼼꼼하고 정성스럽게 작업해주셔서 만족합니다. 추천합니다!' },
        { author: '이영희', rating: 4, text: '가격 대비 품질이 좋아요. 다음에도 이용할 예정입니다.' }
      ]
    },
    {
      id: 2,
      name: '퀵배송 서비스',
      category: '택배/배송',
      rating: 4.8,
      description: '빠르고 안전한 배송 서비스를 제공합니다. 당일배송부터 대형 가구 배송까지 모든 배송 서비스를 제공합니다.',
      services: [
        { name: '당일 배송', price: '5,000원', description: '당일 배송 서비스' },
        { name: '대량 가구 배송', price: '30,000원', originalPrice: '50,000원', description: '대형 가구 배송' },
        { name: '이사 도움', price: '100,000원~', description: '이사 관련 도움' }
      ],
      stats: {
        views: 89,
        inquiries: 15,
        reviews: 42
      },
      verified: true,
      contact: {
        phone: '02-3456-7890',
        hours: '평일 08:00-20:00',
        address: '서울시 강남구 xx동',
        email: 'quick@delivery.com'
      },
      reviews: [
        { author: '박상준', rating: 5, text: '정말 깨끗하게 청소해주셨어요. 만족합니다!' },
        { author: '최수진', rating: 5, text: '친절하고 꼼꼼하게 해주시네요. 다음에도 부탁드릴게요.' }
      ]
    },
    {
      id: 3,
      name: '청준 청소 대행',
      category: '청소',
      rating: 4.4,
      description: '아파트 전문 청소 서비스를 제공합니다. 정기 청소부터 대청소까지 모든 청소 서비스를 제공합니다.',
      services: [
        { name: '의류 청소', price: '35,000원', description: '의류 전문 청소' },
        { name: '기타 정리', price: '30,000원', description: '각종 정리 서비스' }
      ],
      stats: {
        views: 67,
        inquiries: 12,
        reviews: 28
      },
      verified: false,
      contact: {
        phone: '02-8765-4321',
        hours: '평일 09:00-18:00',
        address: '서울시 송파구 xx동',
        email: 'clean@service.com'
      },
      reviews: [
        { author: '정현우', rating: 4, text: '청소가 깔끔하고 만족스러웠습니다.' },
        { author: '김소영', rating: 5, text: '친절하고 꼼꼼하게 해주시네요.' }
      ]
    },
    {
      id: 4,
      name: '펫케어 클리닉',
      category: '반려동물',
      rating: 4.7,
      description: '반려동물 전문 케어 서비스를 제공합니다. Windows 정품 인증 등 컴퓨터 관련 서비스도 함께 제공합니다.',
      services: [
        { name: '기타 정리', price: '30,000원', description: '반려동물 용품 정리' }
      ],
      stats: {
        views: 234,
        inquiries: 45,
        reviews: 78
      },
      verified: true,
      contact: {
        phone: '02-9876-5432',
        hours: '평일 10:00-19:00',
        address: '서울시 마포구 xx동',
        email: 'pet@care.com'
      },
      reviews: [
        { author: '이민정', rating: 5, text: '반려동물을 정말 사랑으로 돌봐주세요.' },
        { author: '박철수', rating: 4, text: '전문적이고 믿을 만한 서비스입니다.' }
      ]
    }
  ];

  return json({ services });
};

const categories = [
  { value: "all", label: "전체" },
  { value: "interior", label: "인테리어" },
  { value: "delivery", label: "택배/배송" },
  { value: "cleaning", label: "청소" },
  { value: "pet", label: "반려동물" }
];

const sortOptions = [
  { value: "rating", label: "평점순" },
  { value: "name", label: "업체명순" },
  { value: "reviews", label: "리뷰순" }
];

export default function Services() {
  const { services: initialServices } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const navigate = useNavigate();
  
  const [filteredServices, setFilteredServices] = useState(initialServices);
  const [sortedServices, setSortedServices] = useState(initialServices);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("rating");
  const [searchQuery, setSearchQuery] = useState("");

  const handleCategoryFilter = (filterValue: string) => {
    setCurrentFilter(filterValue);
    
    let filtered;
    if (filterValue === 'all') {
      filtered = [...initialServices];
    } else {
      filtered = initialServices.filter((service: MockService) => 
        service.category.includes(filterValue === 'interior' ? '인테리어' : 
                                  filterValue === 'delivery' ? '택배/배송' :
                                  filterValue === 'cleaning' ? '청소' : 
                                  filterValue === 'pet' ? '반려동물' : '')
      );
    }
    
    setFilteredServices(filtered);
    applySortToFilteredServices(filtered, sortBy);
  };

  const applySortToFilteredServices = (services: MockService[], sortOption: string) => {
    let sorted;
    switch(sortOption) {
      case 'rating':
        sorted = [...services].sort((a, b) => b.rating - a.rating);
        break;
      case 'name':
        sorted = [...services].sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'reviews':
        sorted = [...services].sort((a, b) => b.reviews.length - a.reviews.length);
        break;
      default:
        sorted = [...services];
    }
    
    setSortedServices(sorted);
  };

  const handleSort = (sortOption: string) => {
    setSortBy(sortOption);
    applySortToFilteredServices(filteredServices, sortOption);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const filtered = initialServices.filter((service: MockService) =>
        service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredServices(filtered);
      applySortToFilteredServices(filtered, sortBy);
    } else {
      setFilteredServices(initialServices);
      applySortToFilteredServices(initialServices, sortBy);
    }
  };


  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  const handleServiceClick = (serviceId: number) => {
    console.log('Service clicked:', serviceId);
    console.log('Navigating to:', `/services/${serviceId}`);
    navigate(`/services/${serviceId}`);
  };

  useEffect(() => {
    applySortToFilteredServices(filteredServices, sortBy);
  }, [filteredServices, sortBy]);

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 검색 및 필터 섹션 */}
      <div className="mb-8">
        {/* 검색 */}
        <div className="flex justify-center items-center gap-4 mb-6">
          <div className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
            <span className="text-var-muted">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch(e as any)}
              placeholder="서비스 검색..."
              className="flex-1 bg-transparent border-none outline-none text-var-primary placeholder-var-muted"
            />
          </div>
        </div>

        {/* 필터바와 정렬 옵션 */}
        <div className="flex justify-between items-center mb-4">
          {/* 필터 바 */}
          <div className="flex gap-2">
            {categories.map((category) => (
              <button
                key={category.value}
                onClick={() => handleCategoryFilter(category.value)}
                className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 ${
                  currentFilter === category.value
                    ? 'border-accent-primary bg-accent-primary text-white'
                    : 'border-var-color bg-var-card text-var-secondary hover:border-accent-primary hover:text-accent-primary'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>

          {/* 정렬 옵션 */}
          <div className="flex items-center gap-2">
            <span className="text-var-muted text-sm">정렬:</span>
            <select
              value={sortBy}
              onChange={(e) => handleSort(e.target.value)}
              className="bg-var-card border border-var-color rounded-lg px-3 py-1 text-sm text-var-primary"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 서비스 카드 목록 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {sortedServices.length > 0 ? (
          sortedServices.map((service: MockService) => (
            <div
              key={service.id} 
              onClick={() => handleServiceClick(service.id)}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              {/* 카테고리와 인증 */}
              <div className="flex items-center gap-2 mb-3">
                <span className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-medium">
                  {service.category}
                </span>
                {service.verified && (
                  <span className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                    인증
                  </span>
                )}
              </div>

              {/* 업체명 */}
              <h3 className="text-lg font-bold text-gray-900 mb-4">{service.name}</h3>

              {/* 서비스 목록 */}
              <div className="space-y-2 mb-4">
                {service.services.map((item, idx: number) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-gray-700 text-sm">{item.name}</span>
                    <div className="flex items-center gap-2">
                      {item.originalPrice && (
                        <span className="text-gray-400 line-through text-sm">{item.originalPrice}</span>
                      )}
                      <span className="text-red-500 font-medium text-sm">{item.price}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* 연락처 */}
              <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <span className="text-pink-500">📞</span>
                  <span>{service.contact.phone}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-orange-500">⏰</span>
                  <span>{service.contact.hours}</span>
                </div>
              </div>

              {/* 통계 정보 */}
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>관심 {service.stats ? service.stats.views : 0}</span>
                <span>문의 {service.stats ? service.stats.inquiries : 0}</span>
                <span>후기 {service.stats ? service.stats.reviews : service.reviews.length}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full flex flex-col items-center justify-center text-center p-12">
            <div className="text-6xl mb-4">🏢</div>
            <h3 className="text-var-primary font-semibold text-lg mb-2">
              서비스가 없습니다
            </h3>
            <p className="text-var-secondary">
              {searchQuery ? '검색 결과가 없습니다. 다른 키워드로 검색해보세요.' : '등록된 서비스가 없습니다.'}
            </p>
          </div>
        )}
      </div>

      {/* 서비스 등록 안내 */}
      <div className="mt-12 card p-8 bg-var-section">
        <div className="text-center">
          <h3 className="text-var-primary font-bold text-xl mb-2">
            서비스를 제공하고 계신가요?
          </h3>
          <p className="text-var-secondary mb-6">
            아파트 주민들에게 유용한 서비스를 등록해보세요!
          </p>
          <button className="bg-accent-primary text-white px-8 py-3 rounded-xl font-medium hover:bg-accent-hover transition-colors">
            서비스 등록하기
          </button>
        </div>
      </div>
    </AppLayout>
  );
}