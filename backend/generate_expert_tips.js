#!/usr/bin/env node
/**
 * Expert Tips Test Data Generator (JavaScript Version)
 * 
 * This script generates expert tips test data using the FastAPI REST endpoints.
 * It creates posts with metadata.type = "expert_tips" through HTTP API calls.
 */

const API_BASE = 'http://localhost:8000';
const API_ENDPOINTS = {
  register: `${API_BASE}/api/auth/register`,
  login: `${API_BASE}/api/auth/login`,
  posts: `${API_BASE}/api/posts`,
  search: `${API_BASE}/api/posts/search`
};

// Expert tip categories and their related keywords
const EXPERT_CATEGORIES = {
  "인테리어": ["방 꾸미기", "가구 배치", "색상 선택", "조명", "수납", "소품"],
  "생활팁": ["청소", "정리정돈", "절약", "효율성", "생활습관", "건강"],
  "요리": ["레시피", "요리법", "식재료", "주방용품", "건강식", "간편식"],
  "육아": ["아이 돌보기", "교육", "놀이", "건강관리", "소통", "성장"],
  "반려동물": ["반려견", "반려묘", "건강관리", "훈련", "용품", "놀이"],
  "가드닝": ["식물 키우기", "베란다", "화분", "물주기", "흙", "햇빛"],
  "DIY": ["만들기", "수리", "조립", "도구", "재료", "창작"],
  "건강": ["운동", "스트레칭", "영양", "수면", "스트레스", "관리"],
  "재정관리": ["절약", "투자", "가계부", "적금", "보험", "계획"],
  "취미": ["독서", "음악", "영화", "게임", "수집", "체험"]
};

// Expert profiles for generating realistic data
const EXPERT_PROFILES = [
  { name: "김민수", title: "인테리어 디자이너", specialties: ["인테리어", "DIY"] },
  { name: "박영희", title: "생활컨설턴트", specialties: ["생활팁"] },
  { name: "이준호", title: "요리연구가", specialties: ["요리", "건강"] },
  { name: "최수진", title: "육아전문가", specialties: ["육아"] },
  { name: "정민아", title: "반려동물 훈련사", specialties: ["반려동물", "건강"] },
  { name: "홍길동", title: "가드닝 전문가", specialties: ["가드닝", "생활팁"] },
  { name: "서지혜", title: "DIY 크리에이터", specialties: ["DIY", "인테리어"] },
  { name: "강태우", title: "헬스 트레이너", specialties: ["건강"] },
  { name: "윤소영", title: "재정관리 전문가", specialties: ["재정관리"] },
  { name: "한승우", title: "취미생활 큐레이터", specialties: ["취미", "생활팁"] }
];

