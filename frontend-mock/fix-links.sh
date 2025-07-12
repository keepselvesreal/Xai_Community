#!/bin/bash

# 모든 HTML 파일의 사이드바 링크를 올바른 파일명으로 수정

for file in *.html; do
    echo "Fixing links in $file..."
    
    # 홈 링크 수정
    sed -i 's|href="#" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"|href="index.html" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"|g' "$file"
    sed -i 's|href="index.html" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"|href="index.html" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"|g' "$file"
    
    # 게시판 링크 수정
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600">.*게시판|href="board-index.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"><span class="mr-3">📝</span>게시판|g' "$file"
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*게시판|href="board-index.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">📝</span>게시판|g' "$file"
    
    # 정보 링크 수정  
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600">.*정보|href="info.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"><span class="mr-3">ℹ️</span>정보|g' "$file"
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*정보|href="info.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">ℹ️</span>정보|g' "$file"
    
    # 서비스 링크 수정
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600">.*입주 업체 서비스|href="services.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"><span class="mr-3">🏢</span>입주 업체 서비스|g' "$file"
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*입주 업체 서비스|href="services.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">🏢</span>입주 업체 서비스|g' "$file"
    
    # 꿀정보 링크 수정
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600">.*전문가 꿀정보|href="tips.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-white bg-blue-600"><span class="mr-3">💡</span>전문가 꿀정보|g' "$file"
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*전문가 꿀정보|href="tips.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">💡</span>전문가 꿀정보|g' "$file"
    
    # 마이페이지 링크 수정
    sed -i 's|href="#" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*마이페이지|href="mypage.html" class="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">👤</span>마이페이지|g' "$file"
    
    # 로그아웃 링크 수정
    sed -i 's|href="#" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">.*로그아웃|href="auth-login.html" class="mt-1 group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900"><span class="mr-3">🚪</span>로그아웃|g' "$file"
    
done

echo "All links fixed!"