import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import { parseServicePost } from "~/types/service-types";
import type { ServicePost } from "~/types/service-types";

export const meta: MetaFunction = () => {
  return [
    { title: "업체 등록 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새로운 서비스 업체를 등록해보세요" },
  ];
};

const categories = [
  { value: "moving", label: "이사" },
  { value: "cleaning", label: "청소" },
  { value: "aircon", label: "에어컨" }
];

export default function ServicesWrite() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  
  // 수정 모드 확인
  const editSlug = searchParams.get('edit');
  const isEditMode = !!editSlug;
  
  const [formData, setFormData] = useState({
    category: "moving",
    companyName: "",
    contact: "",
    availableHours: "",
    description: ""
  });
  const [services, setServices] = useState([
    { serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [originalPost, setOriginalPost] = useState<any>(null);

  // 수정 모드일 때 기존 데이터 로드
  const loadExistingService = async () => {
    if (!isEditMode || !editSlug) return;
    
    setIsLoading(true);
    try {
      console.log('🔍 Loading existing service for edit:', editSlug);
      
      // 기존 서비스 데이터 가져오기
      const response = await apiClient.getPost(editSlug);
      
      if (response.success && response.data) {
        console.log('📦 Loaded post data:', response.data);
        setOriginalPost(response.data);
        
        // content 필드에서 ServicePost JSON 파싱
        try {
          console.log('📝 Parsing content:', response.data.content);
          const serviceData: ServicePost = parseServicePost(response.data.content);
          console.log('✅ Parsed service data:', serviceData);
          
          // 카테고리 매핑 (metadata에서 가져오기)
          let category = "moving"; // 기본값
          if (response.data.metadata?.category) {
            const categoryMap: { [key: string]: string } = {
              '이사': 'moving',
              '청소': 'cleaning', 
              '에어컨': 'aircon'
            };
            category = categoryMap[response.data.metadata.category] || "moving";
          }
          
          // 폼 데이터 설정
          setFormData({
            category,
            companyName: serviceData.company.name,
            contact: serviceData.company.contact,
            availableHours: serviceData.company.availableHours,
            description: serviceData.company.description
          });
          
          // 서비스 목록 설정 (문자열 기반 가격 처리)
          const mappedServices = serviceData.services.map(service => ({
            serviceName: service.name,
            price: service.price, // 이미 문자열이므로 그대로 사용
            specialPrice: service.specialPrice || "",
            hasSpecialPrice: !!service.specialPrice
          }));
          
          setServices(mappedServices.length > 0 ? mappedServices : [
            { serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }
          ]);
          
          console.log('✅ Form data loaded successfully:', {
            formData: {
              category,
              companyName: serviceData.company.name,
              contact: serviceData.company.contact,
              availableHours: serviceData.company.availableHours,
              description: serviceData.company.description
            },
            services: mappedServices,
            // 🔍 숫자 정밀도 디버깅
            originalPrices: serviceData.services.map(s => ({ name: s.name, price: s.price, type: typeof s.price })),
            mappedPrices: mappedServices.map(s => ({ name: s.serviceName, price: s.price, type: typeof s.price }))
          });
          
        } catch (parseError) {
          console.error('❌ Failed to parse service content:', parseError);
          showError('업체 정보를 불러오는 중 오류가 발생했습니다. 올바르지 않은 데이터 형식입니다.');
          navigate('/services');
          return;
        }
      } else {
        console.error('❌ Failed to load post:', response);
        showError('업체 정보를 찾을 수 없습니다.');
        navigate('/services');
      }
    } catch (error) {
      console.error('🚨 Error loading existing service:', error);
      showError('업체 정보를 불러오는 중 오류가 발생했습니다.');
      navigate('/services');
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 시 수정 모드라면 데이터 로드
  useEffect(() => {
    if (isEditMode) {
      loadExistingService();
    }
  }, [isEditMode, editSlug]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleServiceChange = (index: number, field: string, value: string) => {
    // 가격 필드는 숫자만 허용
    if (field === 'price' || field === 'specialPrice') {
      // 숫자만 남기고 문자열로 저장 (정밀도 보장)
      const cleanedValue = value.replace(/[^\d]/g, '');
      setServices(prev => prev.map((service, i) => 
        i === index ? { ...service, [field]: cleanedValue } : service
      ));
    } else {
      setServices(prev => prev.map((service, i) => 
        i === index ? { ...service, [field]: value } : service
      ));
    }
  };

  const handleSpecialPriceToggle = (index: number, checked: boolean) => {
    setServices(prev => prev.map((service, i) => 
      i === index 
        ? { ...service, hasSpecialPrice: checked, specialPrice: checked ? service.specialPrice : "" }
        : service
    ));
  };

  const addService = () => {
    setServices(prev => [...prev, { serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }]);
  };

  const removeService = (index: number) => {
    if (services.length > 1) {
      setServices(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 입력 검증
    if (!formData.companyName.trim()) {
      showError("업체명을 입력해주세요.");
      return;
    }
    
    if (!formData.contact.trim()) {
      showError("연락처를 입력해주세요.");
      return;
    }
    
    if (!formData.availableHours.trim()) {
      showError("문의 가능시간을 입력해주세요.");
      return;
    }
    
    // 서비스 검증
    for (let i = 0; i < services.length; i++) {
      const service = services[i];
      if (!service.serviceName.trim()) {
        showError(`${i + 1}번째 서비스 이름을 입력해주세요.`);
        return;
      }
      if (!service.price.trim()) {
        showError(`${i + 1}번째 서비스 가격을 입력해주세요.`);
        return;
      }
      if (service.hasSpecialPrice && !service.specialPrice.trim()) {
        showError(`${i + 1}번째 서비스의 특가를 입력해주세요.`);
        return;
      }
    }

    setIsSubmitting(true);
    
    try {
      // 업체 데이터를 ServicePost 형식으로 구성
      const servicePostData = {
        company: {
          name: formData.companyName.trim(),
          contact: formData.contact.trim(),
          availableHours: formData.availableHours.trim(),
          description: formData.description.trim()
        },
        services: services
          .filter(s => s.serviceName.trim() && s.price.trim())
          .map(service => ({
            name: service.serviceName.trim(),
            price: service.price.trim() || '0', // 문자열로 유지하여 정밀도 보장
            specialPrice: service.hasSpecialPrice && service.specialPrice ? 
              service.specialPrice.trim() : undefined, // 문자열로 유지하여 정밀도 보장
            description: undefined // 현재 폼에는 서비스별 설명 없음
          }))
      };

      const categoryKorean = formData.category === 'moving' ? '이사' : 
                            formData.category === 'cleaning' ? '청소' : '에어컨';

      if (isEditMode && originalPost) {
        // 수정 모드: PUT 요청
        console.log('📝 Updating existing service:', editSlug);
        
        const updateData = {
          title: servicePostData.company.name,
          content: JSON.stringify(servicePostData, null, 2),
          metadata: {
            type: 'moving services',
            category: categoryKorean,
            tags: [categoryKorean, '업체', '서비스'],
            visibility: 'public'
          }
        };
        
        const response = await apiClient.updatePost(editSlug!, updateData);
        
        if (response.success) {
          showSuccess("업체 정보가 성공적으로 수정되었습니다!");
          console.log('Service updated successfully:', response.data);
          
          // 수정된 서비스 상세 페이지로 이동
          navigate(`/moving-services/${editSlug}`);
        } else {
          throw new Error(response.error || '서비스 수정에 실패했습니다.');
        }
      } else {
        // 신규 등록 모드: POST 요청
        console.log('🆕 Creating new service');
        
        const { createService } = await import('~/lib/services-api');
        const response = await createService({
          servicePost: servicePostData,
          category: categoryKorean
        });

        if (response.success) {
          showSuccess("업체가 성공적으로 등록되었습니다!");
          console.log('Service created successfully:', response.data);
          
          // 폼 리셋
          setFormData({
            category: "moving",
            companyName: "",
            contact: "",
            availableHours: "",
            description: ""
          });
          setServices([{ serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }]);
          
          // 서비스 목록 페이지로 이동
          navigate("/services");
        } else {
          throw new Error(response.error || '서비스 등록에 실패했습니다.');
        }
      }
      
    } catch (error) {
      const errorMessage = isEditMode ? "업체 정보 수정 중 오류가 발생했습니다." : "업체 등록 중 오류가 발생했습니다.";
      showError(errorMessage);
      console.error("업체 처리 오류:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    const hasContent = formData.companyName.trim() || 
                      formData.description.trim() || 
                      services.some(s => s.serviceName.trim() || s.price.trim());
    
    const cancelMessage = isEditMode 
      ? "수정 중인 내용이 있습니다. 정말로 취소하시겠습니까?"
      : "작성 중인 내용이 있습니다. 정말로 취소하시겠습니까?";
    
    if (hasContent) {
      if (window.confirm(cancelMessage)) {
        if (isEditMode) {
          navigate(`/moving-services-post/${editSlug}`);
        } else {
          navigate("/services");
        }
      }
    } else {
      if (isEditMode) {
        navigate(`/moving-services-post/${editSlug}`);
      } else {
        navigate("/services");
      }
    }
  };

  // 로딩 중일 때 표시할 컴포넌트
  if (isLoading) {
    return (
      <AppLayout 
        user={user || { id: 'test', email: 'test@test.com', name: '테스트사용자' }}
        onLogout={logout}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <div className="text-center">
              <div className="text-4xl mb-4">⏳</div>
              <p className="text-var-secondary">업체 정보를 불러오는 중...</p>
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout 
      user={user || { id: 'test', email: 'test@test.com', name: '테스트사용자' }}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-var-primary mb-2">
            {isEditMode ? '업체 정보 수정' : '업체 등록'}
          </h1>
          <p className="text-var-secondary">
            {isEditMode 
              ? '등록된 업체 정보를 수정할 수 있습니다.'
              : '아파트 주민들에게 유용한 서비스를 제공하는 업체를 등록해보세요.'
            }
          </p>
        </div>

        {/* 업체 등록 폼 */}
        <div className="bg-var-card border border-var-color rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 카테고리 선택 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                카테고리 <span className="text-red-500">*</span>
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
              >
                {categories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 업체명 입력 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                업체명 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                placeholder="업체명을 입력하세요"
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                maxLength={100}
              />
            </div>

            {/* 연락처와 문의 가능시간 - 같은 행 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-var-primary mb-2">
                  연락처 <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  name="contact"
                  value={formData.contact}
                  onChange={handleInputChange}
                  placeholder="연락처를 입력하세요"
                  className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-var-primary mb-2">
                  문의 가능시간 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="availableHours"
                  value={formData.availableHours}
                  onChange={handleInputChange}
                  placeholder="예: 09:00~18:00"
                  className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                />
              </div>
            </div>

            {/* 서비스 목록 라벨과 추가 버튼 */}
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-var-primary">
                서비스 목록 <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={addService}
                className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors duration-200 flex items-center gap-2 text-sm"
              >
                ➕ 추가
              </button>
            </div>

            {/* 서비스 목록 섹션 */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <div className="space-y-4">
                {services.map((service, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="block text-xs font-medium text-gray-600">
                            서비스{index + 1} 이름
                          </label>
                          {services.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeService(index)}
                              className="text-red-500 hover:text-red-700 text-xs"
                            >
                              🗑️ 삭제
                            </button>
                          )}
                        </div>
                        <input
                          type="text"
                          value={service.serviceName}
                          onChange={(e) => handleServiceChange(index, 'serviceName', e.target.value)}
                          placeholder="서비스 이름을 입력하세요"
                          className="w-full px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
                          maxLength={100}
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">
                          서비스{index + 1} 가격
                        </label>
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <input
                              type="number"
                              value={service.price}
                              onChange={(e) => handleServiceChange(index, 'price', e.target.value)}
                              placeholder={service.hasSpecialPrice ? "기존 가격" : "가격을 입력하세요"}
                              className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                              min="0"
                            />
                            <label className="flex items-center gap-1 text-xs text-var-primary">
                              <input
                                type="checkbox"
                                checked={service.hasSpecialPrice}
                                onChange={(e) => handleSpecialPriceToggle(index, e.target.checked)}
                                className="w-3 h-3 text-accent-primary bg-var-section border-var-color rounded focus:ring-accent-primary focus:ring-1"
                              />
                              특가
                            </label>
                          </div>
                          
                          {service.hasSpecialPrice && (
                            <div className="flex items-center gap-3">
                              <input
                                type="number"
                                value={service.specialPrice}
                                onChange={(e) => handleServiceChange(index, 'specialPrice', e.target.value)}
                                placeholder="특가 가격"
                                className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                min="0"
                              />
                              <div className="w-10"></div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 업체 소개 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                업체 소개
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="업체 소개를 입력하세요..."
                rows={6}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
                maxLength={1000}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.description.length}/1,000자
              </div>
            </div>

            {/* 등록 가이드라인 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">📝 업체 등록 가이드라인</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 정확하고 신뢰할 수 있는 업체 정보를 제공해주세요</li>
                <li>• 서비스 내용과 가격을 명확하게 기재해주세요</li>
                <li>• 연락처와 문의 가능시간을 정확히 입력해주세요</li>
                <li>• 아파트 주민들에게 도움이 되는 서비스를 등록해주세요</li>
                <li>• 허위 정보나 과장된 내용은 피해주세요</li>
              </ul>
            </div>

            {/* 버튼 영역 */}
            <div className="flex justify-end gap-3 pt-4 border-t border-var-color">
              <button
                type="button"
                onClick={handleCancel}
                disabled={isSubmitting}
                className="px-6 py-3 border border-var-color rounded-lg text-var-secondary hover:bg-var-hover transition-colors duration-200 disabled:opacity-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={
                  isSubmitting || 
                  !formData.companyName.trim() || 
                  !formData.contact.trim() || 
                  !formData.availableHours.trim() ||
                  !services.some(s => s.serviceName.trim() && s.price.trim())
                }
                className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {isEditMode ? '수정 중...' : '등록 중...'}
                  </>
                ) : (
                  <>
                    {isEditMode ? '✅ 업체 정보 수정' : '📝 업체 등록'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AppLayout>
  );
}