// Expert tip content templates
const EXPERT_TIP_TEMPLATES = {
  "인테리어": [
    {
      title: "작은 방을 넓어 보이게 하는 {tip_detail} 방법",
      content: `작은 방을 넓어 보이게 하려면 다음과 같은 방법을 사용해보세요:

## 1. 밝은 색상 활용
벽지와 가구를 밝은 색으로 선택하여 공간감을 확대시킵니다. 흰색, 베이지, 연한 회색 등이 효과적입니다.

## 2. 거울 배치
창문 맞은편에 큰 거울을 설치하여 자연광을 반사시키고 공간을 두 배로 넓어 보이게 합니다.

## 3. 수직 공간 활용
높은 선반과 벽걸이 수납을 이용해 바닥 공간을 확보하고, 시선을 위로 끌어올립니다.

## 4. 투명 가구 사용
유리나 아크릴 소재의 가구를 사용하여 시각적 부담을 줄이고 개방감을 조성합니다.

이러한 방법들을 조합하여 사용하면 좁은 공간도 훨씬 넓고 쾌적하게 느낄 수 있습니다.`,
      keywords: ["공간 확장", "밝은 색상", "거울", "수납"]
    },
    {
      title: "아파트 현관 {tip_detail} 인테리어 꿀팁",
      content: `아파트 현관을 더욱 실용적이고 예쁘게 만들어보세요:

## 공간 활용 팁
- **벽면 활용**: 현관 벽면에 후크를 설치하여 가방이나 우산을 걸 수 있게 합니다
- **상단 공간**: 신발장 위 공간에 작은 화분이나 소품을 배치합니다
- **거울 설치**: 전신거울을 설치하여 외출 전 마지막 점검을 할 수 있게 합니다

## 분위기 연출
- **조명**: 따뜻한 색온도의 조명을 사용하여 집에 들어오는 순간부터 편안함을 느끼게 합니다
- **계절 소품**: 계절에 맞는 소품으로 포인트를 주어 항상 새로운 느낌을 연출합니다
- **향**: 향초나 디퓨저로 좋은 향을 연출하여 후각적 만족도를 높입니다

현관은 집의 첫인상을 결정하는 중요한 공간이니 신경 써서 꾸며보세요!`,
      keywords: ["현관 인테리어", "수납", "조명", "소품"]
    }
  ],
  "생활팁": [
    {
      title: "전기요금 {tip_detail}% 절약하는 실용적인 방법",
      content: `전기요금을 크게 절약할 수 있는 실용적인 방법들을 소개합니다:

## 가전제품 효율적 사용법

### 에어컨 관리
- **적정온도 설정**: 여름 26-28°C, 겨울 18-20°C 유지
- **필터 청소**: 월 1회 필터 청소로 효율성 향상
- **문 닫기**: 사용 시 문과 창문을 닫아 냉난방 효율 극대화

### 냉장고 관리
- **문 여는 횟수 줄이기**: 필요한 것을 미리 정리하여 한 번에 꺼내기
- **적정 온도 유지**: 냉장실 3-4°C, 냉동실 -18°C 설정

### 대기전력 차단
- **멀티탭 스위치 활용**: 사용하지 않는 전자제품의 플러그 뽑기
- **LED 전구 교체**: 백열전구 대비 80% 전력 절약

이 방법들을 실천하면 월 전기요금을 20-30% 절약할 수 있습니다!`,
      keywords: ["전기요금", "절약", "가전제품", "생활습관"]
    }
  ],
  "요리": [
    {
      title: "초보자도 실패없는 {tip_detail} 요리법",
      content: `요리 초보자도 쉽게 따라할 수 있는 간단한 요리법을 소개합니다:

## 기본 준비사항

### 필수 도구
- **기본 도구**: 도마, 칼, 프라이팬, 냄비
- **계량 도구**: 계량컵, 계량스푼
- **보조 도구**: 뒤집개, 국자, 집게

### 기본 재료 (항상 준비)
- **조미료**: 소금, 후추, 간장, 식용유
- **양념**: 마늘, 양파, 생강

## 실패하지 않는 요리 순서

### 1단계: 계획 세우기
- **메뉴 선정**: 간단한 요리부터 시작
- **재료 준비**: 모든 재료를 미리 손질하고 계량

### 2단계: 기본 조리법 익히기
- **중간 불 사용**: 처음에는 강불보다 중간 불로 천천히
- **간 보기**: 조리 중간중간 맛을 보며 간 조절

## 성공을 위한 꿀팁
- **레시피 정확히 따르기**: 처음에는 창의적 변화 자제
- **서두르지 않기**: 천천히 차근차근 진행

한 번 성공하면 다음부터는 자신만의 변화를 줄 수 있어요!`,
      keywords: ["초보 요리", "레시피", "조리법", "간단"]
    }
  ],
  "건강": [
    {
      title: "하루 10분 {tip_detail} 운동으로 건강 챙기기",
      content: `바쁜 일상 속에서도 할 수 있는 간단한 운동법을 소개합니다:

## 시간대별 운동 계획

### 아침 운동 (5분)
1. **목과 어깨 스트레칭** (2분)
   - 목을 좌우, 앞뒤로 천천히 돌리기
   - 어깨를 위아래, 앞뒤로 돌리기

2. **제자리 걷기** (2분)
   - 무릎을 높이 올리며 제자리에서 걷기

3. **심호흡** (1분)
   - 깊게 숨을 들이마시고 천천히 내쉬기

### 점심 운동 (3분)
- 의자에 앉아 다리 들어 올리기
- 어깨 돌리기, 목 스트레칭

### 저녁 운동 (2분)
- 간단한 요가 자세
- 복부 운동 (플랭크 30초 x 2세트)

## 운동 효과
- 혈액 순환 개선
- 스트레스 해소
- 수면의 질 개선

건강한 습관을 만들어 더 활기찬 하루를 보내세요!`,
      keywords: ["간단 운동", "건강 관리", "스트레칭", "일상"]
    }
  ]
};

