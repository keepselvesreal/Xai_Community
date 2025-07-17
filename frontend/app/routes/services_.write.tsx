import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import PostWriteForm, { type PostWriteFormConfig } from "~/components/common/PostWriteForm";
import CategoryField from "~/components/service/CategoryField";
import ContactFields from "~/components/service/ContactFields";
import ServiceListField, { type ServiceItem } from "~/components/service/ServiceListField";
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

interface ServiceWriteData {
  title: string; // 업체명 (PostWriteForm 호환)
  content: string; // 업체 소개 (PostWriteForm 호환)
  category: string;
  contact: string;
  availableHours: string;
}

export default function ServicesWrite() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { showSuccess, showError } = useNotification();
  
  // 수정 모드 확인
  const editSlug = searchParams.get('edit');
  const isEditMode = !!editSlug;
  
  const [formData, setFormData] = useState<ServiceWriteData>({
    title: "", // 업체명
    content: "", // 업체 소개
    category: "moving",
    contact: "",
    availableHours: ""
  });
  const [services, setServices] = useState<ServiceItem[]>([
    { serviceName: "", price: "", specialPrice: "", hasSpecialPrice: false }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [originalPost, setOriginalPost] = useState<any>(null);

  // 수정 모드일 때 기존 데이터 로드
  const loadExistingService = async () => {
    if (!isEditMode || !editSlug) return;
    
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
            title: serviceData.company.name, // 업체명 -> title
            content: serviceData.company.description, // 업체 소개 -> content
            category,
            contact: serviceData.company.contact,
            availableHours: serviceData.company.availableHours
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
          
          console.log('✅ Form data loaded successfully');
          
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
    }
  };

  // 컴포넌트 마운트 시 수정 모드라면 데이터 로드
  useEffect(() => {
    if (isEditMode) {
      loadExistingService();
    }
  }, [isEditMode, editSlug]);

  // PostWriteForm 호환 데이터 변경 핸들러
  const handleDataChange = (data: Partial<ServiceWriteData>) => {
    setFormData(prev => ({ ...prev, ...data }));
  };

  // 카테고리 변경 핸들러
  const handleCategoryChange = (category: string) => {
    setFormData(prev => ({ ...prev, category }));
  };

  // 연락처 변경 핸들러
  const handleContactChange = (contact: string) => {
    setFormData(prev => ({ ...prev, contact }));
  };

  // 문의 가능시간 변경 핸들러
  const handleAvailableHoursChange = (availableHours: string) => {
    setFormData(prev => ({ ...prev, availableHours }));
  };

  // 서비스 목록 변경 핸들러
  const handleServicesChange = (newServices: ServiceItem[]) => {
    setServices(newServices);
  };

  const handleSubmit = async (data: ServiceWriteData) => {
    // 입력 검증
    if (!data.contact.trim()) {
      showError("연락처를 입력해주세요.");
      return;
    }
    
    if (!data.availableHours.trim()) {
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
          name: data.title.trim(), // title -> name
          contact: data.contact.trim(),
          availableHours: data.availableHours.trim(),
          description: data.content.trim() // content -> description
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

      const categoryKorean = data.category === 'moving' ? '이사' : 
                            data.category === 'cleaning' ? '청소' : '에어컨';

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
            title: "",
            content: "",
            category: "moving",
            contact: "",
            availableHours: ""
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
    const hasContent = formData.title.trim() || 
                      formData.content.trim() || 
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

  // PostWriteForm 설정
  const config: PostWriteFormConfig = {
    pageTitle: isEditMode ? '업체 정보 수정' : '업체 등록',
    pageDescription: isEditMode 
      ? '등록된 업체 정보를 수정할 수 있습니다.'
      : '아파트 주민들에게 유용한 서비스를 제공하는 업체를 등록해보세요.',
    submitButtonText: isEditMode ? '업체 정보 수정' : '업체 등록',
    successMessage: isEditMode ? '업체 정보가 성공적으로 수정되었습니다!' : '업체가 성공적으로 등록되었습니다!',
    guidelines: [
      '정확하고 신뢰할 수 있는 업체 정보를 제공해주세요',
      '서비스 내용과 가격을 명확하게 기재해주세요',
      '연락처와 문의 가능시간을 정확히 입력해주세요',
      '아파트 주민들에게 도움이 되는 서비스를 등록해주세요',
      '허위 정보나 과장된 내용은 피해주세요'
    ],
    titleMaxLength: 100,
    contentMaxLength: 1000,
    titleLabel: "업체명",
    contentLabel: "업체 소개"
  };

  // 카테고리 필드 (extendedFields) - 업체명 위에 위치
  const extendedFields = (
    <CategoryField
      value={formData.category}
      onChange={handleCategoryChange}
    />
  );

  // 연락처와 서비스 목록을 업체명 뒤에 위치 (afterTitleFields)
  const afterTitleFields = (
    <>
      <ContactFields
        contact={formData.contact}
        availableHours={formData.availableHours}
        onContactChange={handleContactChange}
        onAvailableHoursChange={handleAvailableHoursChange}
      />
      
      <ServiceListField
        services={services}
        onServicesChange={handleServicesChange}
      />
    </>
  );

  return (
    <PostWriteForm<ServiceWriteData>
      config={config}
      initialData={formData}
      onDataChange={handleDataChange}
      extendedFields={extendedFields}
      afterTitleFields={afterTitleFields}
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isSubmitting={isSubmitting}
      isEditMode={isEditMode}
    />
  );
}