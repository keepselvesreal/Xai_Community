# API 테스트 매트릭스

## 📋 개요

이 문서는 Xai Community 백엔드 API의 모든 엔드포인트에 대한 테스트 커버리지를 매트릭스 형태로 정리한 참고 자료입니다. 각 API 엔드포인트별로 현재 테스트 상태, 필요한 테스트 시나리오, 구현 우선순위를 한눈에 파악할 수 있습니다.

**업데이트 일자**: 2025-06-27  
**총 API 수**: 36개  
**테스트 완료**: 15개 (42%)  
**미완성**: 21개 (58%)

## 🔍 범례

### 테스트 상태
- ✅ **완료**: 완전한 테스트 커버리지
- ⚠️ **부분**: 기본적인 테스트만 존재
- ❌ **미구현**: 테스트 없음
- 🔄 **진행중**: 현재 구현 중

### 우선순위
- 🔴 **High**: 보안, 핵심 기능 (즉시 구현 필요)
- 🟡 **Medium**: 사용자 경험, 비즈니스 로직 (2주 내)
- 🟢 **Low**: 유지보수, 편의성 (1개월 내)

### 테스트 종류
- **U**: Unit Test (단위 테스트)
- **I**: Integration Test (통합 테스트)
- **S**: Security Test (보안 테스트)
- **P**: Performance Test (성능 테스트)

## 📊 API 테스트 매트릭스

### 🔐 인증 시스템 (Authentication)

| 엔드포인트 | HTTP | 테스트 상태 | 우선순위 | 테스트 종류 | 테스트 파일 | 누락된 테스트 시나리오 |
|-----------|------|------------|----------|------------|------------|---------------------|
| `/register` | POST | ✅ | - | U, I | `test_auth_router.py` | 이메일 중복, 약한 비밀번호 |
| `/login` | POST | ✅ | - | U, I, S | `test_auth_router.py` | 브루트포스 방지, 계정 잠금 |
| `/refresh` | POST | ❌ | 🔴 | U, I, S | - | 토큰 만료, 재사용 방지, 블랙리스트 |
| `/health` | GET | ✅ | - | U | `test_auth_router.py` | - |
| `/profile` | GET | ⚠️ | 🟡 | I | `test_auth_router.py` | 프로필 데이터 검증, 권한 확인 |
| `/profile` | PUT | ❌ | 🟡 | U, I, S | - | 데이터 검증, 중복 체크, XSS 방지 |
| `/change-password` | POST | ⚠️ | 🔴 | I, S | `test_auth_router.py` | 현재 비밀번호 확인, 강도 검증 |
| `/deactivate` | POST | ⚠️ | 🟡 | I | `test_auth_router.py` | 데이터 정리, 복구 불가 확인 |
| `/admin/users` | GET | ⚠️ | 🟡 | I, S | `test_auth_router.py` | 페이지네이션, 필터링, 권한 |
| `/admin/users/{id}/suspend` | POST | ❌ | 🟡 | I, S | - | 관리자 권한, 로그 기록, 알림 |
| `/admin/users/{id}/activate` | POST | ❌ | 🟡 | I, S | - | 관리자 권한, 상태 변경 검증 |
| `/admin/users/{id}` | DELETE | ❌ | 🟡 | I, S | - | 관리자 권한, 연관 데이터 처리 |

**커버리지**: 25% (3/12)

### 📝 게시글 시스템 (Posts)

| 엔드포인트 | HTTP | 테스트 상태 | 우선순위 | 테스트 종류 | 테스트 파일 | 누락된 테스트 시나리오 |
|-----------|------|------------|----------|------------|------------|---------------------|
| `/api/posts/health` | GET | ❌ | 🟢 | U | - | 서비스 상태 확인 |
| `/api/posts/search` | GET | ✅ | - | I, P | `test_posts_router.py` | 복잡한 쿼리, 성능 |
| `/api/posts` | GET | ✅ | - | I, P | `test_posts_router.py` | 대용량 데이터 페이지네이션 |
| `/api/posts` | POST | ✅ | - | U, I, S | `test_posts_router.py` | 파일 첨부, 스팸 방지 |
| `/api/posts/{slug}` | GET | ✅ | - | I, P | `test_posts_router.py` | 조회수 증가, 캐싱 |
| `/api/posts/{slug}` | PUT | ✅ | - | I, S | `test_posts_router.py` | 작성자 권한, 버전 관리 |
| `/api/posts/{slug}` | DELETE | ✅ | - | I, S | `test_posts_router.py` | 연관 데이터 정리 |
| `/api/posts/{slug}/like` | POST | ❌ | 🟡 | U, I | - | 중복 방지, 반응 변경, 통계 업데이트 |
| `/api/posts/{slug}/dislike` | POST | ❌ | 🟡 | U, I | - | 좋아요와 배타적 처리 |
| `/api/posts/{slug}/bookmark` | POST | ❌ | 🟡 | U, I | - | 북마크 목록 관리 |
| `/api/posts/{slug}/stats` | GET | ❌ | 🟡 | I, P | - | 실시간 통계, 캐싱 |

