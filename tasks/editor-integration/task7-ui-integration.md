# Task 7: API 테스트 UI 확장

**Feature Group**: editor-integration  
**Task 제목**: API 테스트 UI 확장  
**작성 시각**: 2025-06-26  
**대상 파일**: `frontend-prototypes/UI.html` (기존 파일 수정)

## 개요

기존 API 테스트용 HTML UI에 에디터 기능을 통합합니다. 마크다운 에디터, 인라인 이미지 업로드, 실시간 미리보기 등의 기능을 추가하여 새로운 콘텐츠 API를 테스트할 수 있는 환경을 구축합니다.

## 리스크 정보

**리스크 레벨**: 낮음

**리스크 설명**:
- 단순 UI 추가로 기존 기능에 영향 없음
- 외부 CDN 의존성 (에디터 라이브러리)
- 브라우저 호환성 고려 필요
- JavaScript 에러 시 기존 기능 영향 최소화

## Subtask 구성

### Subtask 7.1: 마크다운 에디터 통합

**테스트 함수**: `test_markdown_editor_integration()`

**설명**: 
- EasyMDE 마크다운 에디터 추가
- 기존 게시글 작성 폼에 통합
- 에디터 설정 및 커스터마이징

**구현 요구사항**:
```html
<!-- HTML 헤더에 EasyMDE CDN 추가 -->
<link rel="stylesheet" href="https://unpkg.com/easymde/dist/easymde.min.css">
<script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>

<!-- 게시글 작성 섹션 수정 -->
<div class="page" id="createPostPage">
    <div class="card">
        <div class="card-header">
            <h2>📝 게시글 작성 (에디터 통합)</h2>
        </div>
        <div class="card-content">
            <form onsubmit="handleCreatePostWithEditor(event)">
                <!-- 기존 필드들 유지 -->
                <div class="form-group">
                    <label class="form-label">제목</label>
                    <input type="text" class="form-input" name="title" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">서비스</label>
                    <select class="form-input" name="service" required>
                        <option value="">선택하세요</option>
                        <option value="shopping">쇼핑</option>
                        <option value="apartment">아파트</option>
                        <option value="community">커뮤니티</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">게시글 타입</label>
                    <input type="text" class="form-input" name="type" placeholder="예: 자유게시판">
                </div>
                
                <!-- 에디터 타입 선택 -->
                <div class="form-group">
                    <label class="form-label">에디터 타입</label>
                    <select class="form-input" id="editorType" onchange="switchEditor()">
                        <option value="markdown">마크다운 에디터</option>
                        <option value="plain">기본 텍스트</option>
                    </select>
                </div>
                
                <!-- 콘텐츠 입력 영역 -->
                <div class="form-group">
                    <label class="form-label">내용</label>
                    <textarea id="postContentEditor" name="content" required 
                              placeholder="게시글 내용을 입력하세요..." 
                              style="min-height: 300px; resize: vertical;"></textarea>
                </div>
                
                <!-- 미리보기 영역 -->
                <div class="form-group">
                    <div class="editor-controls">
                        <button type="button" onclick="showPreview()" class="btn btn-secondary">미리보기</button>
                        <button type="button" onclick="hidePreview()" class="btn btn-secondary">미리보기 숨기기</button>
                    </div>
                    <div id="contentPreview" class="preview-area" style="display: none;">
                        <h4>미리보기</h4>
                        <div id="previewContent" class="preview-content"></div>
                        <div id="previewMetadata" class="preview-metadata"></div>
                    </div>
                </div>
                
                <!-- 기존 필드들 유지 -->
                <div class="form-group">
                    <label class="form-label">태그 (쉼표로 구분)</label>
                    <input type="text" class="form-input" name="tags" placeholder="태그1, 태그2, 태그3">
                </div>
                
                <!-- 파일 업로드 섹션 확장 -->
                <div class="form-group">
                    <label class="form-label">파일 첨부</label>
                    <div class="file-upload-section">
                        <input type="file" id="fileInput" multiple accept="image/*" style="display: none;">
                        <button type="button" onclick="document.getElementById('fileInput').click()" class="btn btn-secondary">파일 선택</button>
                        <button type="button" onclick="uploadInlineImages()" class="btn btn-secondary">인라인 업로드</button>
                        <div id="uploadStatus" class="upload-status"></div>
                    </div>
                    <div id="uploadedFiles" class="uploaded-files"></div>
                </div>
                
                <button type="submit" class="btn btn-primary">게시글 작성</button>
            </form>
        </div>
    </div>
</div>

<style>
/* 에디터 관련 스타일 */
.editor-controls {
    margin-bottom: 10px;
}

.preview-area {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    margin-top: 10px;
    background: #f9fafb;
}

.preview-content {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 15px;
    background: white;
    min-height: 100px;
    margin-bottom: 10px;
}

.preview-metadata {
    font-size: 0.9em;
    color: #6b7280;
    padding: 10px;
    background: #f3f4f6;
    border-radius: 4px;
}

.upload-status {
    margin-top: 10px;
    font-size: 0.9em;
}

.uploaded-files {
    margin-top: 10px;
}

.file-item {
    display: inline-block;
    margin: 5px;
    padding: 8px 12px;
    background: #e5f3ff;
    border-radius: 4px;
    font-size: 0.9em;
}

.easymde-container {
    z-index: 100;
}
</style>
```