// Utility functions
function getRandomElement(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function getRandomElements(array, count) {
  const shuffled = array.sort(() => 0.5 - Math.random());
  return shuffled.slice(0, Math.min(count, array.length));
}

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomDate(daysAgo) {
  const now = new Date();
  const pastDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));
  return pastDate.toISOString();
}

// Expert Tips Generator Class
class ExpertTipsGenerator {
  constructor() {
    this.authToken = null;
  }

  async createTestUser() {
    const userData = {
      email: "expert_tips_admin@example.com",
      user_handle: "expert_admin",
      name: "Expert Tips Admin",
      display_name: "Expert Tips Admin",
      password: "TestPassword123!"
    };

    try {
      // Try to login first (user might already exist)
      const loginResponse = await fetch(API_ENDPOINTS.login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: userData.email,
          password: userData.password
        })
      });

      if (loginResponse.ok) {
        const result = await loginResponse.json();
        this.authToken = result.access_token;
        console.log(`✅ Logged in as existing user: ${userData.email}`);
        return true;
      }
    } catch (error) {
      // Continue to registration if login fails
    }

    // If login failed, try to register
    try {
      const registerResponse = await fetch(API_ENDPOINTS.register, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });

      if (registerResponse.status === 201) {
        console.log(`✅ Registered new user: ${userData.email}`);
        
        // Login after registration
        const loginResponse = await fetch(API_ENDPOINTS.login, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: userData.email,
            password: userData.password
          })
        });

        if (loginResponse.ok) {
          const result = await loginResponse.json();
          this.authToken = result.access_token;
          console.log(`✅ Logged in after registration`);
          return true;
        } else {
          console.log(`❌ Login failed after registration: ${loginResponse.status}`);
          return false;
        }
      } else {
        const errorText = await registerResponse.text();
        console.log(`❌ Registration failed: ${registerResponse.status} - ${errorText}`);
        return false;
      }
    } catch (error) {
      console.log(`❌ Error during user creation: ${error.message}`);
      return false;
    }
  }

  generateExpertTipData(expert, category) {
    const templates = EXPERT_TIP_TEMPLATES[category] || [{
      title: `${category} 전문가 팁`,
      content: `${category} 분야의 전문가로서 실생활에 도움이 되는 실용적인 팁을 제공합니다.

## 핵심 포인트
- 전문가의 경험을 바탕으로 한 검증된 방법
- 누구나 쉽게 따라할 수 있는 실용적인 내용
- 실제 효과를 경험할 수 있는 구체적인 방법

전문가의 조언을 통해 더 나은 결과를 얻어보세요!`,
      keywords: [category, "팁", "전문가"]
    }];

    const template = getRandomElement(templates);
    const keywords = EXPERT_CATEGORIES[category] || [category];
    
    // Generate specific tip details
    const tipDetails = [
      "3가지 핵심", "5단계", "완벽한", "실용적인", "간단한", 
      "효과적인", "전문가의", "검증된", "실전", "꿀"
    ];
    
    const tipDetail = getRandomElement(tipDetails);
    const title = template.title.replace('{tip_detail}', tipDetail);
    
    // Generate tags
    const tags = getRandomElements(keywords, 3);
    
    // Generate view counts and engagement metrics
    const viewsCount = getRandomInt(150, 2500);
    const likesCount = getRandomInt(10, Math.floor(viewsCount * 0.15));
    const savesCount = getRandomInt(5, Math.floor(viewsCount * 0.08));
    
    // Generate creation date (within last 6 months)
    const daysAgo = getRandomInt(1, 180);
    const createdAt = getRandomDate(daysAgo);
    
    // Determine if it's "new" (within last 7 days)
    const isNew = daysAgo <= 7;
    
    return {
      title: title,
      content: template.content,
      service: "residential_community",
      metadata: {
        type: "expert_tips",
        category: category,
        tags: tags,
        expert_name: expert.name,
        expert_title: expert.title,
        views_count: viewsCount,
        likes_count: likesCount,
        saves_count: savesCount,
        is_new: isNew,
        visibility: "public",
        editor_type: "markdown"
      }
    };
  }

  async createExpertTip(tipData) {
    try {
      const response = await fetch(API_ENDPOINTS.posts, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(tipData)
      });

      if (response.status === 201) {
        return true;
      } else {
        const errorText = await response.text();
        console.log(`❌ Failed to create tip '${tipData.title.substring(0, 50)}...': ${response.status} - ${errorText}`);
        return false;
      }
    } catch (error) {
      console.log(`❌ Error creating tip '${tipData.title.substring(0, 50)}...': ${error.message}`);
      return false;
    }
  }

  async generateExpertTips(numTips = 30) {
    const createdTips = [];
    
    for (let i = 0; i < numTips; i++) {
      // Select random expert and category
      const expert = getRandomElement(EXPERT_PROFILES);
      // Choose category from expert's specialties
      const category = getRandomElement(expert.specialties);
      
      // Generate tip data
      const tipData = this.generateExpertTipData(expert, category);
      
      // Create tip via API
      const success = await this.createExpertTip(tipData);
      
      if (success) {
        createdTips.push(tipData);
        console.log(`✅ Created expert tip ${i+1}/${numTips}: ${tipData.title.substring(0, 50)}...`);
      } else {
        console.log(`❌ Failed to create expert tip ${i+1}/${numTips}`);
      }
    }
    
    return createdTips;
  }

  async verifyCreatedTips() {
    try {
      const params = new URLSearchParams({
        metadata_type: "expert_tips",
        page: 1,
        page_size: 50
      });

      const response = await fetch(`${API_ENDPOINTS.posts}?${params}`);
      
      if (response.ok) {
        const result = await response.json();
        const tips = result.items || [];
        
        console.log(`\n📊 Verification Results:`);
        console.log(`   Total expert tips found: ${tips.length}`);
        
        // Analyze by category
        const categories = {};
        const experts = {};
        
        tips.forEach(tip => {
          const metadata = tip.metadata || {};
          const category = metadata.category || "Unknown";
          const expertName = metadata.expert_name || "Unknown";
          
          categories[category] = (categories[category] || 0) + 1;
          experts[expertName] = (experts[expertName] || 0) + 1;
        });
        
        console.log(`   Categories:`, categories);
        console.log(`   Experts:`, experts);
        
        return {
          total_tips: tips.length,
          categories: categories,
          experts: experts,
          tips: tips
        };
      } else {
        console.log(`❌ Verification failed: ${response.status}`);
        return { error: `HTTP ${response.status}` };
      }
    } catch (error) {
      console.log(`❌ Verification failed: ${error.message}`);
      return { error: error.message };
    }
  }
}