**커버리지**: 55% (6/11)

### 💬 댓글 시스템 (Comments)

| 엔드포인트 | HTTP | 테스트 상태 | 우선순위 | 테스트 종류 | 테스트 파일 | 누락된 테스트 시나리오 |
|-----------|------|------------|----------|------------|------------|---------------------|
| `/api/posts/{slug}/comments` | GET | ✅ | - | I, P | `test_comments_router.py` | 대용량 댓글, 중첩 구조 |
| `/api/posts/{slug}/comments` | POST | ✅ | - | U, I, S | `test_comments_router.py` | 스팸 방지, 길이 제한 |
| `/api/posts/{slug}/comments/{id}/replies` | POST | ✅ | - | U, I | `test_comments_router.py` | 중첩 레벨 제한 |
| `/api/posts/{slug}/comments/{id}` | PUT | ✅ | - | I, S | `test_comments_router.py` | 작성자 권한, 수정 이력 |
| `/api/posts/{slug}/comments/{id}` | DELETE | ✅ | - | I, S | `test_comments_router.py` | 답글 처리, 소프트 삭제 |
| `/api/posts/{slug}/comments/{id}/like` | POST | ❌ | 🟡 | U, I | - | 반응 중복 방지 |
| `/api/posts/{slug}/comments/{id}/dislike` | POST | ❌ | 🟡 | U, I | - | 배타적 반응 처리 |

**커버리지**: 71% (5/7)

### 📁 파일 업로드 시스템 (Files)

| 엔드포인트 | HTTP | 테스트 상태 | 우선순위 | 테스트 종류 | 테스트 파일 | 누락된 테스트 시나리오 |
|-----------|------|------------|----------|------------|------------|---------------------|
| `/upload` | POST | ✅ | - | U, I, S | `test_file_upload_api.py` | 악성 파일 검증, 메타데이터 |
| `/{file_id}` | GET | ❌ | 🔴 | I, S, P | - | 접근 권한, 캐싱, 스트리밍 |
| `/{file_id}/info` | GET | ❌ | 🟡 | I, S | - | 권한 확인, 메타데이터 보안 |
| `/health` | GET | ❌ | 🟢 | U | - | 스토리지 상태 |

**커버리지**: 25% (1/4)

### 🎨 콘텐츠 처리 시스템 (Content)

| 엔드포인트 | HTTP | 테스트 상태 | 우선순위 | 테스트 종류 | 테스트 파일 | 누락된 테스트 시나리오 |
|-----------|------|------------|----------|------------|------------|---------------------|
| `/api/content/preview` | POST | ❌ | 🔴 | U, S | - | 마크다운 파싱, XSS 방지, 이미지 처리 |
| `/api/content/test` | GET | ❌ | 🟢 | U | - | 기본 응답 확인 |

**커버리지**: 0% (0/2)

## 🎯 테스트 시나리오 상세 명세

### 🔴 High Priority 테스트 시나리오

#### 1. Refresh Token 보안 테스트
```python
# 우선순위: 🔴 High
# 예상 구현 시간: 4시간
# 테스트 파일: tests/security/test_refresh_token.py

테스트 시나리오:
- 정상적인 토큰 갱신
- 만료된 토큰 처리
- 재사용된 토큰 탐지
- 토큰 블랙리스트 처리
- 동시 갱신 요청 처리
```

#### 2. 콘텐츠 보안 테스트
```python
# 우선순위: 🔴 High  
# 예상 구현 시간: 6시간
# 테스트 파일: tests/security/test_content_security.py

테스트 시나리오:
- XSS 공격 방지 (게시글, 댓글)
- 마크다운 인젝션 방지
- 이미지 태그 검증
- 링크 검증 (javascript: 등)
- HTML 태그 화이트리스트
```

#### 3. 파일 접근 제어 테스트
```python
# 우선순위: 🔴 High
# 예상 구현 시간: 5시간  
# 테스트 파일: tests/security/test_file_access.py

테스트 시나리오:
- 업로드 사용자 권한 확인
- 비공개 파일 접근 제어
- 파일 URL 토큰 검증
- 외부 접근 차단
- 직접 링크 방지
```

#### 4. 비밀번호 변경 보안 테스트
```python
# 우선순위: 🔴 High
# 예상 구현 시간: 3시간
# 테스트 파일: tests/security/test_password_change.py

테스트 시나리오:
- 현재 비밀번호 검증
- 새 비밀번호 강도 확인
- 최근 비밀번호 재사용 방지
- 세션 무효화 처리
```

### 🟡 Medium Priority 테스트 시나리오

