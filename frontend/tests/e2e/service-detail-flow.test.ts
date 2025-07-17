import { test, expect, Page } from '@playwright/test';

// Mock 데이터 설정
const mockService = {
  id: 'service-1',
  name: '깔끔한 이사 서비스',
  category: '이사',
  rating: 4.5,
  contact: {
    phone: '010-1234-5678',
    email: 'contact@cleanmove.co.kr',
    address: '서울시 강남구 테헤란로 123',
    hours: '09:00 ~ 18:00',
  },
  services: [
    {
      name: '원룸 이사',
      price: '60000',
      description: '원룸 전체 이사',
    },
  ],
  serviceStats: {
    views: 1250,
    bookmarks: 89,
    inquiries: 23,
    reviews: 45,
  },
};

const mockPost = {
  id: 'post-1',
  title: '깔끔한 이사 서비스',
  content: '전문 이사 서비스입니다.',
  slug: 'test-service',
  author: {
    id: 'user-1',
    user_handle: 'cleanmove',
    display_name: '깔끔한 이사',
    email: 'info@cleanmove.com',
  },
  author_id: 'user-1',
  created_at: '2024-01-01T00:00:00Z',
  metadata: {
    type: 'moving_services',
    category: '이사',
  },
  stats: {
    view_count: 1250,
    bookmark_count: 89,
    comment_count: 23,
  },
  status: 'published',
};

// API 모킹 설정
async function setupMocks(page: Page) {
  // 서비스 상세 API 모킹
  await page.route('**/api/posts/test-service', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: mockPost,
      }),
    });
  });

  // 댓글 배치 조회 API 모킹
  await page.route('**/api/posts/test-service/comments/batch', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: [
          {
            id: 'comment-1',
            content: '문의 내용입니다.',
            author: {
              id: 'user-2',
              user_handle: 'customer',
              display_name: '고객',
              email: 'customer@example.com',
            },
            created_at: '2024-01-01T00:00:00Z',
            metadata: {
              subtype: 'service_inquiry',
            },
          },
        ],
      }),
    });
  });

  // 북마크 API 모킹
  await page.route('**/api/posts/test-service/bookmark', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: { bookmark_count: 90 },
      }),
    });
  });

  // convertPostToService 모킹 (클라이언트 사이드)
  await page.addInitScript(() => {
    window.mockService = {
      id: 'service-1',
      name: '깔끔한 이사 서비스',
      category: '이사',
      rating: 4.5,
      contact: {
        phone: '010-1234-5678',
        email: 'contact@cleanmove.co.kr',
        address: '서울시 강남구 테헤란로 123',
        hours: '09:00 ~ 18:00',
      },
      services: [
        {
          name: '원룸 이사',
          price: '60000',
          description: '원룸 전체 이사',
        },
      ],
      serviceStats: {
        views: 1250,
        bookmarks: 89,
        inquiries: 23,
        reviews: 45,
      },
    };
  });
}

