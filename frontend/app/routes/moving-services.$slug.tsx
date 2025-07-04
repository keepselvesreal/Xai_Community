import { useState, useEffect } from "react";
import { type MetaFunction } from "@remix-run/node";
import { useParams, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import { convertPostToService } from "~/types/service-types";
import type { Service } from "~/types/service-types";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "서비스 상세 정보" },
  ];
};

export default function ServiceDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  
  const [service, setService] = useState<Service | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [reviewText, setReviewText] = useState("");
  const [isLiked, setIsLiked] = useState(false);
  const [selectedRating, setSelectedRating] = useState(0);
  const [showInquiryForm, setShowInquiryForm] = useState(false);
  const [inquiryTitle, setInquiryTitle] = useState("");
  const [inquiryContent, setInquiryContent] = useState("");
  const [inquiryContact, setInquiryContact] = useState("");
  const [isInquiryPublic, setIsInquiryPublic] = useState(true);
  const [comments, setComments] = useState<any[]>([]);
  const [isLoadingComments, setIsLoadingComments] = useState(false);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState("");
  const [replyContentMap, setReplyContentMap] = useState<{[key: string]: string}>({});
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editContentMap, setEditContentMap] = useState<{[key: string]: string}>({});

  // 🔄 서버에서 최신 통계 데이터 재로드 함수 (재사용 가능)
  const refreshServiceStats = async (): Promise<void> => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        const updatedService = convertPostToService(response.data);
        if (updatedService) {
          setService(updatedService);
          console.log('🔄 Service stats refreshed from server:', updatedService.serviceStats);
        }
      }
    } catch (error) {
      console.warn('⚠️ Failed to refresh service stats:', error);
    }
  };

  const loadService = async () => {
    if (!slug) return;
    
    console.log('🔍 Loading service with slug:', slug);
    setIsLoading(true);
    
    try {
      // 기존 안정적인 API 사용
      const response = await apiClient.getPost(slug);
      console.log('📡 API response:', response);
      
      if (response.success && response.data) {
        console.log('📦 Raw post data:', response.data);
        console.log('📦 Raw post data keys:', Object.keys(response.data));
        console.log('📦 Raw post data structure:', {
          hasData: 'data' in response.data,
          hasContent: 'content' in response.data,
          hasMetadata: 'metadata' in response.data,
          hasExtendedStats: 'extended_stats' in response.data,
          hasStats: 'stats' in response.data,
          dataKeys: Object.keys(response.data)
        });
        
        // 🚨 확장 통계 데이터 상세 디버깅
        console.log('📊 Extended stats debug:', {
          extended_stats: response.data.extended_stats,
          stats: response.data.stats,
          view_count: response.data.view_count,
          comment_count: response.data.comment_count,
          bookmark_count: response.data.bookmark_count
        });
        
        // Post 데이터를 Service로 변환
        const serviceData = convertPostToService(response.data);
        if (serviceData) {
          // 🔍 디버깅: 작성자 정보 상세 로깅
          console.log('🔍 Service author debugging:', {
            originalPostData: response.data,
            originalAuthor: response.data.author,
            originalAuthorId: response.data.author_id,
            convertedServiceData: serviceData,
            serviceAuthor: serviceData.author,
            serviceAuthorId: serviceData.author_id
          });
          
          setService(serviceData);
          
          // 사용자의 북마크 상태 설정
          if (response.data.user_reaction) {
            setIsLiked(response.data.user_reaction.bookmarked || false);
          }
        } else {
          console.error('❌ Service conversion failed');
          console.log('❌ Failed post data structure:', {
            hasContent: !!response.data.content,
            hasMetadata: !!response.data.metadata,
            metadataType: response.data.metadata?.type,
            contentPreview: response.data.content?.substring(0, 100)
          });
          setIsNotFound(true);
          showError('서비스 데이터 변환에 실패했습니다');
        }
      } else {
        console.error('❌ API call failed', response);
        setIsNotFound(true);
        showError('서비스를 찾을 수 없습니다');
      }
    } catch (error) {
      console.error('🚨 Error loading service:', error);
      setIsNotFound(true);
      showError('서비스를 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  // 데이터 변환 유틸리티 함수
  const ensureId = (item: any) => {
    const processedItem = {
      ...item,
      id: item.id || item._id
    };
    
    // author 정보 처리
    if (processedItem.author) {
      processedItem.author = {
        ...processedItem.author,
        id: processedItem.author.id || processedItem.author._id
      };
    }
    
    return processedItem;
  };

  // 재귀적 댓글 데이터 처리
  const processCommentsRecursive = (comments: any[]): any[] => {
    return comments.map(comment => {
      const processedComment = ensureId(comment);
      if (processedComment.replies && processedComment.replies.length > 0) {
        processedComment.replies = processCommentsRecursive(processedComment.replies);
      }
      return processedComment;
    });
  };

  const loadComments = async () => {
    if (!slug) return;
    
    setIsLoadingComments(true);
    try {
      const response = await apiClient.getComments(slug);
      if (response.success && response.data) {
        const processedComments = processCommentsRecursive(response.data.comments || []);
        console.log('📦 Processed comments:', processedComments);
        setComments(processedComments);
      }
    } catch (error) {
      console.error('댓글 불러오기 오류:', error);
    } finally {
      setIsLoadingComments(false);
    }
  };

  useEffect(() => {
    loadService();
    loadComments();
  }, [slug]);

  // 로딩 상태
  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4">⏳</div>
            <p className="text-var-secondary">서비스 정보를 불러오는 중...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  // 404 상태
  if (isNotFound || !service) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4">❌</div>
            <h3 className="text-xl font-semibold text-red-600 mb-2">서비스를 찾을 수 없습니다</h3>
            <p className="text-var-secondary mb-4">요청하신 서비스가 존재하지 않거나 삭제되었을 수 있습니다.</p>
            <button
              onClick={() => navigate('/services')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              서비스 목록으로 돌아가기
            </button>
          </div>
        </div>
      </AppLayout>
    );
  }

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  const renderInteractiveStars = (rating: number, onRatingChange: (rating: number) => void) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      const isHalfFilled = rating >= i - 0.5 && rating < i;
      const isFilled = rating >= i;
      const isEmpty = rating < i - 0.5;
      
      stars.push(
        <div key={i} className="relative inline-block cursor-pointer group">
          {/* 기본 회색 별 */}
          <span className="text-gray-300 text-2xl select-none">★</span>
          
          {/* 채워진 별 (전체) */}
          {isFilled && (
            <span className="absolute inset-0 text-yellow-400 text-2xl overflow-hidden select-none transition-colors duration-200">
              ★
            </span>
          )}
          
          {/* 반 채워진 별 */}
          {isHalfFilled && (
            <span 
              className="absolute inset-0 text-yellow-400 text-2xl overflow-hidden select-none transition-colors duration-200" 
              style={{ width: '50%' }}
            >
              ★
            </span>
          )}
          
          {/* 호버 효과 - 왼쪽 반 */}
          <div 
            className="absolute inset-0 w-1/2 h-full opacity-0 hover:opacity-100 transition-opacity duration-200"
            onMouseEnter={() => {
              // 호버 시 미리보기 효과 (선택사항)
            }}
          >
            <span className="text-yellow-200 text-2xl select-none">★</span>
          </div>
          
          {/* 호버 효과 - 오른쪽 반 */}
          <div 
            className="absolute inset-0 w-1/2 h-full ml-auto opacity-0 hover:opacity-100 transition-opacity duration-200"
            onMouseEnter={() => {
              // 호버 시 미리보기 효과 (선택사항)
            }}
          >
            <span className="text-yellow-200 text-2xl select-none">★</span>
          </div>
          
          {/* 클릭 영역 - 왼쪽 반 (0.5점) */}
          <button 
            className="absolute inset-0 w-1/2 h-full opacity-0 cursor-pointer hover:bg-yellow-100 hover:opacity-20 rounded-l transition-all duration-200"
            onClick={(e) => {
              e.stopPropagation();
              onRatingChange(i - 0.5);
            }}
            title={`${i - 0.5}점`}
          />
          
          {/* 클릭 영역 - 오른쪽 반 (1점) */}
          <button 
            className="absolute inset-0 w-1/2 h-full ml-auto opacity-0 cursor-pointer hover:bg-yellow-100 hover:opacity-20 rounded-r transition-all duration-200"
            onClick={(e) => {
              e.stopPropagation();
              onRatingChange(i);
            }}
            title={`${i}점`}
          />
        </div>
      );
    }
    return stars;
  };

  const handleBackClick = () => {
    navigate('/services');
  };

  const handleInquiry = () => {
    window.open(`tel:${service.contact.phone}`);
  };

  const handleLike = async () => {
    if (!service) return;
    
    try {
      const response = await apiClient.bookmarkPost(service.slug || service.postId || '');
      
      if (response.success) {
        // 북마크 상태 업데이트
        setIsLiked(!isLiked);
        
        // 여러 방법으로 bookmark_count 접근 시도
        const bookmarkCount = response.data?.bookmark_count ?? 
                              response.data?.data?.bookmark_count ??
                              response.bookmark_count ??
                              (response.data?.action === 'unbookmarked' ? 0 : 
                               response.data?.action === 'bookmarked' ? 1 : undefined);
        
        // 서비스 데이터 업데이트
        setService(prev => {
          if (!prev) return null;
          return {
            ...prev,
            bookmarks: bookmarkCount !== undefined ? bookmarkCount : prev.bookmarks,
            stats: {
              ...prev.stats,
              bookmark_count: bookmarkCount !== undefined ? bookmarkCount : prev.stats?.bookmark_count || 0
            },
            serviceStats: {
              ...prev.serviceStats,
              bookmarks: bookmarkCount !== undefined ? bookmarkCount : prev.serviceStats?.bookmarks || 0
            }
          };
        });
        
        const action = response.action || (isLiked ? '해제' : '추가');
        showSuccess(`관심 목록에서 ${action}되었습니다`);
      } else {
        console.error('❌ 북마크 API 실패:', response);
        showError('관심 설정에 실패했습니다');
      }
    } catch (error) {
      console.error('🚨 북마크 처리 오류:', error);
      showError('관심 설정 중 오류가 발생했습니다');
    }
  };

  const handleReviewSubmit = async () => {
    if (reviewText.trim() && selectedRating > 0) {
      try {
        const response = await apiClient.createServiceReview(slug!, {
          content: `평점: ${selectedRating}점\n\n${reviewText}`
        });
        
        if (response.success) {
          showSuccess('후기가 등록되었습니다!');
          setReviewText('');
          setSelectedRating(0);
          
          // 🚀 실시간 후기 통계 반영
          setService(prev => {
            if (!prev) return null;
            return {
              ...prev,
              serviceStats: {
                ...prev.serviceStats,
                reviews: (prev.serviceStats?.reviews || 0) + 1
              },
              // stats 객체도 함께 업데이트
              stats: {
                ...prev.stats,
                review_count: (prev.stats?.review_count || 0) + 1
              }
            };
          });
          
          // 댓글 새로고침하여 새로운 후기 표시
          await loadComments();
          
          // 📡 서버에서 최신 통계 데이터 재로드 (안전장치)
          setTimeout(() => {
            refreshServiceStats();
          }, 500);
        } else {
          showError('후기 등록에 실패했습니다');
        }
      } catch (error) {
        console.error('후기 등록 오류:', error);
        showError('후기 등록 중 오류가 발생했습니다');
      }
    } else {
      showError('별점과 후기 내용을 모두 입력해주세요.');
    }
  };

  const handleReplySubmit = async (commentId: string) => {
    const content = replyContentMap[commentId] || '';
    console.log('🔍 Reply submit:', { commentId, content, slug });
    
    if (!content.trim()) {
      showError('답글 내용을 입력해주세요.');
      return;
    }

    if (!commentId || commentId === 'undefined') {
      console.error('❌ Invalid commentId:', commentId);
      showError('답글을 작성할 댓글을 찾을 수 없습니다.');
      return;
    }

    try {
      const response = await apiClient.createReply(slug!, commentId, content);
      if (response.success) {
        showSuccess('답글이 등록되었습니다!');
        setReplyContentMap(prev => ({ ...prev, [commentId]: '' }));
        setReplyingTo(null);
        await loadComments();
      } else {
        showError('답글 등록에 실패했습니다');
      }
    } catch (error) {
      console.error('답글 등록 오류:', error);
      showError('답글 등록 중 오류가 발생했습니다');
    }
  };

  // 재귀적 답글 렌더링 컴포넌트
  const renderReply = (reply: any, depth: number = 0, maxDepth: number = 3) => {
    const isMaxDepth = depth >= maxDepth;
    const isOwner = isCommentOwner(reply);
    
    return (
      <div key={reply.id} className={`bg-gray-50 rounded-lg p-3 ${depth > 0 ? 'ml-4' : ''}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-blue-600">
              {reply.author?.display_name || reply.author?.user_handle || '익명'}
            </span>
            <span className="text-xs text-var-muted">
              {new Date(reply.created_at).toLocaleDateString()}
            </span>
          </div>
          {/* 작성자 수정/삭제 버튼 */}
          {isOwner && (
            <div className="flex items-center gap-2">
              <button 
                className="text-xs text-gray-600 hover:text-blue-600 transition-colors"
                onClick={() => handleEditReply(reply.id)}
              >
                {editingComment === reply.id ? '저장' : '수정'}
              </button>
              <button 
                className="text-xs text-gray-600 hover:text-red-600 transition-colors"
                onClick={() => handleDeleteReply(reply.id)}
              >
                삭제
              </button>
            </div>
          )}
        </div>
        {/* 수정 모드인 경우 텍스트 영역, 아닌 경우 일반 텍스트 */}
        {editingComment === reply.id ? (
          <div className="space-y-3">
            <textarea
              value={editContentMap[reply.id] || ''}
              onChange={(e) => setEditContentMap(prev => ({ ...prev, [reply.id]: e.target.value }))}
              className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
              rows={3}
              placeholder="답글 내용을 수정해주세요..."
            />
            <div className="flex gap-2">
              <button
                onClick={() => handleEditReply(reply.id)}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                disabled={!(editContentMap[reply.id] || '').trim()}
              >
                저장
              </button>
              <button
                onClick={() => {
                  setEditingComment(null);
                  setEditContentMap(prev => ({ ...prev, [reply.id]: '' }));
                }}
                className="px-3 py-1 border border-gray-300 text-sm rounded hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-var-secondary whitespace-pre-line">
            {reply.content}
          </p>
        )}
        
        {/* 답글 버튼 (최대 깊이가 아닌 경우에만) */}
        {user && !isMaxDepth && (
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={() => setReplyingTo(replyingTo === reply.id ? null : reply.id)}
              className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >
              {replyingTo === reply.id ? '답글 취소' : '답글'}
            </button>
          </div>
        )}

        {/* 답글 작성 폼 */}
        {replyingTo === reply.id && (
          <div className="mt-3 pl-4 border-l-2 border-blue-200">
            <textarea
              value={replyContentMap[reply.id] || ''}
              onChange={(e) => setReplyContentMap(prev => ({ ...prev, [reply.id]: e.target.value }))}
              placeholder="답글을 작성해주세요..."
              className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
              rows={3}
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => {
                  console.log('🔘 Nested reply button clicked for:', reply.id);
                  handleReplySubmit(reply.id);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                disabled={!(replyContentMap[reply.id] || '').trim()}
              >
                답글 작성
              </button>
              <button
                onClick={() => {
                  setReplyingTo(null);
                  setReplyContentMap(prev => ({ ...prev, [reply.id]: '' }));
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        )}
        
        {/* 중첩된 답글들 */}
        {reply.replies && reply.replies.length > 0 && (
          <div className="mt-4 space-y-3">
            {reply.replies.map((nestedReply: any) => renderReply(nestedReply, depth + 1, maxDepth))}
          </div>
        )}
        
        {/* 최대 깊이 도달 안내 */}
        {isMaxDepth && reply.replies && reply.replies.length > 0 && (
          <div className="mt-2 text-xs text-gray-500 italic">
            💡 더 깊은 답글은 지원되지 않습니다 (최대 {maxDepth}단계)
          </div>
        )}
      </div>
    );
  };

  // 서비스 업체 글 작성자 확인 함수
  const isServiceOwner = () => {
    if (!user || !service) {
      console.log('🔍 Service owner check - missing data:', { hasUser: !!user, hasService: !!service });
      return false;
    }

    // 🔍 현재 사용자 정보 상세 로깅
    console.log('🔍 Current user info:', {
      user: user,
      userId: user.id,
      userHandle: user.user_handle,
      userEmail: user.email,
      userType: typeof user.id
    });
    
    // service에서 작성자 정보 확인 (여러 가능한 필드 체크)
    const possibleAuthorFields = [
      service.author,
      service.author_id, 
      service.user_id,
      service.created_by,
      service.originalAuthor,
      service.postAuthor
    ];
    
    console.log('🔍 Service owner check - all possible author fields:', {
      service: service,
      author: service.author,
      author_id: service.author_id,
      user_id: service.user_id,
      created_by: service.created_by,
      originalAuthor: service.originalAuthor,
      postAuthor: service.postAuthor,
      possibleAuthorFields: possibleAuthorFields.filter(field => field !== undefined)
    });
    
    // 각 가능한 작성자 필드에 대해 확인
    for (const authorInfo of possibleAuthorFields) {
      if (!authorInfo) continue;
      
      console.log('🔍 Checking author field:', { authorInfo, type: typeof authorInfo });
      
      // 여러 방법으로 소유권 확인
      let userIdMatch = false;
      let userHandleMatch = false;
      let emailMatch = false;
      
      if (typeof authorInfo === 'string') {
        // 문자열인 경우 ID로 간주
        userIdMatch = authorInfo === user.id;
      } else if (typeof authorInfo === 'object' && authorInfo !== null) {
        // 객체인 경우 여러 필드 확인
        userIdMatch = authorInfo.id === user.id || authorInfo._id === user.id || authorInfo.user_id === user.id;
        userHandleMatch = authorInfo.user_handle === user.user_handle;
        emailMatch = authorInfo.email === user.email;
      }
      
      const isOwnerForThisField = userIdMatch || userHandleMatch || emailMatch;
      
      console.log('🔍 Service owner check for field:', { 
        authorInfo,
        isOwnerForThisField,
        userIdMatch,
        userHandleMatch,
        emailMatch,
        userId: user.id, 
        userHandle: user.user_handle,
        userEmail: user.email
      });
      
      if (isOwnerForThisField) {
        console.log('✅ Service ownership confirmed via field:', authorInfo);
        return true;
      }
    }
    
    console.log('❌ Service ownership not confirmed for any field');
    return false;
  };

  // 댓글 작성자 확인 함수
  const isCommentOwner = (comment: any) => {
    if (!user || !comment.author) {
      console.log('🔍 Owner check - missing data:', { hasUser: !!user, hasAuthor: !!comment.author });
      return false;
    }
    
    // 여러 방법으로 소유권 확인
    const userIdMatch = comment.author.id === user.id;
    const userHandleMatch = comment.author.user_handle === user.user_handle;
    const emailMatch = comment.author.email === user.email;
    
    const isOwner = userIdMatch || userHandleMatch || emailMatch;
    
    console.log('🔍 Owner check:', { 
      isOwner, 
      userIdMatch,
      userHandleMatch,
      emailMatch,
      userId: user.id, 
      userHandle: user.user_handle,
      userEmail: user.email,
      authorId: comment.author.id, 
      authorHandle: comment.author.user_handle,
      authorEmail: comment.author.email
    });
    
    return isOwner;
  };

  // 댓글 수정 함수
  const handleEditComment = async (commentId: string) => {
    console.log('🖊️ Edit comment:', commentId);
    
    if (editingComment === commentId) {
      // 수정 모드에서 저장
      const newContent = editContentMap[commentId];
      if (!newContent || !newContent.trim()) {
        showError('내용을 입력해주세요.');
        return;
      }
      
      try {
        const response = await apiClient.updateComment(slug!, commentId, newContent.trim());
        if (response.success) {
          showSuccess('댓글이 수정되었습니다.');
          setEditingComment(null);
          setEditContentMap(prev => ({ ...prev, [commentId]: '' }));
          await loadComments();
        } else {
          showError('댓글 수정에 실패했습니다.');
        }
      } catch (error) {
        console.error('댓글 수정 오류:', error);
        showError('댓글 수정 중 오류가 발생했습니다.');
      }
    } else {
      // 수정 모드 활성화
      const comment = comments.find(c => c.id === commentId);
      if (comment) {
        setEditingComment(commentId);
        setEditContentMap(prev => ({ ...prev, [commentId]: comment.content }));
        // 다른 수정/답글 모드 취소
        setReplyingTo(null);
      }
    }
  };

  // 댓글 삭제 함수
  const handleDeleteComment = async (commentId: string) => {
    console.log('🗑️ Delete comment:', commentId);
    if (confirm('정말 삭제하시겠습니까?')) {
      try {
        const response = await apiClient.deleteComment(slug!, commentId);
        if (response.success) {
          showSuccess('댓글이 삭제되었습니다.');
          await loadComments();
        } else {
          showError('댓글 삭제에 실패했습니다.');
        }
      } catch (error) {
        console.error('댓글 삭제 오류:', error);
        showError('댓글 삭제 중 오류가 발생했습니다.');
      }
    }
  };

  // 답글 수정 함수
  const handleEditReply = async (replyId: string) => {
    console.log('🖊️ Edit reply:', replyId);
    
    if (editingComment === replyId) {
      // 수정 모드에서 저장
      const newContent = editContentMap[replyId];
      if (!newContent || !newContent.trim()) {
        showError('내용을 입력해주세요.');
        return;
      }
      
      try {
        const response = await apiClient.updateComment(slug!, replyId, newContent.trim());
        if (response.success) {
          showSuccess('답글이 수정되었습니다.');
          setEditingComment(null);
          setEditContentMap(prev => ({ ...prev, [replyId]: '' }));
          await loadComments();
        } else {
          showError('답글 수정에 실패했습니다.');
        }
      } catch (error) {
        console.error('답글 수정 오류:', error);
        showError('답글 수정 중 오류가 발생했습니다.');
      }
    } else {
      // 수정 모드 활성화 - 중첩된 답글에서 답글 찾기
      const findReplyInComments = (comments: any[], targetId: string): any => {
        for (const comment of comments) {
          if (comment.id === targetId) return comment;
          if (comment.replies) {
            const found = findReplyInComments(comment.replies, targetId);
            if (found) return found;
          }
        }
        return null;
      };
      
      const reply = findReplyInComments(comments, replyId);
      if (reply) {
        setEditingComment(replyId);
        setEditContentMap(prev => ({ ...prev, [replyId]: reply.content }));
        // 다른 수정/답글 모드 취소
        setReplyingTo(null);
      }
    }
  };

  // 답글 삭제 함수
  const handleDeleteReply = async (replyId: string) => {
    console.log('🗑️ Delete reply:', replyId);
    if (confirm('정말 삭제하시겠습니까?')) {
      try {
        const response = await apiClient.deleteComment(slug!, replyId);
        if (response.success) {
          showSuccess('답글이 삭제되었습니다.');
          await loadComments();
        } else {
          showError('답글 삭제에 실패했습니다.');
        }
      } catch (error) {
        console.error('답글 삭제 오류:', error);
        showError('답글 삭제 중 오류가 발생했습니다.');
      }
    }
  };

  const handleEditService = () => {
    if (!service) return;
    
    // 수정 페이지로 이동 (slug를 파라미터로 전달)
    navigate(`/services/write?edit=${service.slug || service.postId}`);
  };

  const handleDeleteService = async () => {
    if (!service) return;
    
    // 삭제 확인 다이얼로그
    const confirmDelete = window.confirm(
      `정말로 "${service.name}" 업체 정보를 삭제하시겠습니까?\n\n삭제된 정보는 복구할 수 없습니다.`
    );
    
    if (!confirmDelete) return;
    
    try {
      console.log('🗑️ Deleting service:', service.slug || service.postId);
      
      // API 클라이언트의 deletePost 메서드 사용
      const response = await apiClient.deletePost(service.slug || service.postId || '');
      
      if (response.success) {
        showSuccess('업체 정보가 삭제되었습니다.');
        
        // 서비스 목록 페이지로 리다이렉트
        navigate('/services');
      } else {
        console.error('❌ Service deletion failed:', response);
        showError('업체 정보 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('🚨 업체 정보 삭제 오류:', error);
      showError('업체 정보 삭제 중 오류가 발생했습니다.');
    }
  };

  const handleInquirySubmit = async () => {
    if (inquiryTitle.trim() && inquiryContent.trim()) {
      try {
        console.log('🔍 Submitting inquiry:', { 
          slug, 
          title: inquiryTitle, 
          content: inquiryContent, 
          isPublic: isInquiryPublic 
        });
        
        const response = await apiClient.createServiceInquiry(slug!, {
          content: `제목: ${inquiryTitle}\n\n${inquiryContent}${inquiryContact ? `\n\n연락처: ${inquiryContact}` : ''}`,
          metadata: {
            isPublic: isInquiryPublic
          }
        });
        
        if (response.success) {
          showSuccess('문의가 등록되었습니다!');
          setInquiryTitle('');
          setInquiryContent('');
          setInquiryContact('');
          setIsInquiryPublic(true);
          setShowInquiryForm(false);
          
          // 🚀 실시간 문의 통계 반영
          setService(prev => {
            if (!prev) return null;
            return {
              ...prev,
              serviceStats: {
                ...prev.serviceStats,
                inquiries: (prev.serviceStats?.inquiries || 0) + 1
              },
              // stats 객체도 함께 업데이트
              stats: {
                ...prev.stats,
                inquiry_count: (prev.stats?.inquiry_count || 0) + 1
              }
            };
          });
          
          // 댓글 새로고침하여 새로운 문의 표시
          await loadComments();
          
          // 📡 서버에서 최신 통계 데이터 재로드 (안전장치)
          setTimeout(() => {
            refreshServiceStats();
          }, 500);
        } else {
          console.error('❌ Inquiry submission failed:', response);
          showError('문의 등록에 실패했습니다');
        }
      } catch (error) {
        console.error('🚨 문의 등록 오류:', error);
        showError('문의 등록 중 오류가 발생했습니다');
      }
    } else {
      showError('제목과 내용을 모두 입력해주세요.');
    }
  };

  return (
    <AppLayout 
      title="서비스 상세" 
      subtitle="업체 정보 및 서비스 안내"
      user={user}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex items-center justify-between mb-6">
          <button 
            onClick={handleBackClick}
            className="flex items-center gap-2 text-var-muted hover:text-var-primary transition-colors"
          >
            ← 목록으로
          </button>
          <div className="flex items-center gap-3">
            {/* 작성자 전용 수정/삭제 버튼 */}
            {isServiceOwner() && (
              <>
                <button 
                  onClick={handleEditService}
                  className="px-4 py-2 border border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  ✏️ 수정
                </button>
                <button 
                  onClick={handleDeleteService}
                  className="px-4 py-2 border border-red-500 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                >
                  🗑️ 삭제
                </button>
              </>
            )}
            <button 
              onClick={() => window.open(`mailto:${service.contact.email}`)}
              className="px-4 py-2 border border-var-color rounded-lg text-var-secondary hover:border-accent-primary hover:text-accent-primary transition-colors"
            >
              문의하기
            </button>
            <button 
              onClick={handleLike}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isLiked 
                  ? 'bg-red-500 text-white' 
                  : 'bg-var-card border border-var-color text-var-secondary hover:bg-red-50 hover:text-red-500'
              }`}
            >
              찜하기 ❤️
            </button>
          </div>
        </div>

        {/* 서비스 헤더 */}
        <div className="bg-green-100 rounded-2xl p-8 mb-8">
          <div className="text-center text-white">
            <h1 className="text-3xl font-bold mb-2 text-green-800">{service.name}</h1>
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="text-green-700">{service.category} •</span>
              <div className="flex items-center gap-1">
                {renderStars(service.rating)}
                <span className="text-green-700">{service.rating}</span>
              </div>
            </div>
            
            {/* 확장 통계 표시 */}
            {service.serviceStats && (
              <div className="flex items-center justify-center gap-6 mb-4">
                <div className="flex items-center gap-1 text-green-700">
                  <span className="text-sm">👁️ 조회</span>
                  <span className="font-medium">{service.serviceStats.views}</span>
                </div>
                <div className="flex items-center gap-1 text-green-700">
                  <span className="text-sm">❤️ 관심</span>
                  <span className="font-medium">{service.serviceStats?.bookmarks || service.bookmarks || 0}</span>
                </div>
                <div className="flex items-center gap-1 text-green-700">
                  <span className="text-sm">💬 문의</span>
                  <span className="font-medium">{service.serviceStats.inquiries}</span>
                </div>
                <div className="flex items-center gap-1 text-green-700">
                  <span className="text-sm">⭐ 후기</span>
                  <span className="font-medium">{service.serviceStats.reviews}</span>
                </div>
              </div>
            )}
            
            <p className="text-green-700 max-w-2xl mx-auto">{service.description}</p>
          </div>
        </div>

        <div className="space-y-8">
          {/* 서비스 가격 및 연락처 통합 섹션 */}
          <div className="bg-var-card rounded-2xl p-6 border border-var-color">
            <h2 className="text-xl font-bold text-var-primary mb-6 flex items-center gap-2">
              🔧 서비스 가격 및 연락처
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* 왼쪽: 서비스 및 가격 */}
              <div>
                <h3 className="text-lg font-semibold text-var-primary mb-4">💰 서비스 가격</h3>
                <div className="space-y-4">
                  {service.services.map((item: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-start p-4 bg-var-section rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium text-var-primary mb-1">{item.name}</h4>
                        <p className="text-var-secondary text-sm">{item.description}</p>
                      </div>
                      <div className="text-right ml-4">
                        {item.specialPrice && (
                          <div className="text-gray-400 line-through text-sm">{item.price.toLocaleString()}원</div>
                        )}
                        <div className="text-red-500 font-bold text-lg">
                          {item.specialPrice ? item.specialPrice.toLocaleString() : item.price.toLocaleString()}원
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">💡 정확한 견적은 현장 상담 후 제공됩니다.</p>
                </div>
              </div>
              
              {/* 오른쪽: 연락처 정보 */}
              <div>
                <h3 className="text-lg font-semibold text-var-primary mb-4">📞 연락처 정보</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-3 bg-var-section rounded-lg">
                    <span className="text-red-500 text-xl">📞</span>
                    <div>
                      <div className="font-medium text-var-primary">{service.contact.phone}</div>
                      <div className="text-var-muted text-sm">전화 문의</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-var-section rounded-lg">
                    <span className="text-orange-500 text-xl">⏰</span>
                    <div>
                      <div className="font-medium text-var-primary">{service.contact.hours}</div>
                      <div className="text-var-muted text-sm">운영 시간</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-var-section rounded-lg">
                    <span className="text-red-500 text-xl">📍</span>
                    <div>
                      <div className="font-medium text-var-primary">{service.contact.address}</div>
                      <div className="text-var-muted text-sm">사업장 위치</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-var-section rounded-lg">
                    <span className="text-blue-500 text-xl">📧</span>
                    <div>
                      <div className="font-medium text-var-primary">{service.contact.email}</div>
                      <div className="text-var-muted text-sm">이메일 문의</div>
                    </div>
                  </div>
                </div>
                
                <button 
                  onClick={handleInquiry}
                  className="w-full mt-4 bg-green-600 text-white py-3 rounded-xl font-medium hover:bg-green-700 transition-colors"
                >
                  📞 전화 상담 신청
                </button>
              </div>
            </div>
          </div>

          {/* 문의 내용과 답변 섹션 */}
          <div className="bg-var-card rounded-2xl p-6 border border-var-color">
            <h2 className="text-xl font-bold text-var-primary mb-6 flex items-center gap-2">
              💬 문의 내용
            </h2>
            
            {/* 실제 문의 내용 */}
            <div className="space-y-4 mb-6">
              {isLoadingComments ? (
                <div className="text-center py-4">
                  <p className="text-var-secondary">문의 내용을 불러오는 중...</p>
                </div>
              ) : comments.length > 0 ? (
                comments
                  .filter(comment => comment.metadata?.subtype === 'service_inquiry')
                  .map((comment, idx) => (
                    <div key={idx} className="border border-var-light rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-var-primary">
                            {comment.author?.display_name || comment.author?.user_handle || '익명'}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            comment.metadata?.isPublic === false 
                              ? 'bg-red-100 text-red-600' 
                              : 'bg-green-100 text-green-600'
                          }`}>
                            {comment.metadata?.isPublic === false ? '비공개' : '공개'}
                          </span>
                        </div>
                        <span className="text-sm text-var-muted">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {/* 수정 모드인 경우 텍스트 영역, 아닌 경우 일반 텍스트 */}
                      {editingComment === comment.id ? (
                        <div className="space-y-3">
                          <textarea
                            value={editContentMap[comment.id] || ''}
                            onChange={(e) => setEditContentMap(prev => ({ ...prev, [comment.id]: e.target.value }))}
                            className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                            rows={4}
                            placeholder="문의 내용을 수정해주세요..."
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEditComment(comment.id)}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                              disabled={!(editContentMap[comment.id] || '').trim()}
                            >
                              저장
                            </button>
                            <button
                              onClick={() => {
                                setEditingComment(null);
                                setEditContentMap(prev => ({ ...prev, [comment.id]: '' }));
                              }}
                              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                              취소
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="text-var-secondary text-sm whitespace-pre-line">
                          {(() => {
                            // 비공개 문의 처리 로직
                            console.log('🔒 Privacy check for comment:', { 
                              commentId: comment.id,
                              isPublic: comment.metadata?.isPublic, 
                              metadata: comment.metadata,
                              author: comment.author,
                              content: comment.content?.substring(0, 50) + '...'
                            });
                            
                            // 비공개 체크 - 여러 방식으로 확인
                            const isPrivate = comment.metadata?.isPublic === false || 
                                            comment.metadata?.isPublic === 'false' ||
                                            comment.metadata?.visibility === 'private';
                            
                            console.log('🔒 Privacy result:', { isPrivate });
                            
                            if (isPrivate) {
                              console.log('🔒 Private comment detected - hiding content regardless of ownership');
                              return "[비공개 문의입니다]";
                            }
                            return comment.content;
                          })()}
                        </div>
                      )}
                      
                      {/* 작성자 수정/삭제 및 답글 버튼 */}
                      <div className="mt-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {user && (
                            <button
                              onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
                              className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                            >
                              {replyingTo === comment.id ? '답글 취소' : '답글'}
                            </button>
                          )}
                        </div>
                        {/* 작성자 수정/삭제 버튼 */}
                        {isCommentOwner(comment) && (
                          <div className="flex items-center gap-3">
                            <button 
                              className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
                              onClick={() => handleEditComment(comment.id)}
                            >
                              {editingComment === comment.id ? '저장' : '수정'}
                            </button>
                            <button 
                              className="text-sm text-gray-600 hover:text-red-600 transition-colors"
                              onClick={() => handleDeleteComment(comment.id)}
                            >
                              삭제
                            </button>
                          </div>
                        )}
                      </div>

                      {/* 답글 작성 폼 */}
                      {replyingTo === comment.id && (
                        <div className="mt-3 pl-4 border-l-2 border-blue-200">
                          <textarea
                            value={replyContentMap[comment.id] || ''}
                            onChange={(e) => setReplyContentMap(prev => ({ ...prev, [comment.id]: e.target.value }))}
                            placeholder="답글을 작성해주세요..."
                            className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                            rows={3}
                          />
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={() => {
                                console.log('🔘 Reply button clicked for comment:', comment.id);
                                handleReplySubmit(comment.id);
                              }}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                              disabled={!(replyContentMap[comment.id] || '').trim()}
                            >
                              답글 작성
                            </button>
                            <button
                              onClick={() => {
                                setReplyingTo(null);
                                setReplyContentMap(prev => ({ ...prev, [comment.id]: '' }));
                              }}
                              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                              취소
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {/* 답글이 있는 경우 표시 (중첩 답글 지원) */}
                      {comment.replies && comment.replies.length > 0 && (
                        <div className="mt-4 space-y-3">
                          {comment.replies.map((reply: any) => renderReply(reply, 0, 3))}
                        </div>
                      )}
                    </div>
                  ))
              ) : (
                <div className="text-center py-8 text-var-muted">
                  <p>아직 문의 내용이 없습니다.</p>
                  <p className="text-sm mt-1">첫 번째 문의를 남겨보세요!</p>
                </div>
              )}
            </div>

            {/* 가운데 정렬된 문의하기 버튼 */}
            <div className="flex justify-center mb-6">
              <button 
                onClick={() => setShowInquiryForm(!showInquiryForm)}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                {showInquiryForm ? '문의 작성 취소' : '💬 문의하기'}
              </button>
            </div>
            
            {/* 문의 작성 폼 */}
            {showInquiryForm && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-medium text-var-primary mb-4">문의 작성</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-var-secondary mb-2">제목 *</label>
                    <input
                      type="text"
                      value={inquiryTitle}
                      onChange={(e) => setInquiryTitle(e.target.value)}
                      placeholder="문의 제목을 입력해주세요"
                      className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-var-secondary mb-2">내용 *</label>
                    <textarea
                      value={inquiryContent}
                      onChange={(e) => setInquiryContent(e.target.value)}
                      placeholder="문의 내용을 상세히 작성해주세요"
                      className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                      rows={4}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-var-secondary mb-2">연락처 (선택)</label>
                    <input
                      type="text"
                      value={inquiryContact}
                      onChange={(e) => setInquiryContact(e.target.value)}
                      placeholder="연락받을 전화번호 또는 이메일"
                      className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary"
                    />
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="inquiryPublic"
                      checked={isInquiryPublic}
                      onChange={(e) => setIsInquiryPublic(e.target.checked)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <label htmlFor="inquiryPublic" className="text-sm text-var-secondary">
                      문의 내용을 공개합니다 (다른 사용자들이 볼 수 있습니다)
                    </label>
                  </div>
                  
                  <button 
                    onClick={handleInquirySubmit}
                    className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                  >
                    문의 등록
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* 후기 섹션 */}
          <div className="bg-var-card rounded-2xl p-6 border border-var-color">
            {(() => {
              const reviewComments = comments.filter(comment => comment.metadata?.subtype === 'service_review');
              return (
                <>
                  <h2 className="text-xl font-bold text-var-primary mb-4">🌟 후기 {reviewComments.length}개</h2>
                  
                  {/* 평점 표시 */}
                  <div className="mb-6 p-4 bg-var-section rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-var-muted">평점:</span>
                      <div className="flex items-center gap-1">
                        {renderStars(service.rating)}
                      </div>
                      <span className="text-var-primary font-medium">({service.rating})</span>
                    </div>
                  </div>

                  {/* 실제 후기 목록 */}
                  <div className="space-y-4 mb-6">
                    {isLoadingComments ? (
                      <div className="text-center py-4">
                        <p className="text-var-secondary">후기를 불러오는 중...</p>
                      </div>
                    ) : reviewComments.length > 0 ? (
                      reviewComments.map((review: any, idx: number) => (
                        <div key={idx} className="border-b border-var-light last:border-b-0 pb-4 last:pb-0">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-var-primary">
                              {review.author?.display_name || review.author?.user_handle || '익명'}
                            </span>
                            <div className="flex items-center gap-1">
                              {renderStars(5)} {/* 기본 5점으로 표시, 나중에 평점 파싱 로직 추가 가능 */}
                            </div>
                            <span className="text-sm text-var-muted">
                              {new Date(review.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {/* 수정 모드인 경우 텍스트 영역, 아닌 경우 일반 텍스트 */}
                          {editingComment === review.id ? (
                            <div className="space-y-3">
                              <textarea
                                value={editContentMap[review.id] || ''}
                                onChange={(e) => setEditContentMap(prev => ({ ...prev, [review.id]: e.target.value }))}
                                className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                                rows={4}
                                placeholder="후기 내용을 수정해주세요..."
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleEditComment(review.id)}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                  disabled={!(editContentMap[review.id] || '').trim()}
                                >
                                  저장
                                </button>
                                <button
                                  onClick={() => {
                                    setEditingComment(null);
                                    setEditContentMap(prev => ({ ...prev, [review.id]: '' }));
                                  }}
                                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                  취소
                                </button>
                              </div>
                            </div>
                          ) : (
                            <p className="text-var-secondary whitespace-pre-line">{review.content}</p>
                          )}
                          
                          {/* 작성자 수정/삭제 및 답글 버튼 */}
                          <div className="mt-3 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {user && (
                                <button
                                  onClick={() => setReplyingTo(replyingTo === review.id ? null : review.id)}
                                  className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                                >
                                  {replyingTo === review.id ? '답글 취소' : '답글'}
                                </button>
                              )}
                            </div>
                            {/* 작성자 수정/삭제 버튼 */}
                            {isCommentOwner(review) && (
                              <div className="flex items-center gap-3">
                                <button 
                                  className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
                                  onClick={() => handleEditComment(review.id)}
                                >
                                  {editingComment === review.id ? '저장' : '수정'}
                                </button>
                                <button 
                                  className="text-sm text-gray-600 hover:text-red-600 transition-colors"
                                  onClick={() => handleDeleteComment(review.id)}
                                >
                                  삭제
                                </button>
                              </div>
                            )}
                          </div>

                          {/* 답글 작성 폼 */}
                          {replyingTo === review.id && (
                            <div className="mt-3 pl-4 border-l-2 border-blue-200">
                              <textarea
                                value={replyContentMap[review.id] || ''}
                                onChange={(e) => setReplyContentMap(prev => ({ ...prev, [review.id]: e.target.value }))}
                                placeholder="답글을 작성해주세요..."
                                className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                                rows={3}
                              />
                              <div className="flex gap-2 mt-2">
                                <button
                                  onClick={() => {
                                    console.log('🔘 Reply button clicked for review:', review.id);
                                    handleReplySubmit(review.id);
                                  }}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                  disabled={!(replyContentMap[review.id] || '').trim()}
                                >
                                  답글 작성
                                </button>
                                <button
                                  onClick={() => {
                                    setReplyingTo(null);
                                    setReplyContentMap(prev => ({ ...prev, [review.id]: '' }));
                                  }}
                                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                  취소
                                </button>
                              </div>
                            </div>
                          )}

                          {/* 답글이 있는 경우 표시 (중첩 답글 지원) */}
                          {review.replies && review.replies.length > 0 && (
                            <div className="mt-4 space-y-3">
                              {review.replies.map((reply: any) => renderReply(reply, 0, 3))}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8 text-var-muted">
                        <p>아직 후기가 없습니다.</p>
                        <p className="text-sm mt-1">첫 번째 후기를 남겨보세요!</p>
                      </div>
                    )}
                  </div>
                </>
              );
            })()}

            {/* 후기 작성 */}
            <div className="border-t border-var-light pt-6">
              <h3 className="font-medium text-var-primary mb-3">후기 작성</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-var-secondary mb-2">별점 평가 *</label>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {renderInteractiveStars(selectedRating, setSelectedRating)}
                    </div>
                    <span className="text-sm text-var-muted ml-2">({selectedRating}점)</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-var-secondary mb-2">후기 내용 *</label>
                  <textarea
                    value={reviewText}
                    onChange={(e) => setReviewText(e.target.value)}
                    placeholder="서비스 이용 후기를 상세히 작성해주세요..."
                    className="w-full p-3 border border-var-color rounded-lg bg-var-background text-var-primary resize-none"
                    rows={4}
                  />
                </div>
                
                <button 
                  onClick={handleReviewSubmit}
                  className="bg-green-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-green-700 transition-colors"
                >
                  후기 등록
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}