#### 1. 사용자 반응 시스템 테스트
```python
# 우선순위: 🟡 Medium
# 예상 구현 시간: 8시간
# 테스트 파일: tests/integration/test_reactions.py

테스트 시나리오:
- 게시글 좋아요/싫어요/북마크
- 댓글 좋아요/싫어요
- 중복 반응 방지
- 반응 변경 처리
- 통계 업데이트 검증
- 반응 취소 처리
```

#### 2. 게시글 통계 테스트
```python
# 우선순위: 🟡 Medium
# 예상 구현 시간: 4시간
# 테스트 파일: tests/integration/test_post_stats.py

테스트 시나리오:
- 조회수 증가 로직
- 실시간 통계 계산
- 통계 캐싱 효과
- 중복 조회 방지
```

#### 3. 관리자 기능 테스트
```python
# 우선순위: 🟡 Medium
# 예상 구현 시간: 6시간
# 테스트 파일: tests/integration/test_admin_functions.py

테스트 시나리오:
- 사용자 계정 정지/활성화
- 계정 삭제 및 데이터 처리
- 관리자 권한 확인
- 감사 로그 기록
```

### 🟢 Low Priority 테스트 시나리오

#### 1. Health Check 테스트
```python
# 우선순위: 🟢 Low
# 예상 구현 시간: 2시간
# 테스트 파일: tests/unit/test_health_checks.py

테스트 시나리오:
- 각 서비스별 상태 확인
- 응답 시간 측정
- 의존성 서비스 상태
```

#### 2. 성능 테스트
```python
# 우선순위: 🟢 Low
# 예상 구현 시간: 8시간
# 테스트 파일: tests/performance/test_api_performance.py

테스트 시나리오:
- 동시 요청 처리
- 대용량 데이터 처리
- 응답 시간 벤치마크
- 메모리 사용량 모니터링
```

## 📈 구현 순서 및 일정

### Week 1-2: 보안 테스트 (🔴 High Priority)
1. **Refresh Token 보안** (4h)
2. **콘텐츠 보안 (XSS 방지)** (6h)
3. **파일 접근 제어** (5h)
4. **비밀번호 변경 보안** (3h)

**예상 소요 시간**: 18시간

### Week 3-4: 사용자 기능 테스트 (🟡 Medium Priority)
1. **사용자 반응 시스템** (8h)
2. **게시글 통계** (4h)
3. **관리자 기능** (6h)
4. **프로필 관리** (4h)

**예상 소요 시간**: 22시간

### Week 5-6: 성능 및 유지보수 테스트 (🟢 Low Priority)
1. **Health Check 엔드포인트** (2h)
2. **성능 및 부하 테스트** (8h)
3. **에러 핸들링 표준화** (4h)
4. **문서화 및 정리** (6h)

**예상 소요 시간**: 20시간

## 🔍 테스트 커버리지 목표

### 현재 상태 (2025-06-27)
```
전체 API: 36개
✅ 완료: 15개 (42%)
⚠️ 부분: 4개 (11%)  
❌ 미구현: 17개 (47%)
```

### 목표 상태 (2025-08-15)
```
전체 API: 36개
✅ 완료: 30개 (83%)
⚠️ 부분: 4개 (11%)
❌ 미구현: 2개 (6%)
```

### 라우터별 목표
| 라우터 | 현재 커버리지 | 목표 커버리지 | 완료 예정일 |
|--------|--------------|--------------|------------|
| Auth | 25% (3/12) | 90% (11/12) | 2025-07-15 |
| Posts | 55% (6/11) | 95% (10/11) | 2025-07-30 |
| Comments | 71% (5/7) | 100% (7/7) | 2025-07-22 |
| Files | 25% (1/4) | 100% (4/4) | 2025-07-25 |
| Content | 0% (0/2) | 100% (2/2) | 2025-07-18 |

## 📋 테스트 실행 체크리스트

### 일일 테스트 실행
- [ ] `make test-unit` - 단위 테스트 실행
- [ ] `make test-integration` - 통합 테스트 실행  
- [ ] `make test-cov` - 커버리지 확인

### 주간 테스트 검토
- [ ] 새로 추가된 테스트 리뷰
- [ ] 실패하는 테스트 원인 분석
- [ ] 테스트 커버리지 트렌드 확인
- [ ] 성능 테스트 결과 검토

### 릴리스 전 체크리스트
- [ ] 모든 보안 테스트 통과
- [ ] 회귀 테스트 100% 통과
- [ ] 성능 테스트 기준치 만족
- [ ] 문서 업데이트 완료

## 🔗 관련 문서

- [테스트 현황 분석 보고서](./테스트_현황_분석_보고서.md)
- [회귀 테스트 구현 가이드](./회귀_테스트_구현_가이드.md)
- [테스트 실행 가이드](./테스트_실행_가이드.md)

---

**작성자**: Claude Code  
**마지막 업데이트**: 2025-06-27  
**다음 검토 예정**: 매주 금요일