test.describe('서비스 상세 페이지 E2E 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await setupMocks(page);
  });

  test('서비스 상세 페이지 전체 플로우가 정상 작동해야 한다', async ({ page }) => {
    // 서비스 상세 페이지 방문
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeVisible();
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 서비스 정보 확인
    await expect(page.getByText('깔끔한 이사 서비스')).toBeVisible();
    await expect(page.getByText('010-1234-5678')).toBeVisible();
    await expect(page.getByText('원룸 이사')).toBeVisible();
    await expect(page.getByText('60,000원')).toBeVisible();

    // 통계 정보 확인
    await expect(page.getByText('1,250')).toBeVisible(); // 조회수
    await expect(page.getByText('89')).toBeVisible(); // 북마크
    await expect(page.getByText('23')).toBeVisible(); // 문의
    await expect(page.getByText('45')).toBeVisible(); // 후기

    // 연락처 정보 확인
    await expect(page.getByText('서울시 강남구 테헤란로 123')).toBeVisible();
    await expect(page.getByText('09:00 ~ 18:00')).toBeVisible();
  });

  test('북마크 기능이 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 북마크 버튼 클릭
    const bookmarkButton = page.getByLabelText('북마크');
    await bookmarkButton.click();

    // API 호출 확인 (네트워크 요청 모니터링)
    const requestPromise = page.waitForRequest('**/api/posts/test-service/bookmark');
    await bookmarkButton.click();
    await requestPromise;

    // 성공 메시지 확인
    await expect(page.getByText('북마크 처리가 완료되었습니다')).toBeVisible();
  });

  test('고정 북마크 버튼이 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 고정 북마크 버튼 확인
    const fixedBookmarkButton = page.locator('button').filter({ hasText: '🔖' }).first();
    await expect(fixedBookmarkButton).toBeVisible();

    // 고정 북마크 버튼 클릭
    await fixedBookmarkButton.click();

    // API 호출 확인
    const requestPromise = page.waitForRequest('**/api/posts/test-service/bookmark');
    await requestPromise;
  });

  test('댓글 시스템이 정상 통합되어야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 댓글 섹션 확인
    await expect(page.getByTestId('comment-section')).toBeVisible();
    await expect(page.getByTestId('comment-page-type')).toHaveText('moving_services');

    // 기존 댓글 확인
    await expect(page.getByText('문의 내용입니다.')).toBeVisible();
    await expect(page.getByText('고객')).toBeVisible();
  });

  test('모바일 반응형이 정상 작동해야 한다', async ({ page }) => {
    // 모바일 뷰포트 설정
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 모바일에서 콘텐츠 확인
    await expect(page.getByText('깔끔한 이사 서비스')).toBeVisible();
    await expect(page.getByText('010-1234-5678')).toBeVisible();

    // 고정 북마크 버튼이 모바일에서도 보이는지 확인
    const fixedBookmarkButton = page.locator('button').filter({ hasText: '🔖' }).first();
    await expect(fixedBookmarkButton).toBeVisible();
  });

  test('네비게이션이 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // '목록으로' 버튼 클릭
    const backButton = page.getByText('← 목록으로');
    await expect(backButton).toBeVisible();
    await backButton.click();

    // 목록 페이지로 이동 확인
    await expect(page).toHaveURL('/services');
  });

  test('전화 링크가 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 전화번호 링크 확인
    const phoneLink = page.getByText('010-1234-5678');
    await expect(phoneLink).toBeVisible();
    await expect(phoneLink).toHaveAttribute('href', 'tel:010-1234-5678');
  });

  test('이메일 링크가 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 이메일 링크 확인
    const emailLink = page.getByText('contact@cleanmove.co.kr');
    await expect(emailLink).toBeVisible();
    await expect(emailLink).toHaveAttribute('href', 'mailto:contact@cleanmove.co.kr');
  });

  test('404 상태를 정상 처리해야 한다', async ({ page }) => {
    // 404 API 응답 설정
    await page.route('**/api/posts/nonexistent-service', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Not found',
        }),
      });
    });

    await page.goto('/moving-services/nonexistent-service');

    // 404 메시지 확인
    await expect(page.getByText('서비스를 찾을 수 없습니다')).toBeVisible();
    await expect(page.getByText('서비스 목록으로 돌아가기')).toBeVisible();

    // 목록으로 돌아가기 버튼 클릭
    const backButton = page.getByText('서비스 목록으로 돌아가기');
    await backButton.click();

    // 목록 페이지로 이동 확인
    await expect(page).toHaveURL('/services');
  });

  test('접근성 기능이 정상 작동해야 한다', async ({ page }) => {
    await page.goto('/moving-services/test-service');

    // 로딩 완료 대기
    await expect(page.getByTestId('loading-skeleton')).toBeHidden();

    // 키보드 네비게이션 테스트
    const bookmarkButton = page.getByLabelText('북마크');
    await bookmarkButton.focus();
    await expect(bookmarkButton).toBeFocused();

    // Tab 키로 다음 요소로 이동
    await page.keyboard.press('Tab');
    
    // aria-label 확인
    await expect(page.getByLabelText('북마크')).toBeVisible();
    await expect(page.getByLabelText('좋아요')).toBeVisible();
    await expect(page.getByLabelText('싫어요')).toBeVisible();
  });
});