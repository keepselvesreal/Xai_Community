import type { Post } from '~/types';

// 다양한 길이의 제목들
const titleTemplates = [
  "짧은 제목",
  "중간 길이의 제목입니다",
  "이것은 좀 더 긴 제목의 예시입니다",
  "매우 긴 제목의 예시로써 게시글 제목이 한 줄을 넘어갈 정도로 길어서 ellipsis 처리가 되어야 하는 상황을 테스트하기 위한 제목입니다",
  "아파트 입주 체크리스트 공유합니다",
  "관리비 절약 노하우 대방출!",
  "우리 아파트 수영장 이용 후기",
  "주차장 에티켓에 대해 이야기해봐요",
  "인테리어 공사 전 알아두면 좋은 것들",
  "아이들 놀이터 안전 관리 제안",
  "겨울철 보일러 관리 방법",
  "엘리베이터 고장 시 대처 방법",
  "분리수거 올바른 방법 정리",
  "아파트 생활 첫 달 소감",
  "층간소음 문제 해결 방법",
  "택배 보관함 사용 매너",
  "공동 현관 출입 시 주의사항",
  "관리사무소 이용 안내",
  "아파트 헬스장 예약 방법",
  "지하주차장 안전 운전 팁",
  "음식물 쓰레기 처리 방법",
  "동네 맛집 추천합니다",
  "아파트 단지 내 산책로 소개",
  "반려동물 키우기 주의사항",
  "베란다 가드닝 시작하기",
  "홈 시큐리티 설치 후기",
  "아파트 화재 대피 요령",
  "정전 시 대처 방법",
  "수도 검침 날짜 안내",
  "관리비 고지서 확인 방법"
];

// 다양한 카테고리들
const categories = [
  '일반',
  '입주 정보',
  '생활 정보',
  '이야기',
  '입주정보',
  '생활정보',
  '공지사항',
  '질문/답변',
  '후기/리뷰',
  '정보공유'
];

// 다양한 길이의 태그들
const tagTemplates = [
  ['짧은태그'],
  ['태그1', '태그2'],
  ['긴태그이름', '매우긴태그이름테스트'],
  ['태그1', '태그2', '태그3'],
  ['태그1', '태그2', '태그3', '태그4'],
  ['태그1', '태그2', '태그3', '태그4', '태그5'],
  ['입주', '체크리스트', '준비사항'],
  ['관리비', '절약', '팁'],
  ['수영장', '후기', '운동'],
  ['주차', '에티켓', '매너'],
  ['인테리어', '공사', '팁'],
  ['놀이터', '안전', '아이'],
  ['보일러', '겨울', '관리'],
  ['엘리베이터', '고장', '대처'],
  ['분리수거', '환경', '방법'],
  ['첫달', '소감', '적응'],
  ['층간소음', '해결', '방법'],
  ['택배', '보관함', '매너'],
  ['출입', '보안', '주의'],
  ['관리사무소', '이용', '안내'],
  ['헬스장', '예약', '운동'],
  ['주차장', '안전', '운전'],
  ['음식물', '쓰레기', '처리'],
  ['맛집', '추천', '동네'],
  ['산책로', '운동', '건강'],
  ['반려동물', '키우기', '주의'],
  ['베란다', '가드닝', '식물'],
  ['보안', '시큐리티', '안전'],
  ['화재', '대피', '안전'],
  ['정전', '대처', '비상']
];

// 다양한 길이의 작성자명들
const authorNames = [
  '김철수',
  '이영희',
  '박민수',
  '최정아',
  '정수현',
  '한승우',
  '조미영',
  '장동건',
  '윤서연',
  '임재훈',
  '매우긴사용자이름테스트용',
  '짧은이름',
  '중간길이사용자명',
  '아파트101호',
  '동네주민',
  '관리비절약왕',
  '수영장매니아',
  '주차장킹',
  '인테리어맘',
  '안전지킴이',
  '환경지킴이',
  '신입주민',
  '베테랑주민',
  '아파트사랑',
  '우리동네지킴이'
];

// 목 데이터 생성 함수
export function generateMockPosts(count: number): Post[] {
  const posts: Post[] = [];
  
  for (let i = 1; i <= count; i++) {
    const titleIndex = (i - 1) % titleTemplates.length;
    const categoryIndex = (i - 1) % categories.length;
    const tagIndex = (i - 1) % tagTemplates.length;
    const authorIndex = (i - 1) % authorNames.length;
    
    // 생성 시간을 다양하게 만들기 (최근 30일 내)
    const daysAgo = Math.floor(Math.random() * 30);
    const hoursAgo = Math.floor(Math.random() * 24);
    const minutesAgo = Math.floor(Math.random() * 60);
    const createdAt = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000 - hoursAgo * 60 * 60 * 1000 - minutesAgo * 60 * 1000);
    
    // 통계 데이터를 다양하게 생성
    const baseViews = Math.floor(Math.random() * 5000) + 50;
    const post: Post = {
      id: `mock-post-${i}`,
      title: titleTemplates[titleIndex],
      content: `${titleTemplates[titleIndex]}의 내용입니다. 이것은 테스트용 더미 내용입니다.`,
      slug: `mock-post-${i}`,
      created_at: createdAt.toISOString(),
      updated_at: createdAt.toISOString(),
      author: {
        id: `author-${authorIndex}`,
        display_name: authorNames[authorIndex],
        user_handle: `user${authorIndex}`,
        name: authorNames[authorIndex]
      },
      metadata: {
        category: categories[categoryIndex],
        tags: tagTemplates[tagIndex],
        type: 'board'
      },
      stats: {
        view_count: baseViews,
        like_count: Math.floor(baseViews * 0.05) + Math.floor(Math.random() * 50),
        dislike_count: Math.floor(baseViews * 0.01) + Math.floor(Math.random() * 5),
        comment_count: Math.floor(baseViews * 0.03) + Math.floor(Math.random() * 20),
        bookmark_count: Math.floor(baseViews * 0.02) + Math.floor(Math.random() * 10)
      }
    };
    
    posts.push(post);
  }
  
  return posts;
}