/**
 * 업체 등록 페이지용 서비스 목록 입력 필드 컴포넌트
 */

import React from 'react';

export interface ServiceItem {
  serviceName: string;
  price: string;
  specialPrice: string;
  hasSpecialPrice: boolean;
}

interface ServiceListFieldProps {
  services: ServiceItem[];
  onServicesChange: (services: ServiceItem[]) => void;
}

export default function ServiceListField({
  services,
  onServicesChange
}: ServiceListFieldProps) {
  const handleServiceChange = (index: number, field: keyof ServiceItem, value: string | boolean) => {
    const updatedServices = services.map((service, i) => {
      if (i === index) {
        // 가격 필드는 숫자만 허용
        if ((field === 'price' || field === 'specialPrice') && typeof value === 'string') {
          const cleanedValue = value.replace(/[^\d]/g, '');
          return { ...service, [field]: cleanedValue };
        }
        return { ...service, [field]: value };
      }
      return service;
    });
    onServicesChange(updatedServices);
  };

  const handleSpecialPriceToggle = (index: number, checked: boolean) => {
    const updatedServices = services.map((service, i) => {
      if (i === index) {
        return {
          ...service,
          hasSpecialPrice: checked,
          specialPrice: checked ? service.specialPrice : ""
        };
      }
      return service;
    });
    onServicesChange(updatedServices);
  };

  const addService = () => {
    const newService: ServiceItem = {
      serviceName: "",
      price: "",
      specialPrice: "",
      hasSpecialPrice: false
    };
    onServicesChange([...services, newService]);
  };

  const removeService = (index: number) => {
    if (services.length > 1) {
      const updatedServices = services.filter((_, i) => i !== index);
      onServicesChange(updatedServices);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <label className="block text-sm font-medium text-gray-700">
          서비스 목록 <span className="text-red-500">*</span>
        </label>
        <button
          type="button"
          onClick={addService}
          className="px-4 py-2 text-white rounded-lg text-sm font-medium flex items-center gap-2"
          style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            border: 'none'
          }}
        >
          <span>➕</span>
          <span>추가</span>
        </button>
      </div>
      
      <div className="space-y-6">
        {services.map((service, index) => (
          <div key={index} className="relative border border-gray-200 rounded-lg p-4">
            {/* 삭제 버튼 (첫 번째 서비스가 아닌 경우에만) */}
            {index > 0 && (
              <div className="flex justify-end mb-2">
                <button 
                  type="button" 
                  className="text-red-500 hover:text-red-600 text-xs"
                  onClick={() => removeService(index)}
                >
                  삭제
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 서비스 이름 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-medium text-gray-600">
                    서비스{index + 1} 이름
                  </label>
                </div>
                <input
                  type="text"
                  value={service.serviceName}
                  onChange={(e) => handleServiceChange(index, 'serviceName', e.target.value)}
                  placeholder="서비스 이름을 입력하세요"
                  className="w-full px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
                  style={{
                    backgroundColor: 'var(--var-section)',
                    borderColor: 'var(--var-color)',
                    color: 'var(--var-primary)'
                  }}
                  maxLength={100}
                />
              </div>
              
              {/* 가격 */}
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
                      placeholder={service.hasSpecialPrice ? '기존 가격' : '가격을 입력하세요'}
                      className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
                      style={{
                        backgroundColor: 'var(--var-section)',
                        borderColor: 'var(--var-color)',
                        color: 'var(--var-primary)',
                        appearance: 'textfield'
                      }}
                      min="0"
                    />
                    <label className="flex items-center gap-1 text-xs text-var-primary">
                      <input
                        type="checkbox"
                        checked={service.hasSpecialPrice}
                        onChange={(e) => handleSpecialPriceToggle(index, e.target.checked)}
                        className="w-3 h-3 text-accent-primary bg-var-section border-var-color rounded focus:ring-accent-primary focus:ring-1"
                        style={{
                          accentColor: '#3b82f6'
                        }}
                      />
                      특가
                    </label>
                  </div>
                  
                  {/* 특가 입력 (체크시에만 표시) */}
                  {service.hasSpecialPrice && (
                    <div className="flex items-center gap-3 special-price-input">
                      <input
                        type="number"
                        value={service.specialPrice}
                        onChange={(e) => handleServiceChange(index, 'specialPrice', e.target.value)}
                        placeholder="특가 가격"
                        className="flex-1 px-3 py-2 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent text-sm"
                        style={{
                          backgroundColor: 'var(--var-section)',
                          borderColor: 'var(--var-color)',
                          color: 'var(--var-primary)',
                          appearance: 'textfield'
                        }}
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
  );
}