# Sentry 대체 시스템 마이그레이션 코드 예시

## 🔄 백엔드 마이그레이션 코드 예시

### 1. 기존 Sentry 코드 → 새 로깅 시스템

#### 1.1 기본 에러 로깅

**Before (Sentry)**:
```python
import sentry_sdk
from sentry_sdk import capture_exception, set_user, set_context

# 에러 캡처
try:
    result = some_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    
# 사용자 컨텍스트 설정
sentry_sdk.set_user({"id": user_id, "email": user_email})

# 추가 컨텍스트
sentry_sdk.set_context("business_context", {"order_id": order_id})
```

**After (새 시스템)**:
```python
from nadle_backend.logging.structured_logger import log_error, ErrorType, LogContext

# 에러 로깅
try:
    result = some_operation()
except Exception as e:
    log_error(
        message="Operation failed in some_operation",
        error_type=ErrorType.SYSTEM_ERROR,
        exception=e,
        context=LogContext(
            user_id=user_id,
            endpoint="/api/some-endpoint",
            method="POST"
        ),
        order_id=order_id  # 추가 데이터
    )
```

#### 1.2 성능 추적

**Before (Sentry)**:
```python
import sentry_sdk

# 트랜잭션 추적
with sentry_sdk.start_transaction(op="database", name="user_query"):
    users = await User.find_all()
```

**After (새 시스템)**:
```python
from nadle_backend.logging.structured_logger import log_performance, LogContext
import time

# 성능 추적
start_time = time.time()
try:
    users = await User.find_all()
    duration = time.time() - start_time
    
    log_performance(
        operation="database_query_users",
        duration=duration,
        endpoint="/api/users",
        context=LogContext(user_id=current_user.id),
        record_count=len(users)
    )
except Exception as e:
    duration = time.time() - start_time
    log_error(
        message="Database query failed",
        error_type=ErrorType.DATABASE_ERROR,
        exception=e,
        context=LogContext(user_id=current_user.id),
        duration=duration
    )
```

#### 1.3 FastAPI 라우터에서의 사용

**Before (Sentry)**:
```python
from fastapi import APIRouter, HTTPException
import sentry_sdk

router = APIRouter()

@router.post("/posts")
async def create_post(post_data: PostCreate):
    try:
        # 사용자 컨텍스트 설정
        sentry_sdk.set_user({"id": current_user.id})
        
        post = await post_service.create_post(post_data)
        return post
    except ValidationError as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**After (새 시스템)**:
```python
from fastapi import APIRouter, HTTPException
from nadle_backend.logging.structured_logger import log_error, log_info, ErrorType, LogContext

router = APIRouter()

