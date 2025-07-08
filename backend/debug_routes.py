#!/usr/bin/env python3
"""
FastAPI 라우트 디버그
"""

from nadle_backend.routers.posts import router

# 등록된 라우트 출력
print("📋 등록된 Posts 라우트:")
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {list(route.methods)} {route.path}")
        if hasattr(route, 'name'):
            print(f"    Function: {route.name}")
        print()