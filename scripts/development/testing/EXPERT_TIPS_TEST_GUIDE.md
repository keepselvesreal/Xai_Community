# 전문가의 꿀정보 페이지 종합 테스트 가이드

> 📅 **작성일**: 2025-07-22  
> 📝 **버전**: v1.0  
> 🎯 **대상**: 전문가의 꿀정보 페이지 완전 테스트  

## 📋 목차

1. [개요](#개요)
2. [테스트 시스템 구성](#테스트-시스템-구성)
3. [자동화 테스트 실행](#자동화-테스트-실행)
4. [브라우저 확인 테스트](#브라우저-확인-테스트)
5. [테스트 데이터 관리](#테스트-데이터-관리)
6. [문제 해결 가이드](#문제-해결-가이드)
7. [FAQ](#faq)

---

## 개요

전문가의 꿀정보 페이지는 **권한 기반 시스템**으로, 일반 게시판과 다른 특별한 기능들이 있습니다:

### 🎯 주요 특징
- **글쓰기 권한 제어**: `can_write_expert_tips` 권한 필요
- **전문가 메타데이터**: 전문가 이름, 직책, 카테고리, 태그
- **전용 콘텐츠 타입**: `metadata.type = "expert_tips"`
- **전문가 검증 시스템**: 전문가 배지 및 신뢰도 표시

### 🧪 테스트 시스템 구성
1. **자동화 API 테스트**: 백엔드 API 완전 자동화 테스트
2. **브라우저 확인 시스템**: 프론트엔드에서 직접 확인하는 수동 테스트
3. **데이터 관리 시스템**: 테스트 데이터 생성/정리 자동화

---

## 테스트 시스템 구성

### 📁 파일 구조

```
scripts/development/testing/
├── api/
│   ├── expert_tips_automation_test.py      # 자동화 테스트 스크립트
│   └── reports/                            # 자동화 테스트 보고서
├── browser/
│   ├── expert_tips_browser_test_setup.py   # 브라우저 테스트 데이터 생성
│   ├── expert_tips_browser_test_guide.html # 브라우저 확인 가이드 대시보드
│   └── expert_tips_test_data_manager.py    # 테스트 데이터 관리
└── EXPERT_TIPS_TEST_GUIDE.md               # 이 문서
```

### 🎯 각 도구의 역할

| 도구 | 용도 | 실행 시점 |
|------|------|-----------|
| `expert_tips_automation_test.py` | API 자동화 테스트 | 개발 완료 후 |
| `expert_tips_browser_test_setup.py` | 브라우저 테스트 데이터 생성 | 브라우저 테스트 전 |
| `expert_tips_browser_test_guide.html` | 브라우저 수동 테스트 가이드 | 브라우저 테스트 중 |
| `expert_tips_test_data_manager.py` | 테스트 데이터 정리 | 테스트 완료 후 |

---

## 자동화 테스트 실행

### 1. 사전 준비사항

#### 서버 실행 확인
```bash
# 백엔드 서버 실행 (8000 포트)
cd backend && uv run python main.py

# 프론트엔드 서버 실행 (5173 포트)
cd frontend && npm run dev
```

#### 기존 전문가 꿀정보 데이터 확인
자동화 테스트는 기존 전문가 꿀정보 게시글이 있어야 합니다:

```bash
# 전문가 꿀정보 데이터 생성 (필요한 경우)
cd scripts/development/data-gen
python generate_expert_tips_api.py
```

### 2. 자동화 테스트 실행

```bash
cd scripts/development/testing/api
python expert_tips_automation_test.py
```

### 3. 테스트 결과 해석

#### ✅ 성공 시 출력 예시
```
🚀 전문가의 꿀정보 페이지 통합 테스트 시작!
🆔 세션 ID: EXPERT_TIPS_20250722_143000_A1B2
📊 총 8개 테스트 섹션 예정
⏱️ 예상 소요 시간: 18분 0초

📋 [1/8] 기본 인프라 검증
   ✅ 서버 헬스체크: 서버 정상 응답 확인
   ✅ 인증 시스템 검증: JWT 토큰 생성 및 검증 성공
   ✅ 전문가 꿀정보 API 엔드포인트: expert_tips 타입 지원 확인

...

🎉 전문가의 꿀정보 통합 테스트 완료!
📄 JSON 보고서: reports/test_report_20250722_143052_A1B2.json
🌐 HTML 보고서: reports/test_report_20250722_143052_A1B2.html
```

#### 📊 보고서 확인
- **JSON 보고서**: 상세한 테스트 결과 데이터
- **HTML 보고서**: 시각적 대시보드 (브라우저에서 확인)

### 4. 자동화 테스트 범위

| 테스트 섹션 | 주요 검증 항목 | 테스트 수 |
|-------------|----------------|-----------|
| **기본 인프라 검증** | 서버 상태, 인증, API 엔드포인트 | 3개 |
| **권한 시스템 검증** | can_write_expert_tips 권한, 접근 제어 | 5개 |
| **전문가 꿀정보 목록** | 필터링, 검색, 페이지네이션, 정렬 | 6개 |
| **CRUD 작업** | 생성, 수정, 삭제, 메타데이터 | 5개 |
| **메타데이터 시스템** | 전문가 정보, 카테고리, 태그 | 6개 |
| **반응 시스템** | 좋아요, 북마크, 댓글, 답글 | 6개 |
| **실시간 통계** | 조회수, 반응 수, 랭킹 | 6개 |
| **데이터 정리** | 테스트 데이터 정리 | 4개 |

---

## 브라우저 확인 테스트

브라우저 테스트는 실제 사용자 관점에서 전문가 꿀정보 페이지를 확인합니다.

### 1. 브라우저 테스트 데이터 생성

```bash
cd scripts/development/testing/browser
python expert_tips_browser_test_setup.py
```

#### 생성되는 데이터
- **전문가 권한 계정**: `expert_browser_test_XXXX@example.com`
- **일반 사용자 계정**: `normal_browser_test_XXXX@example.com`
- **샘플 댓글**: 15개 (전문가/일반 사용자 작성)
- **샘플 반응**: 20개 (좋아요/북마크)

### 2. 브라우저 확인 가이드 열기

```bash
# 브라우저에서 가이드 대시보드 열기
open browser/expert_tips_browser_test_guide.html
# 또는
start browser/expert_tips_browser_test_guide.html
```

### 3. 체크리스트 기반 테스트

브라우저 가이드 대시보드에서 다음 순서로 진행:

#### Step 1: 권한 시스템 테스트
1. **전문가 권한 계정 로그인**
   - 이메일: `expert_browser_test_XXXX@example.com`
   - 비밀번호: `TestPassword123!`
   - 확인: "글쓰기" 버튼 표시

2. **일반 사용자 계정 로그인**
   - 이메일: `normal_browser_test_XXXX@example.com`
   - 비밀번호: `TestPassword123!`
   - 확인: "글쓰기" 버튼 숨김

3. **접근 제어 테스트**
   - 일반 사용자로 `/expert-tips/write` 직접 접근
   - 확인: 403 에러 또는 리디렉션

#### Step 2: 목록 페이지 기능
1. **전문가 꿀정보 목록 접속**: `http://localhost:5173/expert-tips`
2. **카테고리 필터링**: 인테리어, 생활팁, 요리 등
3. **전문가별 필터링**: 특정 전문가 게시글만 표시
4. **검색 기능**: 제목, 내용, 전문가 이름으로 검색
5. **페이지네이션**: 페이지 이동
6. **정렬 기능**: 최신순, 인기순, 조회순

#### Step 3: 상세 페이지 기능
1. **콘텐츠 렌더링**: 마크다운 내용 정상 표시
2. **전문가 메타데이터**: 이름, 직책, 카테고리, 태그
3. **조회수 증가**: 새로고침 시 조회수 증가
4. **반응 버튼**: 좋아요, 싫어요, 북마크
5. **통계 표시**: 조회수, 좋아요 수, 북마크 수

#### Step 4: 댓글 시스템
1. **댓글 목록**: 샘플 댓글들 정상 표시
2. **댓글 작성**: 새 댓글 작성 및 즉시 표시
3. **답글 작성**: 기존 댓글에 답글 작성
4. **댓글 수정**: 본인 댓글만 수정 가능
5. **댓글 삭제**: 본인 댓글만 삭제 가능
6. **댓글 반응**: 댓글에 좋아요/싫어요

#### Step 5: 실시간 업데이트
1. **조회수 실시간 반영**: 새로고침 시 즉시 증가
2. **반응 수 실시간 반영**: 클릭 시 즉시 업데이트
3. **댓글 수 실시간 반영**: 댓글 작성 시 즉시 증가
4. **목록↔상세 일치성**: 목록과 상세 페이지 통계 일치

### 4. 진행률 추적

브라우저 가이드 대시보드는 자동으로 진행률을 추적합니다:
- ✅ 체크 완료된 항목: 녹색으로 표시
- ⏳ 진행률 바: 상단에 시각적 표시
- 📊 완료 시 리포트 생성 가능

---

## 테스트 데이터 관리

테스트 완료 후 생성된 데이터를 정리해야 합니다.

### 1. 테스트 세션 목록 확인

```bash
cd scripts/development/testing/browser
python expert_tips_test_data_manager.py --action list
```

### 2. 특정 세션 데이터 식별

```bash
# 특정 세션의 테스트 데이터 확인
python expert_tips_test_data_manager.py --action identify --session BROWSER_TEST_20250722_143000

# 모든 브라우저 테스트 데이터 확인
python expert_tips_test_data_manager.py --action identify
```

### 3. 테스트 데이터 정리

```bash
# Dry Run (실제 삭제 안함, 확인용)
python expert_tips_test_data_manager.py --action cleanup --session BROWSER_TEST_20250722_143000 --dry-run

# 실제 정리 실행
python expert_tips_test_data_manager.py --action cleanup --session BROWSER_TEST_20250722_143000 --admin-email admin@example.com --admin-password AdminPassword123!
```

### 4. 정리 대상 데이터

| 데이터 타입 | 정리 여부 | 비고 |
|-------------|-----------|------|
| 테스트 사용자 | ✅ 삭제 | browser_test_XXXX 패턴 |
| 테스트 댓글 | ✅ 삭제 | browser_test_session 메타데이터 |
| 테스트 반응 | ✅ 삭제 | 테스트 사용자가 생성한 반응 |
| 전문가 꿀정보 게시글 | ❌ 보존 | 기존 데이터 보존 |

### 5. 정리 보고서

데이터 정리 후 자동으로 보고서가 생성됩니다:

```
📄 정리 보고서 저장됨: expert_tips_cleanup_report_20250722_143052.md
```

---

## 문제 해결 가이드

### 1. 자동화 테스트 문제

#### 🔴 "전문가 꿀정보 게시글이 없습니다"
**원인**: 테스트할 expert_tips 타입 게시글이 없음  
**해결**:
```bash
cd scripts/development/data-gen
python generate_expert_tips_api.py
```

#### 🔴 "권한 없는 사용자 403 Forbidden 응답" 실패
**원인**: 권한 시스템이 제대로 작동하지 않음  
**해결**:
1. 관리자 계정 확인
2. `can_write_expert_tips` 권한 설정 확인
3. API 라우터의 권한 검증 로직 확인

#### 🔴 Rate Limiting 에러
**원인**: API 호출이 너무 빈번함  
**해결**: 잠시 기다린 후 다시 실행

### 2. 브라우저 테스트 문제

#### 🔴 테스트 계정 로그인 실패
**원인**: 테스트 데이터가 생성되지 않았거나 비밀번호 불일치  
**해결**:
```bash
# 테스트 데이터 재생성
python expert_tips_browser_test_setup.py
```

#### 🔴 "글쓰기" 버튼이 전문가 계정에서도 안 보임
**원인**: 권한이 제대로 부여되지 않음  
**해결**:
1. 관리자 페이지에서 사용자 권한 확인
2. 브라우저 캐시 클리어
3. 다시 로그인

#### 🔴 댓글/반응이 표시되지 않음
**원인**: 샘플 데이터 생성 실패  
**해결**:
```bash
# 테스트 데이터 재생성
python expert_tips_browser_test_setup.py
```

### 3. 데이터 정리 문제

#### 🔴 "관리자 인증이 필요합니다"
**원인**: 관리자 계정 정보가 잘못됨  
**해결**:
```bash
# 올바른 관리자 계정으로 실행
python expert_tips_test_data_manager.py --action cleanup --admin-email admin@example.com --admin-password AdminPassword123!
```

#### 🔴 일부 데이터가 정리되지 않음
**원인**: API 권한 부족 또는 참조 무결성 제약  
**해결**:
1. 관리자 권한으로 실행
2. 수동으로 관리자 페이지에서 정리

---

## FAQ

### Q1: 자동화 테스트와 브라우저 테스트의 차이점은?

**A**: 
- **자동화 테스트**: API 레벨에서 백엔드 로직 검증, 완전 자동
- **브라우저 테스트**: 사용자 관점에서 프론트엔드 UI/UX 검증, 수동 확인

### Q2: 테스트 데이터가 프로덕션에 영향을 주나요?

**A**: 아니요. 모든 테스트 데이터는:
- 식별 가능한 패턴으로 생성 (`browser_test_`, `EXPERT_TIPS_` 등)
- 세션 ID로 추적 가능
- 자동 정리 스크립트로 안전하게 제거

### Q3: 기존 전문가 꿀정보 게시글이 삭제될까요?

**A**: 아니요. 테스트 데이터 정리 시:
- ✅ 삭제: 테스트 계정, 테스트 댓글, 테스트 반응
- ❌ 보존: 기존 전문가 꿀정보 게시글

### Q4: 권한 시스템 테스트가 실패하면 어떻게 하나요?

**A**: 다음 순서로 확인:
1. 백엔드 API의 권한 검증 로직 확인
2. 프론트엔드의 권한 표시 UI 확인  
3. 관리자 페이지에서 권한 부여 상태 확인

### Q5: 테스트 완료 후 반드시 데이터를 정리해야 하나요?

**A**: 권장사항입니다:
- **개발 환경**: 선택사항이지만 정리 권장
- **스테이징 환경**: 반드시 정리
- **프로덕션 환경**: 테스트 금지

### Q6: 브라우저 가이드를 커스터마이징할 수 있나요?

**A**: 네, `expert_tips_browser_test_guide.html` 파일을 수정하여:
- 체크리스트 항목 추가/수정
- 스타일링 변경
- 추가 URL 링크 추가

---

## 🎯 전체 워크플로우 요약

### 1단계: 자동화 테스트
```bash
cd scripts/development/testing/api
python expert_tips_automation_test.py
```

### 2단계: 브라우저 테스트 데이터 생성
```bash
cd scripts/development/testing/browser
python expert_tips_browser_test_setup.py
```

### 3단계: 브라우저 수동 확인
```bash
# 가이드 대시보드 열기
open expert_tips_browser_test_guide.html
```

### 4단계: 테스트 데이터 정리
```bash
python expert_tips_test_data_manager.py --action cleanup
```

---

## 📞 지원 및 문의

테스트 관련 문제나 개선 제안이 있으시면:

1. **이슈 생성**: 프로젝트 저장소에 이슈 등록
2. **로그 첨부**: 오류 발생 시 관련 로그 첨부
3. **환경 정보**: OS, 브라우저, 서버 버전 등 명시

---

**📅 마지막 업데이트**: 2025-07-22  
**✏️ 다음 업데이트 예정**: 사용자 피드백 반영 후