**검증 조건**:
- EasyMDE 에디터 정상 로드
- 마크다운 문법 지원
- 툴바 기능 동작
- 기존 UI와 스타일 일관성

### Subtask 7.2: 인라인 업로드 기능

**테스트 함수**: `test_inline_upload_ui()`

**설명**: 
- 에디터 내 드래그앤드롭 이미지 업로드
- 인라인 업로드 API 연동
- 업로드 진행 상황 표시

**구현 요구사항**:
```javascript
// 전역 변수
let markdownEditor = null;
let currentEditorType = 'markdown';

// 에디터 초기화
function initializeEditor() {
    if (markdownEditor) {
        markdownEditor.toTextArea();
        markdownEditor = null;
    }
    
    const editorType = document.getElementById('editorType').value;
    
    if (editorType === 'markdown') {
        markdownEditor = new EasyMDE({
            element: document.getElementById('postContentEditor'),
            placeholder: '마크다운으로 게시글을 작성하세요...',
            spellChecker: false,
            autosave: {
                enabled: true,
                uniqueId: 'post_content_draft',
                delay: 1000,
            },
            uploadImage: true,
            imageUploadFunction: uploadImageToServer,
            toolbar: [
                'bold', 'italic', 'heading', '|',
                'quote', 'unordered-list', 'ordered-list', '|',
                'link', 'image', '|',
                'preview', 'side-by-side', 'fullscreen', '|',
                {
                    name: 'upload',
                    action: function(editor) {
                        document.getElementById('fileInput').click();
                    },
                    className: 'fa fa-upload',
                    title: '이미지 업로드'
                }
            ],
            shortcuts: {
                'Ctrl-Alt-I': function(editor) {
                    document.getElementById('fileInput').click();
                }
            }
        });
        
        // 드래그앤드롭 이벤트 추가
        setupDragAndDrop();
    }
    
    currentEditorType = editorType;
}

// 에디터 전환
function switchEditor() {
    const content = getCurrentContent();
    initializeEditor();
    setCurrentContent(content);
}

// 현재 콘텐츠 가져오기
function getCurrentContent() {
    if (currentEditorType === 'markdown' && markdownEditor) {
        return markdownEditor.value();
    } else {
        return document.getElementById('postContentEditor').value;
    }
}

// 콘텐츠 설정
function setCurrentContent(content) {
    if (currentEditorType === 'markdown' && markdownEditor) {
        markdownEditor.value(content);
    } else {
        document.getElementById('postContentEditor').value = content;
    }
}

// 드래그앤드롭 설정
function setupDragAndDrop() {
    if (!markdownEditor) return;
    
    const codeMirror = markdownEditor.codemirror;
    
    codeMirror.on('drop', async (cm, e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const files = e.dataTransfer.files;
        if (files.length === 0) return;
        
        const imageFiles = Array.from(files).filter(file => 
            file.type.startsWith('image/')
        );
        
        if (imageFiles.length === 0) {
            showNotification('이미지 파일만 업로드할 수 있습니다.', 'warning');
            return;
        }
        
        for (const file of imageFiles) {
            try {
                showNotification(`이미지 업로드 중: ${file.name}`, 'info');
                
                const result = await uploadInlineImage(file);
                
                // 커서 위치에 마크다운 이미지 삽입
                const cursor = cm.getCursor();
                const imageMarkdown = `\n![${file.name}](${result.url})\n`;
                cm.replaceRange(imageMarkdown, cursor);
                
                showNotification(`이미지 업로드 완료: ${file.name}`, 'success');
                
            } catch (error) {
                console.error('Upload failed:', error);
                showNotification(`업로드 실패: ${file.name} - ${error.message}`, 'error');
            }
        }
    });
    
    // 드래그 오버 스타일링
    codeMirror.on('dragover', (cm, e) => {
        e.preventDefault();
        cm.getWrapperElement().style.backgroundColor = '#f0f9ff';
    });
    
    codeMirror.on('dragleave', (cm, e) => {
        cm.getWrapperElement().style.backgroundColor = '';
    });
}

// 인라인 이미지 업로드
async function uploadInlineImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('authToken');
    if (!token) {
        throw new Error('로그인이 필요합니다');
    }
    
    const response = await fetch('/api/content/upload/inline', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '업로드 실패');
    }
    
    return await response.json();
}

// EasyMDE 업로드 함수 (툴바 버튼용)
async function uploadImageToServer(file, onSuccess, onError) {
    try {
        const result = await uploadInlineImage(file);
        onSuccess(result.url);
    } catch (error) {
        onError(error.message);
    }
}

// 파일 선택 시 인라인 업로드
async function uploadInlineImages() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    
    if (files.length === 0) {
        showNotification('업로드할 파일을 선택해주세요.', 'warning');
        return;
    }
    
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<div class="loading">업로드 중...</div>';
    
    try {
        for (const file of files) {
            if (!file.type.startsWith('image/')) {
                showNotification(`${file.name}은 이미지 파일이 아닙니다.`, 'warning');
                continue;
            }
            
            const result = await uploadInlineImage(file);
            
            // 에디터에 이미지 마크다운 추가
            const imageMarkdown = `![${file.name}](${result.url})`;
            
            if (markdownEditor) {
                const currentValue = markdownEditor.value();
                markdownEditor.value(currentValue + '\n' + imageMarkdown + '\n');
            } else {
                const textarea = document.getElementById('postContentEditor');
                textarea.value += '\n' + imageMarkdown + '\n';
            }
            
            // 업로드된 파일 목록에 추가
            addUploadedFileToList(result);
        }
        
        statusDiv.innerHTML = '<div class="success">업로드 완료!</div>';
        fileInput.value = ''; // 파일 입력 초기화
        
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.innerHTML = `<div class="error">업로드 실패: ${error.message}</div>`;
    }
}

// 업로드된 파일 목록에 추가
function addUploadedFileToList(fileResult) {
    const container = document.getElementById('uploadedFiles');
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <span>${fileResult.filename}</span>
        <button onclick="copyToClipboard('${fileResult.markdown}')" class="btn-sm">마크다운 복사</button>
        <button onclick="copyToClipboard('${fileResult.url}')" class="btn-sm">URL 복사</button>
    `;
    
    container.appendChild(fileItem);
}

