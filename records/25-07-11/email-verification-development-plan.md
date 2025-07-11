# 이메일 인증 기능 개발 계획

**작성일**: 2025-07-11  
**상태**: 계획 수립 완료  
**우선순위**: 높음  

## 🎯 목표
현재 회원가입 페이지 디자인을 기반으로 이메일 인증 전용 개발 페이지를 만들어, 기존 기능에 영향 주지 않고 이메일 인증 플로우를 완성한다.

## 📋 구현 단계

### 1단계: 프론트엔드 개발 페이지 생성
- **파일**: `frontend/app/routes/dev.email-verification.tsx`
- **기능**: 
  - 현재 `auth.register.tsx` 디자인 복사
  - 이메일 입력란 + "인증하기" 버튼
  - 인증번호 입력란 (인증 메일 발송 후 표시)
  - 아이디/비밀번호 입력란 (인증 성공 후 활성화)

### 2단계: 백엔드 API 엔드포인트 확장
이미 `EmailService`가 존재하므로 이를 활용:
- **인증 메일 발송**: `POST /api/auth/send-verification-email`
- **인증번호 확인**: `POST /api/auth/verify-email-code`
- 기존 `auth.py` 라우터에 엔드포인트 추가

### 3단계: 이메일 인증 플로우 구현
1. **이메일 입력 → 인증하기 버튼 클릭**
   - 백엔드에서 6자리 랜덤 숫자 생성
   - 해당 이메일로 인증번호 발송
   - 프론트엔드에서 인증번호 입력란 표시

2. **인증번호 입력 → 확인**
   - 백엔드에서 인증번호 검증 (5분 내 유효)
   - 성공 시 아이디/비밀번호 입력란 활성화
   - 실패 시 에러 메시지 표시

3. **회원가입 완료**
   - 기존 회원가입 로직 재사용
   - 이메일 인증 완료 플래그 설정

### 4단계: 이메일 서비스 구성
- **개발용 SMTP 설정**: Mailtrap 또는 Gmail SMTP 사용
- **인증번호 저장**: Redis 또는 MongoDB temporary collection
- **만료시간**: 5분

## 🛠 기술 스택
- **프론트엔드**: 기존 Remix + TypeScript 구조 활용
- **백엔드**: 기존 FastAPI + EmailService 확장
- **이메일**: 기존 EmailService (SMTP 기반)
- **저장소**: MongoDB (인증번호 임시 저장용)

## 📁 생성할 파일들
1. `frontend/app/routes/dev.email-verification.tsx` - 개발 전용 페이지
2. `backend/nadle_backend/models/email_verification.py` - 인증 모델
3. 기존 `auth.py`에 2개 엔드포인트 추가

## 🔄 플로우 시퀀스
```
1. 사용자: 이메일 입력 → "인증하기" 클릭
2. 프론트: POST /api/auth/send-verification-email
3. 백엔드: 6자리 코드 생성 → DB 저장 → 이메일 발송
4. 사용자: 이메일 확인 → 인증번호 입력
5. 프론트: POST /api/auth/verify-email-code  
6. 백엔드: 코드 검증 → 성공/실패 응답
7. 프론트: 성공 시 아이디/비밀번호 입력란 활성화
8. 사용자: 회원가입 완료
```

## 🎨 UI/UX 디자인
- 기존 `auth.register.tsx`의 깔끔한 카드 스타일 유지
- 단계별 진행 상황 표시 (이메일 입력 → 인증 → 회원가입)
- 인증 대기 중 로딩 스피너
- 인증번호 재발송 기능 (60초 쿨다운)

## 📊 기존 인프라 활용
- **EmailService**: `backend/nadle_backend/services/email_service.py` 기존 코드 활용
- **설정**: `backend/nadle_backend/config.py`의 `email_verification_code_length` 활용
- **데이터베이스**: 기존 MongoDB 연결 활용
- **인증 로직**: 기존 `auth_service.py` 패턴 확장

## 🚀 장점
- 기존 회원가입 기능에 전혀 영향 없음
- 개발 전용 페이지로 안전한 테스트 가능
- 기존 EmailService 인프라 재사용
- 완성 후 기존 회원가입에 쉽게 적용 가능

## ⚠️ 주의사항
- 개발 페이지는 프로덕션 배포 시 제외 필요
- SMTP 설정은 개발 환경에서만 사용
- 인증번호는 반드시 만료시간 설정
- 보안을 위해 인증 시도 횟수 제한 고려

---
**다음 단계**: 이 계획이 승인되면 1단계부터 순차적으로 구현 시작