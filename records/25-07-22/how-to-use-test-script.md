📋 댓글/답글 CRUD 자동화 테스트 스크립트 사용법

  🚀 기본 실행

  # 현재 디렉토리에서 실행 (백엔드 서버가 8000포트에서 실행 중이어야 함)
  cd /home/nadle/projects/Xai_Community/v5/scripts/development/testing
  python board_api_automation_test.py

  ⚙️ 고급 실행 옵션

  # 다른 포트의 백엔드 서버 사용
  python board_api_automation_test.py --base-url http://localhost:3001

  # 다른 포트의 프론트엔드 서버 사용  
  python board_api_automation_test.py --frontend-url http://localhost:3000

  # 둘 다 지정
  python board_api_automation_test.py --base-url http://localhost:3001 --frontend-url http://localhost:3000

  📊 테스트 시나리오

  실행하면 다음과 같은 29개의 종합 테스트가 자동으로 실행됩니다:

  1. 게시글 목록 기능 테스트 (13개)

  - 전체 목록 조회
  - 카테고리별 필터링 (자유게시판, 생활정보, 이야기)
  - 정렬 기능 (최신순, 조회수순, 추천순)
  - 검색 기능 (키워드별)
  - 페이지네이션 테스트

  2. 게시글 CRUD 테스트 (4개)

  - 게시글 작성/조회/수정/삭제

  3. 댓글/답글 CRUD 테스트 (12개) ✨ 새로 추가됨

  - 빈 댓글 목록 조회
  - 댓글 작성
  - 댓글이 있는 목록 조회
  - 답글 작성
  - 답글이 포함된 목록 조회
  - 답글 수정/삭제
  - 댓글 수정/삭제
  - 댓글 반응 (좋아요/싫어요) 테스트

  🔍 테스트 결과 확인

  1. 콘솔 출력

  ✅ 댓글/답글 CRUD 테스트 완료 - 총 12개 테스트

  📊 생성된 데이터:
     - users: 1개
     - posts: 5개
     - comments: 3개

  세션 ID: TEST_20250722_092050_49CF

  2. 브라우저에서 확인

  🌐 브라우저에서 확인:
     - 게시판 목록: http://localhost:5173/board
     - 생성된 게시글들을 직접 확인해보세요!

  3. 세션 데이터 파일

  test_session_TEST_20250722_092050_49CF.json

  🧹 테스트 데이터 정리

  안전한 정리 (Dry-run)

  # 삭제될 데이터 미리보기
  python cleanup_test_data.py TEST_20250722_092050_49CF

  실제 삭제 실행

  # 실제로 테스트 데이터 삭제
  python cleanup_test_data.py TEST_20250722_092050_49CF --confirm

  🏷️ 테스트 데이터 식별

  모든 테스트 데이터는 고유한 세션 ID로 태깅됩니다:

  게시글 제목 예시

  [🧪TEST-TEST_20250722_092050_49CF] CRUD 작성 테스트용 게시글

  댓글 내용 예시

  🧪[TEST-TEST_20250722_092050_49CF] 이것은 댓글/답글 CRUD 테스트를 위한 댓글입니다. (댓글#1)

  📈 성능 모니터링

  각 테스트의 응답 시간이 측정되어 출력됩니다:
  ✅ 성공 - 댓글 ID: 687ed966882f60e0e56557e7, 시간: 0.093초
  ✅ 성공 - 답글 ID: 687ed967882f60e0e56557ea, 시간: 0.122초

  🔧 사전 요구사항

  1. 백엔드 서버 실행
  cd /home/nadle/projects/Xai_Community/v5/backend
  uv run python main.py
  2. 프론트엔드 서버 실행 (선택사항, 브라우저 확인용)
  cd /home/nadle/projects/Xai_Community/v5/frontend
  npm run dev
  3. Python 의존성
  pip install aiohttp

  💡 활용 팁

  1. 개발 중 API 검증: 새로운 댓글/답글 기능 구현 후 전체 기능 동작 확인
  2. 성능 테스트: 응답 시간 모니터링으로 성능 저하 조기 발견
  3. 브라우저 검증: 실제 UI에서 생성된 데이터 확인
  4. 안전한 정리: 세션 ID 기반으로 테스트 데이터만 정확히 삭제

  이제 댓글/답글 기능의 전체 CRUD 작업을 자동으로 테스트하고 브라우저에서 결과를 확인할 수 있습니다! 🎉