// 클립보드 복사
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('클립보드에 복사되었습니다.', 'success');
    }).catch(err => {
        console.error('Copy failed:', err);
        showNotification('복사에 실패했습니다.', 'error');
    });
}
```

**검증 조건**:
- 드래그앤드롭 업로드 동작
- 인라인 업로드 API 연동
- 업로드 진행 상황 표시
- 에러 처리 및 사용자 피드백

### Subtask 7.3: 실시간 미리보기 기능

**테스트 함수**: `test_content_preview_ui()`

**설명**: 
- 마크다운 콘텐츠 실시간 미리보기
- 메타데이터 정보 표시 (단어 수, 읽기 시간)
- 미리보기 API 연동

**구현 요구사항**:
```javascript
// 미리보기 표시
async function showPreview() {
    const content = getCurrentContent();
    const editorType = document.getElementById('editorType').value;
    
    if (!content.trim()) {
        showNotification('미리보기할 내용이 없습니다.', 'warning');
        return;
    }
    
    const previewArea = document.getElementById('contentPreview');
    const previewContent = document.getElementById('previewContent');
    const previewMetadata = document.getElementById('previewMetadata');
    
    // 로딩 표시
    previewContent.innerHTML = '<div class="loading">미리보기 생성 중...</div>';
    previewMetadata.innerHTML = '';
    previewArea.style.display = 'block';
    
    try {
        const response = await fetch('/api/posts/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
            },
            body: JSON.stringify({
                content: content,
                content_type: editorType === 'markdown' ? 'markdown' : 'text'
            })
        });
        
        if (!response.ok) {
            throw new Error(`미리보기 생성 실패: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 미리보기 콘텐츠 표시
        previewContent.innerHTML = result.content_rendered;
        
        // 메타데이터 표시
        previewMetadata.innerHTML = `
            <div class="metadata-item">
                <strong>단어 수:</strong> ${result.word_count}개
            </div>
            <div class="metadata-item">
                <strong>예상 읽기 시간:</strong> ${result.reading_time}분
            </div>
            <div class="metadata-item">
                <strong>인라인 이미지:</strong> ${result.inline_images.length}개
            </div>
            <div class="metadata-item">
                <strong>처리 시간:</strong> ${(result.processing_time * 1000).toFixed(1)}ms
            </div>
        `;
        
        // 인라인 이미지 정보 표시
        if (result.inline_images.length > 0) {
            const imageList = result.inline_images.map(id => `<code>${id}</code>`).join(', ');
            previewMetadata.innerHTML += `
                <div class="metadata-item">
                    <strong>이미지 파일 ID:</strong> ${imageList}
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Preview error:', error);
        previewContent.innerHTML = `<div class="error">미리보기 생성 실패: ${error.message}</div>`;
        previewMetadata.innerHTML = '';
    }
}

