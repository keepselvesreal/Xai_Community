// 수동 테스트 스크립트 - 브라우저 콘솔에서 실행
// 서비스 목록 페이지의 실시간 통계 반영 테스트

console.log('🧪 서비스 목록 실시간 통계 테스트 시작');

// 1. 현재 서비스 목록에서 첫 번째 서비스의 북마크 수 확인
function getCurrentBookmarkCount() {
  const firstServiceElement = document.querySelector('[class*="bg-white border border-gray-200"]');
  if (firstServiceElement) {
    const bookmarkElement = firstServiceElement.querySelector('span:contains("관심")');
    if (bookmarkElement) {
      const bookmarkText = bookmarkElement.textContent;
      const count = parseInt(bookmarkText.match(/\d+/)?.[0] || '0');
      console.log('📊 현재 북마크 수:', count);
      return count;
    }
  }
  console.log('❌ 북마크 요소를 찾을 수 없음');
  return 0;
}

// 2. 첫 번째 서비스 카드 클릭하여 상세 페이지로 이동
function navigateToFirstService() {
  console.log('🎯 첫 번째 서비스 카드 클릭 시도');
  const firstServiceCard = document.querySelector('[class*="bg-white border border-gray-200"]');
  if (firstServiceCard) {
    console.log('✅ 서비스 카드 발견, 클릭합니다');
    firstServiceCard.click();
    return true;
  } else {
    console.log('❌ 서비스 카드를 찾을 수 없음');
    return false;
  }
}

// 3. 서비스 상세 페이지에서 북마크 토글 후 목록으로 돌아가기
function testBookmarkToggle() {
  console.log('🔖 북마크 토글 테스트');
  
  // 북마크 버튼 찾기
  const bookmarkButton = document.querySelector('button:contains("저장")');
  if (bookmarkButton) {
    console.log('✅ 북마크 버튼 발견, 클릭합니다');
    bookmarkButton.click();
    
    // 3초 후 목록으로 돌아가기
    setTimeout(() => {
      console.log('🔙 목록 페이지로 돌아갑니다');
      window.history.back();
      
      // 2초 후 북마크 수 재확인
      setTimeout(() => {
        const newCount = getCurrentBookmarkCount();
        console.log('📊 업데이트된 북마크 수:', newCount);
        console.log('✅ 실시간 반영 테스트 완료');
      }, 2000);
    }, 3000);
  } else {
    console.log('❌ 북마크 버튼을 찾을 수 없음');
  }
}

// 테스트 실행
const initialCount = getCurrentBookmarkCount();
console.log('📊 초기 북마크 수:', initialCount);

// 사용법 안내
console.log('🚀 테스트 실행 방법:');
console.log('1. navigateToFirstService() - 첫 번째 서비스로 이동');
console.log('2. 상세 페이지에서 testBookmarkToggle() 실행');
console.log('3. 목록으로 돌아와서 getCurrentBookmarkCount() 재실행');