# 트러블슈팅: ID + 한글 Slug 구현 과정

**작성일**: 2025-06-30  
**세션**: 게시글 상세 페이지 API 통합 및 ID + 한글 Slug 구현  
**담당자**: Claude Code Assistant

## 📋 목차
1. [세션 개요](#세션-개요)
2. [발생한 문제들](#발생한-문제들)
3. [해결 과정](#해결-과정)
4. [최종 구현 결과](#최종-구현-결과)
5. [학습한 교훈](#학습한-교훈)
6. [향후 참고사항](#향후-참고사항)

---

## 세션 개요

### 🎯 초기 목표
- 게시글 상세 페이지와 API 통합
- 게시글 목록에서 상세 페이지로의 네비게이션 문제 해결
- ID + 한글 Slug 시스템 구현 (TDD 기반)

### 🔧 주요 작업 범위
- 백엔드: PostRepository slug 생성 로직 개선
- 프론트엔드: 게시글 네비게이션 및 컴포넌트 수정
- API: 엔드포인트 파라미터 개선 (slug_or_id 지원)
- 테스트: TDD 기반 검증 시스템 구축

---

## 발생한 문제들

### 1. 🐛 한글 제목 Slug 생성 문제

#### 문제 상황
```javascript
// 문제: 한글 제목이 "untitled"로 변환됨
Board: Post 686286b342b07df7b3b99cf8 slug: untitled
```

#### 원인 분석
- 기존 정규식 `[^a-z0-9\s-]`가 한글 문자(가-힣)를 제거
- 한글 제목 "입주민 커뮤니티 이용 안내" → 모든 문자 제거 → "untitled" 생성

#### 해결 방법
```python
# 기존 정규식 (문제)
slug = re.sub(r"[^a-z0-9\s\-]", "", slug)

# 수정된 정규식 (해결)
slug = re.sub(r"[^a-z0-9\s\-가-힣]", "", slug)
```

---

### 2. 🐛 게시글 클릭 시 네비게이션 실패

#### 문제 상황
```html
<!-- HTML은 정상 생성되지만 클릭이 작동하지 않음 -->
<a href="/posts/686296f554b90ab2ea1ab1f2-25-06-30-점검5">
  <div class="post-item">...</div>
</a>
```

#### 원인 분석
1. **무한 리렌더링**: useEffect 의존성 배열 문제로 지속적인 API 호출
2. **이벤트 충돌**: 스크롤 컨테이너의 onScroll 이벤트가 클릭 이벤트 방해
3. **Remix Link 컴포넌트**: 이벤트 핸들링 충돌

#### 해결 과정
```typescript
// 1단계: 무한 리렌더링 해결
useEffect(() => {
  fetchPosts();
}, []); // eslint-disable-line react-hooks/exhaustive-deps

// 2단계: 직접 클릭 핸들러 구현
<div 
  onClick={(e) => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/posts/${post.slug}`);
  }}
>

// 3단계: Remix navigate 사용
const navigate = useNavigate();
```

---

### 3. 🐛 프론트엔드 Import 오류

#### 문제 상황
```javascript
// posts.$slug.tsx에서 발생
Uncaught SyntaxError: The requested module '/app/components/layout/AppLayout.tsx' 
does not provide an export named 'AppLayout'
```

#### 원인 분석
- AppLayout은 `export default`로 내보내지만 `named import`로 가져오려 시도
- Card, Button 등 다른 컴포넌트들도 동일한 문제

#### 해결 방법
```typescript
// 문제가 있던 import
import { AppLayout } from '~/components/layout/AppLayout';
import { Card } from '~/components/ui/Card';

// 수정된 import  
import AppLayout from '~/components/layout/AppLayout';
import Card from '~/components/ui/Card';
```

---

### 4. 🐛 댓글 섹션 undefined 오류

#### 문제 상황
```javascript
// React 오류
TypeError: Cannot read properties of undefined (reading 'length')
at CommentSection (posts.$slug.tsx:109:56)
```

#### 원인 분석
- CommentSection 컴포넌트에서 `comments.length` 접근 시 comments가 undefined
- 초기 렌더링 시점에 comments 상태가 아직 로드되지 않음

#### 해결 방법
```typescript
// 문제가 있던 코드
댓글 <span>{comments.length}</span>개

// 수정된 코드 (안전한 접근)
댓글 <span>{comments?.length || 0}</span>개

// 다른 참조들도 안전하게 수정
{comments?.map((comment) => (...))}
{(!comments || comments.length === 0) && (...)}
```

---

### 5. 🐛 API 엔드포인트 파라미터 불일치

#### 문제 상황
```python
# 라우터에서 slug_or_id 파라미터를 받지만 서비스에서는 slug만 사용
@router.post("/{slug_or_id}/like")
async def like_post(slug_or_id: str, ...):
    result = await posts_service.toggle_post_reaction(slug, "like", current_user)  # 오류!
```

#### 원인 분석
- 라우터 파라미터명과 서비스 호출 시 변수명 불일치
- 일부 엔드포인트는 여전히 slug만 지원하는 상태

#### 해결 방법
```python
# 1. 라우터 수정: 올바른 변수명 사용
result = await posts_service.toggle_post_reaction(slug_or_id, "like", current_user)

# 2. 서비스 레이어 수정: slug 또는 ID 모두 지원
async def toggle_post_reaction(self, slug_or_id: str, ...):
    try:
        post = await self.post_repository.get_by_slug(slug_or_id)
    except PostNotFoundError:
        try:
            post = await self.post_repository.get_by_id(slug_or_id)
        except PostNotFoundError:
            raise PostNotFoundError(f"Post not found with slug or ID: {slug_or_id}")
```

---

## 해결 과정

### 🔄 TDD 기반 개발 프로세스

#### 1단계: 테스트 작성
```python
# test_korean_slug_generation.py
def test_generate_korean_slug_format(self):
    """한글 제목으로부터 올바른 slug 형식이 생성되는지 테스트."""
    title = "테스트 게시글"
    slug = self.post_repository._generate_slug(title)
    assert slug is not None
    assert len(slug) > 0
    assert "-" in slug  # ID와 제목 구분자
```

#### 2단계: 구현
```python
# PostRepository.create() 메서드 개선
async def create(self, post_data: PostCreate, author_id: str) -> Post:
    # 1. 임시 slug로 생성
    temp_slug = "temp-" + str(uuid.uuid4())[:8]
    
    # 2. 데이터베이스에 저장하여 ID 획득
    await post.save()
    
    # 3. 최종 slug 생성 (ID + 한글 제목)
    title_slug = self._generate_slug(post_data.title)
    final_slug = f"{str(post.id)}-{title_slug}"
    
    # 4. 최종 slug로 업데이트
    post.slug = final_slug
    await post.save()
```

#### 3단계: 검증
```bash
# 테스트 실행 결과
============================= test session starts ==============================
collected 17 items
tests/unit/test_korean_slug_generation.py .................              [100%]
collected 7 items  
tests/integration/test_post_detail_integration.py .......                [100%]
======================== 24 passed, 81 warnings in 8.65s ========================
```

### 🔧 통합 테스트 및 디버깅

#### API 응답 검증
```json
{
  "id": "68629582dd98c7381c6b7d19",
  "slug": "68629582dd98c7381c6b7d19-입주민-커뮤니티-이용-안내",
  "title": "입주민 커뮤니티 이용 안내"
}
```

#### 프론트엔드 디버깅
```javascript
// board.tsx에 추가한 디버깅 로그
console.log('Board: API response data:', response.data);
console.log(`Board: Post ${post.id} slug:`, post.slug);
console.log('Post clicked, navigating to:', `/posts/${post.slug}`);
```

---

## 최종 구현 결과

### ✅ 성공적으로 해결된 기능들

#### 1. **ID + 한글 Slug 시스템**
- 형식: `{mongodb_objectid}-{korean_title}`
- 예시: `68629582dd98c7381c6b7d19-입주민-커뮤니티-이용-안내`
- 고유성 보장 + SEO 친화적

#### 2. **API 엔드포인트 개선**
- 모든 posts 관련 API가 slug 또는 ID 모두 지원
- 하위 호환성 유지

#### 3. **프론트엔드 통합**
- 안정적인 게시글 네비게이션
- 불필요한 fallback 로직 제거
- 컴포넌트 import 오류 해결

#### 4. **TDD 검증**
- 17개 단위 테스트 통과
- 7개 통합 테스트 통과
- 실제 API 호출 검증 완료

### 📊 성능 및 안정성 개선
- 무한 리렌더링 문제 해결
- 이벤트 충돌 방지
- 안전한 타입 접근 구현
- 에러 핸들링 강화

---

## 학습한 교훈

### 🎓 기술적 교훈

#### 1. **정규식 다국어 지원**
```python
# 한글 지원을 위한 정규식 패턴
# 가-힣: 한글 완성형 문자 범위
regex_pattern = r"[^a-z0-9\s\-가-힣]"
```

#### 2. **React useEffect 의존성 관리**
```typescript
// 무한 리렌더링 방지
useEffect(() => {
  fetchPosts();
}, []); // 빈 배열로 한 번만 실행

// 배열 길이만 의존성으로 설정
useEffect(() => {
  updateScrollCounter(sortedPosts.length);
}, [sortedPosts.length]); // 전체 배열 대신 길이만
```

#### 3. **안전한 타입 접근**
```typescript
// Optional chaining과 null coalescing 활용
comments?.length || 0
post.stats?.view_count || post.stats?.views || 0
```

#### 4. **Import/Export 일관성**
```typescript
// 프로젝트 전체에서 일관된 export 방식 사용
// default export vs named export 혼용 주의
```

### 🔍 디버깅 전략

#### 1. **단계별 로그 추가**
- API 응답 데이터 확인
- 컴포넌트 렌더링 상태 추적
- 이벤트 핸들러 실행 확인

#### 2. **TDD 기반 검증**
- 먼저 테스트 작성하여 기대 동작 명확화
- 단위 테스트 + 통합 테스트 조합
- 실제 데이터로 검증

#### 3. **점진적 문제 해결**
- 한 번에 모든 문제를 해결하려 하지 않음
- 각 문제를 분리하여 순차적 해결
- 각 단계마다 테스트로 검증

---

## 향후 참고사항

### 🚀 추가 개선 가능 영역

#### 1. **Slug 생성 최적화**
```python
# 향후 고려사항
- 매우 긴 제목 처리 (길이 제한)
- 중복 제목 처리 개선
- 캐싱 시스템 도입
```

#### 2. **프론트엔드 성능 최적화**
```typescript
// React.memo 활용한 리렌더링 최적화
// 가상화(Virtualization)를 통한 긴 목록 성능 개선
// Suspense를 활용한 로딩 상태 관리
```

#### 3. **에러 처리 강화**
```typescript
// 네트워크 오류 재시도 로직
// 사용자 친화적 에러 메시지
// 오프라인 상태 처리
```

### 📝 개발 가이드라인

#### 1. **새로운 컴포넌트 개발 시**
- import/export 방식 프로젝트 전체와 일관성 유지
- Optional chaining 활용한 안전한 데이터 접근
- 적절한 로딩 상태 및 에러 처리

#### 2. **API 개발 시**
- slug_or_id 패턴으로 유연한 접근 지원
- 하위 호환성 고려한 점진적 변경
- TDD 기반 검증 시스템 구축

#### 3. **다국어 처리 시**
- 정규식에 해당 언어 문자 범위 포함
- URL 인코딩/디코딩 고려
- SEO 최적화 관점에서 설계

### 🔗 관련 문서
- [API 명세서 v3.2](./Spec--API_v3.md)
- [TDD 테스트 코드](../backend/tests/unit/test_korean_slug_generation.py)
- [통합 테스트](../backend/tests/integration/test_post_detail_integration.py)

---

**이 문서는 실제 개발 과정에서 발생한 문제들과 해결 과정을 기록한 것으로, 향후 유사한 상황에서 참고할 수 있는 실용적인 가이드입니다.**