// 미리보기 숨기기
function hidePreview() {
    document.getElementById('contentPreview').style.display = 'none';
}

// 자동 미리보기 (선택적 기능)
let previewTimeout = null;

function setupAutoPreview() {
    if (!markdownEditor) return;
    
    markdownEditor.codemirror.on('change', () => {
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
            if (document.getElementById('contentPreview').style.display !== 'none') {
                showPreview();
            }
        }, 2000); // 2초 후 자동 미리보기
    });
}

// 미리보기 토글
function togglePreview() {
    const previewArea = document.getElementById('contentPreview');
    if (previewArea.style.display === 'none') {
        showPreview();
    } else {
        hidePreview();
    }
}
```

**검증 조건**:
- 실시간 미리보기 API 연동
- 메타데이터 정확한 표시
- 로딩 및 에러 상태 처리
- 성능 최적화 (디바운싱)

### Subtask 7.4: API 테스트 인터페이스

**테스트 함수**: `test_content_api_testing()`

**설명**: 
- 새로운 콘텐츠 API 테스트 인터페이스
- API 응답 형식 확인
- 테스트 시나리오 실행

**구현 요구사항**:
```javascript
// 에디터 통합 게시글 생성
async function handleCreatePostWithEditor(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // 현재 에디터 콘텐츠 가져오기
    const content = getCurrentContent();
    const editorType = document.getElementById('editorType').value;
    
    // 게시글 데이터 구성
    const postData = {
        title: formData.get('title'),
        content: content,
        service: formData.get('service'),
        metadata: {
            type: formData.get('type') || null,
            tags: formData.get('tags') ? 
                formData.get('tags').split(',').map(tag => tag.trim()).slice(0, 3) : [],
            visibility: 'public',
            editor_type: editorType,
            file_ids: getCurrentFileIds() // 첨부된 파일 ID 목록
        }
    };
    
    try {
        // 로딩 상태 표시
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = '작성 중...';
        submitButton.disabled = true;
        
        const response = await fetch('/api/posts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(postData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '게시글 작성 실패');
        }
        
        const result = await response.json();
        
        showNotification('게시글이 성공적으로 작성되었습니다!', 'success');
        
        // 폼 초기화
        form.reset();
        if (markdownEditor) {
            markdownEditor.value('');
        }
        
        // 업로드된 파일 목록 초기화
        document.getElementById('uploadedFiles').innerHTML = '';
        
        // 게시글 목록 새로고침
        if (typeof loadPosts === 'function') {
            loadPosts();
        }
        
        // API 응답 로깅 (개발용)
        console.log('Post created:', result);
        
        // 테스트용 응답 표시
        displayApiResponse('게시글 생성', result);
        
    } catch (error) {
        console.error('Create post error:', error);
        showNotification(`게시글 작성 실패: ${error.message}`, 'error');
    } finally {
        // 버튼 상태 복원
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

// 현재 첨부된 파일 ID 목록 가져오기
function getCurrentFileIds() {
    const fileItems = document.querySelectorAll('#uploadedFiles .file-item');
    const fileIds = [];
    
    fileItems.forEach(item => {
        const fileId = item.dataset.fileId;
        if (fileId) {
            fileIds.push(fileId);
        }
    });
    
    return fileIds;
}

// API 응답 표시 (테스트용)
function displayApiResponse(operation, response) {
    // API 테스트 결과를 표시하는 모달이나 패널이 있다면 활용
    if (typeof showApiTestResult === 'function') {
        showApiTestResult(operation, response);
    }
    
    // 콘솔에 상세 정보 출력
    console.group(`API Test: ${operation}`);
    console.log('Response:', response);
    console.log('Status: Success');
    console.log('Timestamp:', new Date().toISOString());
    console.groupEnd();
}

// 에디터 기능 테스트
async function testEditorFeatures() {
    const tests = [
        {
            name: '마크다운 렌더링 테스트',
            action: async () => {
                const testContent = `# 테스트 제목\n\n**볼드 텍스트**와 *이탤릭 텍스트*\n\n- 리스트 아이템 1\n- 리스트 아이템 2`;
                setCurrentContent(testContent);
                await showPreview();
                return '마크다운 렌더링 완료';
            }
        },
        {
            name: '미리보기 API 테스트',
            action: async () => {
                const testContent = 'API 테스트용 콘텐츠입니다.';
                const response = await fetch('/api/posts/preview', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        content: testContent,
                        content_type: 'markdown'
                    })
                });
                const result = await response.json();
                return `미리보기 생성됨 (${result.word_count}단어, ${result.reading_time}분)`;
            }
        }
    ];
    
    console.log('에디터 기능 테스트 시작');
    
    for (const test of tests) {
        try {
            console.log(`실행 중: ${test.name}`);
            const result = await test.action();
            console.log(`✓ ${test.name}: ${result}`);
        } catch (error) {
            console.error(`✗ ${test.name}: ${error.message}`);
        }
    }
    
    console.log('에디터 기능 테스트 완료');
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 에디터 초기화
    initializeEditor();
    
    // 자동 미리보기 설정
    setupAutoPreview();
    
    // 파일 입력 이벤트 리스너
    document.getElementById('fileInput').addEventListener('change', function() {
        if (this.files.length > 0) {
            uploadInlineImages();
        }
    });
    
    // 테스트 메뉴에 에디터 테스트 추가
    if (typeof addTestMenuItem === 'function') {
        addTestMenuItem('에디터 기능 테스트', testEditorFeatures);
    }
});
```

**검증 조건**:
- 새로운 API 엔드포인트 테스트
- 에디터 통합 게시글 생성
- API 응답 형식 검증
- 테스트 시나리오 자동화

## 의존성 정보

**선행 조건**: 
- Task 3, 4의 API 엔드포인트 구현
- 기존 UI.html의 구조 및 스타일

**외부 라이브러리**:
- `EasyMDE` - 마크다운 에디터 (CDN)
- `Font Awesome` - 아이콘 (기존 사용 중)

**후속 작업**: 
- 실제 프로덕션 UI에서 참고할 구현 패턴 제공

## 테스트 요구사항

### 기능 테스트
```javascript
function test_markdown_editor_integration() {
    // EasyMDE 로드 확인
    // 마크다운 문법 동작 확인
    // 툴바 기능 테스트
}

