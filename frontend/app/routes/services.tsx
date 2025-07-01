import { useState, useEffect, useRef } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate, Link } from "@remix-run/react";
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
  try {
    // 실제 API에서 서비스 데이터 조회
    const { fetchServices } = await import('~/lib/services-api');
    const response = await fetchServices({ page: 1, size: 50 }); // 더 많은 데이터 조회

    if (response.success && response.data) {
      // API 응답을 Mock 서비스 형식으로 변환
      const { convertPostsToServiceResponses } = await import('~/lib/services-api');
      const { convertServicePostToMockService } = await import('~/types/service-types');
      
      const serviceResponses = convertPostsToServiceResponses(response.data.items);
      
      const services = serviceResponses.map((serviceResponse, index) => {
        const category = serviceResponse.metadata.category as any || '이사';
        const mockService = convertServicePostToMockService(
          serviceResponse.serviceData,
          parseInt(serviceResponse.id) || index + 1,
          category
        );
        // 실제 Post ID를 저장하여 상세페이지에서 사용
        mockService.postId = serviceResponse.id;
        return mockService;
      });

      console.log(`Loaded ${services.length} services from API`);
      return json({ services, fromApi: true });
    } else {
      console.warn('Failed to fetch services from API, using fallback data');
      throw new Error('API fetch failed');
    }
  } catch (error) {
    console.error('Error loading services from API:', error);
    
    // Fallback: 기존 Mock 데이터 사용
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
        stats: { views: 89, inquiries: 15, reviews: 42 },
        verified: true,
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
        stats: { views: 67, inquiries: 12, reviews: 28 },
        verified: false,
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
        stats: { views: 234, inquiries: 45, reviews: 78 },
        verified: true,
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

    return json({ services: fallbackServices, fromApi: false });
  }
};

const categories = [
  { value: "all", label: "전체" },
  { value: "moving", label: "이사" },
  { value: "cleaning", label: "청소" },
  { value: "aircon", label: "에어컨" }
];

const sortOptions = [
  { value: "latest", label: "최신순" },
  { value: "views", label: "조회수" },
  { value: "saves", label: "저장수" },
  { value: "reviews", label: "후기수" },
  { value: "inquiries", label: "문의수" }
];