@router.post("/posts")
async def create_post(post_data: PostCreate, request: Request):
    context = LogContext(
        user_id=current_user.id,
        request_id=request.state.request_id,
        endpoint="/api/posts",
        method="POST",
        ip_address=request.client.host
    )
    
    try:
        log_info("Creating new post", context=context, post_title=post_data.title)
        
        post = await post_service.create_post(post_data)
        
        log_info("Post created successfully", context=context, post_id=post.id)
        return post
        
    except ValidationError as e:
        log_error(
            message="Post validation failed",
            error_type=ErrorType.VALIDATION_ERROR,
            exception=e,
            context=context,
            post_data=post_data.dict()
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        log_error(
            message="Post creation failed",
            error_type=ErrorType.SYSTEM_ERROR,
            exception=e,
            context=context,
            post_data=post_data.dict()
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. 미들웨어 교체

#### 2.1 main.py 수정

**Before (Sentry)**:
```python
from fastapi import FastAPI
from nadle_backend.monitoring.sentry_config import init_sentry_for_fastapi
from nadle_backend.middleware.sentry_middleware import SentryRequestMiddleware

app = FastAPI()

# Sentry 초기화
if settings.sentry_dsn:
    init_sentry_for_fastapi(app, settings.sentry_dsn, settings.environment)

# Sentry 미들웨어
app.add_middleware(SentryRequestMiddleware)
```

**After (새 시스템)**:
```python
from fastapi import FastAPI
from nadle_backend.middleware.logging_middleware import (
    StructuredLoggingMiddleware,
    ErrorTrackingMiddleware,
    PerformanceTrackingMiddleware
)
from nadle_backend.logging.structured_logger import structured_logger

app = FastAPI()

# 구조화된 로깅 미들웨어
app.add_middleware(StructuredLoggingMiddleware, log_requests=True, log_responses=True)
app.add_middleware(ErrorTrackingMiddleware, track_4xx=False, track_5xx=True)
app.add_middleware(PerformanceTrackingMiddleware, slow_request_threshold=2.0)

# 로거 초기화 로그
structured_logger.info("Application started", additional_data={"environment": settings.environment})
```

#### 2.2 서비스 계층에서의 사용

**Before (Sentry)**:
```python
from nadle_backend.services.base_service import BaseService
import sentry_sdk

class PostService(BaseService):
    async def create_post(self, post_data: PostCreate) -> Post:
        try:
            # 비즈니스 로직
            post = Post(**post_data.dict())
            await post.save()
            
            # 성공 로깅
            sentry_sdk.add_breadcrumb(
                message="Post created",
                category="business",
                data={"post_id": str(post.id)}
            )
            
            return post
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
```

**After (새 시스템)**:
```python
from nadle_backend.services.base_service import BaseService
from nadle_backend.logging.structured_logger import log_info, log_error, ErrorType

class PostService(BaseService):
    async def create_post(self, post_data: PostCreate, context: LogContext = None) -> Post:
        try:
            log_info("Starting post creation", context=context, post_title=post_data.title)
            
            # 비즈니스 로직
            post = Post(**post_data.dict())
            await post.save()
            
            log_info(
                "Post created successfully",
                context=context,
                post_id=str(post.id),
                author_id=post.author_id
            )
            
            return post
        except ValidationError as e:
            log_error(
                message="Post validation failed",
                error_type=ErrorType.VALIDATION_ERROR,
                exception=e,
                context=context,
                post_data=post_data.dict()
            )
            raise
        except Exception as e:
            log_error(
                message="Post creation failed",
                error_type=ErrorType.SYSTEM_ERROR,
                exception=e,
                context=context,
                post_data=post_data.dict()
            )
            raise
```

## 🎨 프론트엔드 마이그레이션 코드 예시

### 1. 기본 에러 로깅

**Before (수동 console.error)**:
```typescript
try {
  const response = await fetch('/api/posts');
  const data = await response.json();
} catch (error) {
  console.error('Failed to fetch posts:', error);
}
```

**After (구조화된 로깅)**:
```typescript
import { errorLogger } from '~/lib/error-logger';

try {
  const response = await fetch('/api/posts');
  const data = await response.json();
} catch (error) {
  errorLogger.logError({
    message: 'Failed to fetch posts',
    stack: error.stack,
    type: 'network',
    severity: 'medium',
    context: {
      url: '/api/posts',
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      component: 'PostList',
      additionalData: {
        method: 'GET',
        endpoint: '/api/posts'
      }
    }
  });
}
```

### 2. React 컴포넌트 에러 처리

**Before (기본 Error Boundary)**:
```typescript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }

    return this.props.children;
  }
}
```

**After (구조화된 로깅 통합)**:
```typescript
import React from 'react';
import { errorLogger } from '~/lib/error-logger';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    errorLogger.logError({
      message: error.message,
      stack: error.stack,
      type: 'javascript',
      severity: 'high',
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        component: 'ErrorBoundary',
        additionalData: {
          componentStack: errorInfo.componentStack,
          errorBoundary: this.props.name || 'Unknown'
        }
      }
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>오류가 발생했습니다</h2>
          <p>페이지를 새로고침하거나 잠시 후 다시 시도해주세요.</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 3. Hook을 사용한 에러 로깅

**Before (수동 처리)**:
```typescript
import { useState, useEffect } from 'react';

export function useApiCall(url: string) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(url)
      .then(response => response.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('API call failed:', error);
        setError(error);
        setLoading(false);
      });
  }, [url]);

  return { data, loading, error };
}
```

**After (구조화된 로깅)**:
```typescript
import { useState, useEffect } from 'react';
import { useErrorLogger } from '~/lib/error-logger';

export function useApiCall(url: string) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { logError, logPerformance } = useErrorLogger();

  useEffect(() => {
    const startTime = performance.now();
    
    fetch(url)
      .then(response => {
        const duration = performance.now() - startTime;
        
        // 성능 로깅
        logPerformance(`API call: ${url}`, duration, 'useApiCall');
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
      })
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(error => {
        const duration = performance.now() - startTime;
        
        // 에러 로깅
        logError(error, 'useApiCall', {
          url,
          duration,
          method: 'GET'
        });
        
        setError(error);
        setLoading(false);
      });
  }, [url]);

  return { data, loading, error };
}
```

### 4. 성능 모니터링

**Before (수동 측정)**:
```typescript
import { useEffect } from 'react';