function test_inline_upload_ui() {
    // 드래그앤드롭 업로드
    // 파일 선택 업로드
    // 에러 처리 확인
}

function test_content_preview_ui() {
    // 미리보기 생성
    // 메타데이터 표시
    // 실시간 업데이트
}

function test_content_api_testing() {
    // API 엔드포인트 호출
    // 응답 데이터 검증
    // 에러 시나리오 테스트
}
```

### 브라우저 호환성 테스트
- Chrome, Firefox, Safari, Edge
- 모바일 브라우저 (반응형)
- JavaScript 비활성화 시 대응

### 성능 테스트
- 대용량 마크다운 문서 처리
- 다중 이미지 업로드
- 메모리 사용량 모니터링

## 구현 참고사항

### 1. 사용자 경험 우선
- 직관적인 인터페이스
- 명확한 피드백 메시지
- 빠른 응답 시간

### 2. 에러 처리 강화
- 네트워크 오류 대응
- 파일 업로드 실패 처리
- 사용자 친화적 에러 메시지

### 3. 성능 최적화
- 디바운싱을 통한 API 호출 최적화
- 이미지 프리로딩
- 메모리 누수 방지

### 4. 접근성 고려
- 키보드 네비게이션 지원
- 스크린 리더 호환성
- 고대비 테마 지원

이 Task는 개발된 API의 실제 동작을 검증하고 사용자 경험을 테스트할 수 있는 중요한 인터페이스를 제공합니다.