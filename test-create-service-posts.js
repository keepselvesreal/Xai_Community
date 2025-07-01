// 테스트용 서비스 Posts 생성 스크립트
const API_BASE = 'http://localhost:8000';

async function createServicePost(serviceData) {
  const postData = {
    title: serviceData.company.name,
    content: JSON.stringify(serviceData),
    service: 'residential_community',
    metadata: {
      type: 'moving services',
      category: serviceData.category,
      tags: [serviceData.category, '업체', '서비스'],
      visibility: 'public'
    }
  };

  console.log('Creating service post:', postData.title);
  
  const response = await fetch(`${API_BASE}/api/posts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(postData)
  });

  const result = await response.json();
  console.log('Response:', result);
  return result;
}

async function main() {
  console.log('Creating test service posts...\n');

  // 서비스 1: 빠른이사 서비스
  const service1 = {
    company: {
      name: '빠른이사 서비스',
      contact: '02-3456-7890',
      availableHours: '평일 08:00-20:00',
      description: '빠르고 안전한 이사 서비스를 제공합니다.'
    },
    services: [
      { name: '원룸 이사', price: 150000, description: '원룸 이사 서비스' },
      { name: '투룸 이사', price: 250000, specialPrice: 200000, description: '투룸 이사 서비스' }
    ],
    category: '이사'
  };

  // 서비스 2: 청준 청소 대행
  const service2 = {
    company: {
      name: '청준 청소 대행',
      contact: '02-8765-4321',
      availableHours: '평일 09:00-18:00',
      description: '아파트 전문 청소 서비스를 제공합니다.'
    },
    services: [
      { name: '의류 청소', price: 35000, description: '의류 전문 청소' },
      { name: '침구류 청소', price: 45000, description: '침구류 전문 청소' }
    ],
    category: '청소'
  };

  // 서비스 3: 시원한 에어컨 서비스
  const service3 = {
    company: {
      name: '시원한 에어컨 서비스',
      contact: '02-9876-5432',
      availableHours: '평일 09:00-18:00',
      description: '에어컨 전문 설치, 수리, 청소 서비스를 제공합니다.'
    },
    services: [
      { name: '에어컨 청소', price: 80000, description: '에어컨 전문 청소' },
      { name: '에어컨 설치', price: 120000, specialPrice: 100000, description: '에어컨 설치 서비스' }
    ],
    category: '에어컨'
  };

  try {
    await createServicePost(service1);
    await createServicePost(service2);
    await createServicePost(service3);
    
    console.log('\n✅ All service posts created successfully!');
    
    // 생성된 posts 확인
    console.log('\nFetching created posts...');
    const response = await fetch(`${API_BASE}/api/posts?service=residential_community&type=moving%20services`);
    const result = await response.json();
    console.log('Created posts:', JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.error('Error creating service posts:', error);
  }
}

main();