// Main function
async function main() {
  console.log("🚀 Expert Tips Test Data Generator (JavaScript Version)");
  console.log("=" * 60);
  
  const generator = new ExpertTipsGenerator();
  
  try {
    // Create and authenticate test user
    console.log("1. Creating and authenticating test user...");
    if (!(await generator.createTestUser())) {
      console.log("❌ Failed to create/authenticate user");
      return;
    }
    
    // Generate expert tips
    console.log("2. Generating expert tips...");
    const numTips = 30; // Generate 30 expert tips
    const createdTips = await generator.generateExpertTips(numTips);
    
    console.log(`\n✅ Successfully created ${createdTips.length} expert tips!`);
    
    // Verify creation
    console.log("3. Verifying created tips...");
    const verification = await generator.verifyCreatedTips();
    
    // Generate summary report
    console.log("\n" + "=".repeat(60));
    console.log("📋 EXPERT TIPS GENERATION SUMMARY");
    console.log("=".repeat(60));
    console.log(`✅ Total tips created: ${createdTips.length}`);
    console.log(`✅ API connection: Success`);
    console.log(`✅ Authentication: Success`);
    console.log(`✅ Verification: ${verification.total_tips || 0} tips found`);
    
    // Show sample tips
    if (createdTips.length > 0) {
      console.log("\n🎯 Sample Expert Tips:");
      createdTips.slice(0, 3).forEach((tip, i) => {
        const metadata = tip.metadata;
        console.log(`\n${i+1}. ${tip.title}`);
        console.log(`   Expert: ${metadata.expert_name} (${metadata.expert_title})`);
        console.log(`   Category: ${metadata.category}`);
        console.log(`   Tags: ${metadata.tags.join(', ')}`);
        console.log(`   Views: ${metadata.views_count}`);
      });
    }
    
    console.log("\n" + "=".repeat(60));
    console.log("🎉 Expert Tips Test Data Generation Complete!");
    console.log("=".repeat(60));
    
  } catch (error) {
    console.log(`\n❌ Error during expert tips generation: ${error.message}`);
    console.error(error);
  }
}

// Run the script
main().catch(console.error);