export default function Services() {
  const { services: initialServices, fromApi } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();
  
  const [filteredServices, setFilteredServices] = useState(initialServices);
  const [sortedServices, setSortedServices] = useState(initialServices);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  // API 연동 상태 표시
  useEffect(() => {
    if (fromApi) {
      console.log('✅ Services loaded from API');
    } else {
      console.log('⚠️ Using fallback data (API unavailable)');
      showError('서비스 데이터를 불러올 수 없어 기본 데이터를 표시합니다.');
    }
  }, [fromApi, showError]);

  const handleCategoryFilter = async (filterValue: string) => {
    setCurrentFilter(filterValue);
    setIsSearching(true);
    
    try {
      if (fromApi) {
        // API를 통한 카테고리 필터링
        let response;
        
        if (filterValue === 'all') {
          const { fetchServices } = await import('~/lib/services-api');
          response = await fetchServices({ page: 1, size: 50 });
        } else {
          const { fetchServicesByCategory } = await import('~/lib/services-api');
          const categoryMap = {
            'moving': '이사',
            'cleaning': '청소', 
            'aircon': '에어컨'
          } as const;
          
          const category = categoryMap[filterValue as keyof typeof categoryMap];
          response = await fetchServicesByCategory(category, { page: 1, size: 50 });
        }
        
        if (response.success && response.data) {
          const { convertPostsToServiceResponses } = await import('~/lib/services-api');
          const { convertServicePostToMockService } = await import('~/types/service-types');
          
          const serviceResponses = convertPostsToServiceResponses(response.data.items);
          const filteredResults = serviceResponses.map((serviceResponse, index) => {
            const category = serviceResponse.metadata.category as any || '이사';
            const mockService = convertServicePostToMockService(
              serviceResponse.serviceData,
              parseInt(serviceResponse.id) || index + 1,
              category
            );
            // 실제 Post ID를 저장하여 상세페이지에서 사용
            mockService.postId = serviceResponse.id;
            return mockService;
          });
          
          setFilteredServices(filteredResults);
          applySortToFilteredServices(filteredResults, sortBy);
          console.log(`Category filter found ${filteredResults.length} results for "${filterValue}"`);
        } else {
          throw new Error('Category filter API failed');
        }
      } else {
        // Fallback: 클라이언트 사이드 필터링
        let filtered;
        if (filterValue === 'all') {
          filtered = [...initialServices];
        } else {
          filtered = initialServices.filter((service: MockService) => 
            service.category.includes(filterValue === 'moving' ? '이사' : 
                                      filterValue === 'cleaning' ? '청소' :
                                      filterValue === 'aircon' ? '에어컨' : '')
          );
        }
        
        setFilteredServices(filtered);
        applySortToFilteredServices(filtered, sortBy);
      }
    } catch (error) {
      console.error('Category filtering failed:', error);
      showError('카테고리 필터링 중 오류가 발생했습니다.');
      
      // Fallback to client-side filtering
      let filtered;
      if (filterValue === 'all') {
        filtered = [...initialServices];
      } else {
        const categoryMatch = {
          'moving': '이사',
          'cleaning': '청소', 
          'aircon': '에어컨'
        } as const;
        
        const targetCategory = categoryMatch[filterValue as keyof typeof categoryMatch];
        filtered = initialServices.filter((service: MockService) => 
          service.category === targetCategory
        );
      }
      
      setFilteredServices(filtered);
      applySortToFilteredServices(filtered, sortBy);
    } finally {
      setIsSearching(false);
    }
  };

  const applySortToFilteredServices = (services: MockService[], sortOption: string) => {
    let sorted;
    switch(sortOption) {
      case 'latest':
        // ID 기준으로 최신순 (높은 ID가 최신)
        sorted = [...services].sort((a, b) => b.id - a.id);
        break;
      case 'views':
        sorted = [...services].sort((a, b) => 
          (b.stats ? b.stats.views : 0) - (a.stats ? a.stats.views : 0)
        );
        break;
      case 'saves':
        sorted = [...services].sort((a, b) => 
          Math.floor((b.stats ? b.stats.views : 0) * 0.12) - Math.floor((a.stats ? a.stats.views : 0) * 0.12)
        );
        break;
      case 'reviews':
        sorted = [...services].sort((a, b) => 
          (b.stats ? b.stats.reviews : b.reviews.length) - (a.stats ? a.stats.reviews : a.reviews.length)
        );
        break;
      case 'inquiries':
        sorted = [...services].sort((a, b) => 
          (b.stats ? b.stats.inquiries : 0) - (a.stats ? a.stats.inquiries : 0)
        );
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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
    
    try {
      if (searchQuery.trim()) {
        if (fromApi) {
          // API를 통한 검색
          const { searchServices } = await import('~/lib/services-api');
          const response = await searchServices(searchQuery.trim(), { page: 1, size: 50 });
          
          if (response.success && response.data) {
            const { convertPostsToServiceResponses } = await import('~/lib/services-api');
            const { convertServicePostToMockService } = await import('~/types/service-types');
            
            const serviceResponses = convertPostsToServiceResponses(response.data.items);
            const searchResults = serviceResponses.map((serviceResponse, index) => {
              const category = serviceResponse.metadata.category as any || '이사';
              const mockService = convertServicePostToMockService(
                serviceResponse.serviceData,
                parseInt(serviceResponse.id) || index + 1,
                category
              );
              // 실제 Post ID를 저장하여 상세페이지에서 사용
              mockService.postId = serviceResponse.id;
              return mockService;
            });
            
            setFilteredServices(searchResults);
            applySortToFilteredServices(searchResults, sortBy);
            console.log(`Search found ${searchResults.length} results for "${searchQuery}"`);
            
            if (searchResults.length === 0) {
              showError(`"${searchQuery}"에 대한 검색 결과가 없습니다.`);
            }
          } else {
            throw new Error('Search API failed');
          }
        } else {
          // Fallback to client-side search
          const filtered = initialServices.filter((service: MockService) =>
            service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
            service.description.toLowerCase().includes(searchQuery.toLowerCase())
          );
          setFilteredServices(filtered);
          applySortToFilteredServices(filtered, sortBy);
          
          if (filtered.length === 0) {
            showError(`"${searchQuery}"에 대한 검색 결과가 없습니다.`);
          }
        }
      } else {
        setFilteredServices(initialServices);
        applySortToFilteredServices(initialServices, sortBy);
      }
    } catch (error) {
      console.error('Search failed:', error);
      showError('검색 중 오류가 발생했습니다.');
      
      // Fallback to client-side search
      const filtered = initialServices.filter((service: MockService) =>
        service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredServices(filtered);
      applySortToFilteredServices(filtered, sortBy);
    } finally {
      setIsSearching(false);
    }
  };


  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  const handleServiceClick = (service: MockService) => {
    // API에서 받은 데이터의 경우 postId 사용, 아니면 기본 id 사용
    const targetId = (service as any).postId || service.id;
    console.log('Service clicked:', service.id, 'Post ID:', targetId);
    console.log('Navigating to:', `/services/${targetId}`);
    navigate(`/services/${targetId}`);
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
        {/* 업체 등록 버튼과 검색창 - 나란히 배치 */}
        <div className="flex justify-center items-center gap-4 mb-6">
          <Link
            to="/services/write"
            className="w-full max-w-xs px-6 py-3 bg-var-card border border-var-color rounded-full hover:border-accent-primary hover:bg-var-hover transition-all duration-200 font-medium text-var-primary flex items-center justify-center gap-2"
          >
            📝 업체 등록
          </Link>
          
          <form onSubmit={handleSearch} className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
            {isSearching ? (
              <div className="w-4 h-4 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
            ) : (
              <span className="text-var-muted">🔍</span>
            )}
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isSearching ? "검색 중..." : "서비스 검색..."}
              disabled={isSearching}
              className="flex-1 bg-transparent border-none outline-none text-var-primary placeholder-var-muted disabled:opacity-50"
            />
          </form>
        </div>

        {/* 필터바와 정렬 옵션 */}
        <div className="flex justify-between items-center mb-4">
          {/* 필터 바 */}
          <div className="flex gap-2">
            {categories.map((category) => (
              <button
                key={category.value}
                onClick={() => handleCategoryFilter(category.value)}
                disabled={isSearching}
                className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                  currentFilter === category.value
                    ? 'border-accent-primary bg-accent-primary text-white'
                    : 'border-var-color bg-var-card text-var-secondary hover:border-accent-primary hover:text-accent-primary'
                }`}
              >
                {isSearching && currentFilter === category.value && (
                  <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                )}
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
              onClick={() => handleServiceClick(service)}
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

              {/* 사용자 반응 표시 */}
              <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    👁️ {service.stats ? service.stats.views : 0}
                  </span>
                  <span className="flex items-center gap-1">
                    👍 {Math.floor((service.stats ? service.stats.views : 0) * 0.15)}
                  </span>
                  <span className="flex items-center gap-1">
                    👎 {Math.floor((service.stats ? service.stats.views : 0) * 0.03)}
                  </span>
                  <span className="flex items-center gap-1">
                    🔖 {Math.floor((service.stats ? service.stats.views : 0) * 0.12)}
                  </span>
                  <span className="flex items-center gap-1">
                    문의 {service.stats ? service.stats.inquiries : 0}
                  </span>
                  <span className="flex items-center gap-1">
                    후기 {service.stats ? service.stats.reviews : service.reviews.length}
                  </span>
                </div>
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