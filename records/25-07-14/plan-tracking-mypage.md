마이페이지 GA4 추적 구현 계획                                                                                 │ │
│ │                                                                                                               │ │
│ │ 📋 분석 완료 내용                                                                                             │ │
│ │                                                                                                               │ │
│ │ 1. 마이페이지 구현 현황                                                                                       │ │
│ │                                                                                                               │ │
│ │ - 섹션 탭: 작성(write) / 반응(reaction) 두 개 탭                                                              │ │
│ │ - 섹션 선택 이벤트: setActivityTab('write'|'reaction') 함수 호출                                              │ │
│ │ - 아이템 클릭 이벤트: <Link to={item.route_path}> 를 통한 라우터 네비게이션                                   │ │
│ │ - 활동 아이템 토글: toggleActivityDetail(activityType) 함수 호출                                              │ │
│ │                                                                                                               │ │
│ │ 2. 기존 GA4 아키텍처 확인                                                                                     │ │
│ │                                                                                                               │ │
│ │ - AnalyticsService 클래스: 완전한 GA4 추적 시스템 구현                                                        │ │
│ │ - 환경별 측정 ID: 개발/스테이징/프로덕션 환경별 자동 선택                                                     │ │
│ │ - 30개 이상 전문화된 추적 메서드: 페이지별 댓글, 반응, 전환 이벤트 추적                                       │ │
│ │                                                                                                               │ │
│ │ 🎯 구현할 추적 이벤트                                                                                         │ │
│ │                                                                                                               │ │
│ │ 1. 섹션 선택 이벤트 (2개)                                                                                     │ │
│ │                                                                                                               │ │
│ │ - mypage_section_select - 작성/반응 섹션 선택 추적                                                            │ │
│ │ - 파라미터: section_type, previous_section, page_location                                                     │ │
│ │                                                                                                               │ │
│ │ 2. 활동 아이템 토글 이벤트 (1개)                                                                              │ │
│ │                                                                                                               │ │
│ │ - mypage_activity_toggle - 활동 아이템 접기/펼치기 추적                                                       │ │
│ │ - 파라미터: activity_type, is_expanded, item_count                                                            │ │
│ │                                                                                                               │ │
│ │ 3. 아이템 클릭 이벤트 (12개)                                                                                  │ │
│ │                                                                                                               │ │
│ │ 작성 섹션 (6개):                                                                                              │ │
│ │ - mypage_written_post_click - 작성한 게시글 클릭                                                              │ │
│ │ - mypage_written_comment_click - 작성한 댓글 클릭                                                             │ │
│ │ - mypage_service_inquiry_click - 서비스 문의 클릭                                                             │ │
│ │ - mypage_service_review_click - 서비스 후기 클릭                                                              │ │
│ │ - mypage_written_item_click - 통합 작성 아이템 클릭                                                           │ │
│ │                                                                                                               │ │
│ │ 반응 섹션 (6개):                                                                                              │ │
│ │ - mypage_liked_post_click - 추천한 게시글 클릭                                                                │ │
│ │ - mypage_disliked_post_click - 비추천한 게시글 클릭                                                           │ │
│ │ - mypage_bookmarked_post_click - 저장한 게시글 클릭                                                           │ │
│ │ - mypage_reaction_item_click - 통합 반응 아이템 클릭                                                          │ │
│ │                                                                                                               │ │
│ │ 4. 세부 파라미터 설계                                                                                         │ │
│ │                                                                                                               │ │
│ │ - page_type: board, property_information, moving_services, expert_tips                                        │ │
│ │ - item_type: post, comment, service_inquiry, service_review                                                   │ │
│ │ - item_id: 게시글/댓글 ID                                                                                     │ │
│ │ - target_route: 이동할 경로                                                                                   │ │
│ │ - interaction_context: mypage_write, mypage_reaction                                                          │ │
│ │                                                                                                               │ │
│ │ 🔧 구현 방법                                                                                                  │ │
│ │                                                                                                               │ │
│ │ 1. AnalyticsService 확장                                                                                      │ │
│ │                                                                                                               │ │
│ │ - 마이페이지 전용 추적 메서드 추가                                                                            │ │
│ │ - 기존 아키텍처와 일관성 유지                                                                                 │ │
│ │ - 환경별 측정 ID 자동 선택 활용                                                                               │ │
│ │                                                                                                               │ │
│ │ 2. 마이페이지 컴포넌트 수정                                                                                   │ │
│ │                                                                                                               │ │
│ │ - 섹션 선택 시 GA4 이벤트 호출                                                                                │ │
│ │ - 아이템 클릭 시 GA4 이벤트 호출                                                                              │ │
│ │ - 활동 아이템 토글 시 GA4 이벤트 호출                                                                         │ │
│ │                                                                                                               │ │
│ │ 3. 테스트 구현                                                                                                │ │
│ │                                                                                                               │ │
│ │ - 유닛 테스트 추가                                                                                            │ │
│ │ - 실제 GA4 이벤트 전송 확인                                                                                   │ │
│ │ - 개발 환경에서 콘솔 로그 확인                                                                                │ │
│ │                                                                                                               │ │
│ │ 📁 수정할 파일들                                                                                              │ │
│ │                                                                                                               │ │
│ │ 1. frontend/app/lib/analytics-service.ts - 마이페이지 추적 메서드 추가                                        │ │
│ │ 2. frontend/app/routes/mypage.tsx - GA4 이벤트 호출 추가                                                      │ │
│ │ 3. frontend/tests/unit/lib/analytics.test.ts - 테스트 케이스 추가                                             │ │
│ │                                                                                                               │ │
│ │ 🚀 예상 결과                                                                                                  │ │
│ │                                                                                                               │ │
│ │ - 마이페이지 사용자 행동 완전 추적                                                                            │ │
│ │ - 작성/반응 섹션 사용 패턴 분석 가능                                                                          │ │
│ │ - 개별 콘텐츠 접근 빈도 측정 가능                                                                             │ │
│ │ - 사용자 참여도 및 콘텐츠 인기도 분석 가능  