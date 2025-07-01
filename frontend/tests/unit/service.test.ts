/**
 * ServicePost 타입 정의 테스트 (TDD RED 단계)
 * 
 * 이 테스트는 구조화된 서비스-가격 데이터를 위한 타입이 올바르게 정의되는지 검증합니다.
 */

// Vitest globals are available through vitest.config.ts

// GREEN: 구현된 타입과 함수 테스트
describe('ServicePost Types', () => {
  test('ServicePost 타입이 올바른 구조를 가져야 한다', async () => {
    const { parseServicePost, serializeServicePost } = await import('../../app/types/service-types');
    
    const testData = {
      company: {
        name: "테스트 업체",
        contact: "02-1234-5678",
        availableHours: "09:00-18:00",
        description: "테스트 설명"
      },
      services: [
        {
          name: "테스트 서비스",
          price: 100000,
          specialPrice: 80000,
          description: "테스트 서비스 설명"
        }
      ]
    };

    const serialized = serializeServicePost(testData);
    const parsed = parseServicePost(serialized);
    
    expect(parsed).toEqual(testData);
  });

  test('parseServicePost가 유효한 JSON을 파싱해야 한다', async () => {
    const { parseServicePost } = await import('../../app/types/service-types');
    
    const validJson = `{
      "company": {
        "name": "테스트 업체",
        "contact": "02-1234-5678",
        "availableHours": "09:00-18:00", 
        "description": "테스트 설명"
      },
      "services": [
        {
          "name": "원룸 이사",
          "price": 150000,
          "specialPrice": 120000
        }
      ]
    }`;

    const result = parseServicePost(validJson);
    
    expect(result.company.name).toBe("테스트 업체");
    expect(result.services).toHaveLength(1);
    expect(result.services[0].price).toBe(150000);
  });

  test('parseServicePost가 잘못된 JSON에서 에러를 던져야 한다', async () => {
    const { parseServicePost } = await import('../../app/types/service-types');
    
    expect(() => {
      parseServicePost('invalid json');
    }).toThrow('Invalid ServicePost JSON format');
  });

  test('serializeServicePost가 유효한 JSON 문자열을 생성해야 한다', async () => {
    const { serializeServicePost } = await import('../../app/types/service-types');
    
    const testData = {
      company: {
        name: "테스트 업체",
        contact: "02-1234-5678",
        availableHours: "09:00-18:00",
        description: "테스트 설명"
      },
      services: [
        {
          name: "원룸 이사", 
          price: 150000
        }
      ]
    };

    const result = serializeServicePost(testData);
    
    expect(typeof result).toBe('string');
    expect(() => JSON.parse(result)).not.toThrow();
  });

  test('ServiceItemWithPrice에서 specialPrice는 선택적이어야 한다', async () => {
    const { parseServicePost } = await import('../../app/types/service-types');
    
    const jsonWithoutSpecialPrice = `{
      "company": {
        "name": "테스트 업체",
        "contact": "02-1234-5678",
        "availableHours": "09:00-18:00",
        "description": "테스트 설명"
      },
      "services": [
        {
          "name": "기본 서비스",
          "price": 100000
        }
      ]
    }`;

    const result = parseServicePost(jsonWithoutSpecialPrice);
    
    expect(result.services[0].specialPrice).toBeUndefined();
    expect(result.services[0].price).toBe(100000);
  });
});

// 타입 체크를 위한 컴파일 테스트 (실행되지 않는 코드)
function typeCheck() {
  // 이 함수는 실행되지 않지만 TypeScript 컴파일러가 타입을 체크함
  
  // @ts-expect-error - ServicePost 타입이 아직 정의되지 않음
  const servicePost: ServicePost = null as any;
  
  // @ts-expect-error - CompanyInfo 타입이 아직 정의되지 않음  
  const company: CompanyInfo = null as any;
  
  // @ts-expect-error - ServiceItemWithPrice 타입이 아직 정의되지 않음
  const service: ServiceItemWithPrice = null as any;
  
  return { servicePost, company, service };
}