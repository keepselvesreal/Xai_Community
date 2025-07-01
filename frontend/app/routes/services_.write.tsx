import { useState } from "react";
import { useNavigate } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";

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
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  
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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleServiceChange = (index: number, field: string, value: string) => {
    setServices(prev => prev.map((service, i) => 
      i === index ? { ...service, [field]: value } : service
    ));
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
      // 업체 등록 데이터를 ServicePost 형식으로 구성
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
            price: parseInt(service.price) || 0,
            specialPrice: service.hasSpecialPrice && service.specialPrice ? 
              parseInt(service.specialPrice) : undefined,
            description: undefined // 현재 폼에는 서비스별 설명 없음
          }))
      };

      // 실제 API 호출
      const { createService } = await import('~/lib/services-api');
      const response = await createService({
        servicePost: servicePostData,
        category: formData.category === 'moving' ? '이사' : 
                 formData.category === 'cleaning' ? '청소' : '에어컨'
      });

      if (response.success) {
        showSuccess("업체가 성공적으로 등록되었습니다!");
        console.log('Service created successfully:', response.data);
      } else {
        throw new Error(response.error || '서비스 등록에 실패했습니다.');
      }
      
      // 폼 리셋
      setFormData({
        category: "moving",
        companyName: "",
        contact: "",
        availableHours: "",
        description: ""
      });
      setServices([{ serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }]);
      
      // 서비스 목록 페이지로 이동 (새로 등록된 서비스 확인 가능)
      navigate("/services");
      
    } catch (error) {
      showError("업체 등록 중 오류가 발생했습니다.");
      console.error("업체 등록 오류:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    const hasContent = formData.companyName.trim() || 
                      formData.description.trim() || 
                      services.some(s => s.serviceName.trim() || s.price.trim());
    
    if (hasContent) {
      if (window.confirm("작성 중인 내용이 있습니다. 정말로 취소하시겠습니까?")) {
        navigate("/services");
      }
    } else {
      navigate("/services");
    }
  };

  return (
    <AppLayout 
      user={user || { id: 'test', email: 'test@test.com', name: '테스트사용자' }}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-var-primary mb-2">업체 등록</h1>
          <p className="text-var-secondary">
            아파트 주민들에게 유용한 서비스를 제공하는 업체를 등록해보세요.
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
                              className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
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
                                className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
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
                    등록 중...
                  </>
                ) : (
                  <>
                    📝 업체 등록
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