export function PostList({ posts }) {
  useEffect(() => {
    const startTime = performance.now();
    
    // 렌더링 완료 후 측정
    setTimeout(() => {
      const duration = performance.now() - startTime;
      console.log(`PostList rendered in ${duration}ms`);
    }, 0);
  }, [posts]);

  return (
    <div>
      {posts.map(post => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
}
```

**After (구조화된 성능 로깅)**:
```typescript
import { useEffect } from 'react';
import { errorLogger } from '~/lib/error-logger';

export function PostList({ posts }) {
  useEffect(() => {
    const startTime = performance.now();
    
    // 렌더링 완료 후 측정
    setTimeout(() => {
      const duration = performance.now() - startTime;
      
      errorLogger.logPerformance({
        operation: 'PostList-render',
        duration,
        component: 'PostList',
        isSlowOperation: duration > 100,
        memoryUsage: (performance as any).memory?.usedJSHeapSize,
        additionalMetrics: {
          postCount: posts.length,
          averageRenderTime: duration / posts.length
        }
      });
    }, 0);
  }, [posts]);

  return (
    <div>
      {posts.map(post => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
}
```

## 🔧 환경 설정 및 초기화

### 1. 백엔드 환경 설정

**requirements.txt 추가**:
```
google-cloud-logging==3.8.0
aiohttp==3.9.0
```

**.env 파일 설정**:
```bash
# Google Cloud Logging
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Discord 알림
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# 로깅 레벨
LOG_LEVEL=INFO
STRUCTURED_LOGGING_ENABLED=true
```

**main.py 전체 수정 예시**:
```python
from fastapi import FastAPI
from nadle_backend.config import settings
from nadle_backend.middleware.logging_middleware import (
    StructuredLoggingMiddleware,
    ErrorTrackingMiddleware,
    PerformanceTrackingMiddleware
)
from nadle_backend.logging.structured_logger import structured_logger

# 애플리케이션 생성
app = FastAPI(title="Nadle Backend API")

# 구조화된 로깅 미들웨어 등록
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(PerformanceTrackingMiddleware)

# 애플리케이션 시작 로그
structured_logger.info(
    "Application starting",
    additional_data={
        "environment": settings.environment,
        "version": "1.0.0",
        "features": ["structured_logging", "discord_notifications", "gcp_logging"]
    }
)

# 기존 라우터 등록
from nadle_backend.routers import auth, posts, comments
app.include_router(auth.router, prefix="/api/auth")
app.include_router(posts.router, prefix="/api/posts")
app.include_router(comments.router, prefix="/api/comments")
```

### 2. 프론트엔드 환경 설정

**app/root.tsx 수정**:
```typescript
import { cssBundleHref } from "@remix-run/css-bundle";
import type { LinksFunction, LoaderFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
} from "@remix-run/react";
import { useEffect } from "react";

import { errorLogger } from "~/lib/error-logger";

export const links: LinksFunction = () => [
  ...(cssBundleHref ? [{ rel: "stylesheet", href: cssBundleHref }] : []),
];

export async function loader({ request }: LoaderFunctionArgs) {
  return json({
    ENV: {
      DISCORD_WEBHOOK_URL: process.env.DISCORD_WEBHOOK_URL,
      NODE_ENV: process.env.NODE_ENV,
    },
  });
}

export default function App() {
  const data = useLoaderData<typeof loader>();

  useEffect(() => {
    // 에러 로거 초기화
    errorLogger.initialize({
      discordWebhookUrl: data.ENV.DISCORD_WEBHOOK_URL,
      isEnabled: data.ENV.NODE_ENV === 'production',
      maxQueueSize: 50,
      flushInterval: 30000, // 30초
    });

    // 사용자 정보 설정 (로그인 상태 확인)
    const user = window.__USER_DATA__;
    if (user) {
      errorLogger.setUserContext(user.id, user.sessionId);
    }
  }, [data.ENV]);

  return (
    <html lang="ko">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
        <LiveReload />
      </body>
    </html>
  );
}
```

## 🧪 테스트 코드 예시

### 1. 백엔드 테스트

```python
import pytest
from nadle_backend.logging.structured_logger import structured_logger, ErrorType, LogContext

@pytest.mark.asyncio
async def test_structured_logging():
    # Given
    context = LogContext(
        user_id="test_user",
        request_id="test_request",
        endpoint="/api/test"
    )
    
    # When
    structured_logger.info("Test message", context=context, test_data="test_value")
    
    # Then
    # 로그 파일이나 출력을 확인하는 테스트
    assert True  # 실제로는 로그 내용 검증

@pytest.mark.asyncio
async def test_error_logging():
    # Given
    context = LogContext(user_id="test_user")
    exception = ValueError("Test error")
    
    # When
    structured_logger.error(
        "Test error occurred",
        ErrorType.VALIDATION_ERROR,
        exception,
        context
    )
    
    # Then
    # Discord 알림 전송 확인 (Mock 사용)
    assert True
```

### 2. 프론트엔드 테스트

```typescript
import { errorLogger } from '~/lib/error-logger';

describe('ErrorLogger', () => {
  beforeEach(() => {
    // Mock Discord webhook
    global.fetch = jest.fn();
  });

  it('should log JavaScript errors', () => {
    // Given
    const error = new Error('Test error');
    
    // When
    errorLogger.logError({
      message: error.message,
      stack: error.stack,
      type: 'javascript',
      severity: 'high'
    });
    
    // Then
    expect(errorLogger.errorQueue).toHaveLength(1);
  });

  it('should measure performance', () => {
    // Given
    const operation = 'test-operation';
    const duration = 150;
    
    // When
    errorLogger.logPerformance({
      operation,
      duration,
      component: 'TestComponent',
      isSlowOperation: true
    });
    
    // Then
    expect(errorLogger.performanceQueue).toHaveLength(1);
  });
});
```

이 마이그레이션 코드 예시들을 통해 기존 Sentry 코드를 단계적으로 새로운 구조화된 로깅 시스템으로 교체할 수 있습니다. 🚀