import { useState } from 'react';
import Card from '~/components/ui/Card';
import Button from '~/components/ui/Button';
import Textarea from '~/components/ui/Textarea';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { getAnalytics } from '~/hooks/useAnalytics';
import { formatRelativeTime } from '~/lib/utils';

interface ServiceReview {
  id: string;
  author: {
    display_name: string;
    user_handle: string;
  };
  content: string;
  rating: number;
  created_at: string;
}

interface ServiceReviewSectionProps {
  serviceId: string;
  reviews: ServiceReview[];
  onReviewAdded: () => void;
  className?: string;
}

export default function ServiceReviewSection({ 
  serviceId, 
  reviews, 
  onReviewAdded, 
  className = "" 
}: ServiceReviewSectionProps) {
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [newReview, setNewReview] = useState('');
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitReview = async () => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!newReview.trim()) {
      showError('후기를 입력해주세요');
      return;
    }

    if (rating === 0) {
      showError('별점을 선택해주세요');
      return;
    }

    setIsSubmitting(true);

    try {
      // 실제 API 호출 로직은 나중에 구현
      // 현재는 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setNewReview('');
      setRating(0);
      setHoverRating(0);
      onReviewAdded();
      showSuccess('후기가 등록되었습니다');

      // GA4 이벤트 추적
      if (typeof window !== 'undefined') {
        const analytics = getAnalytics();
        analytics.trackServiceReview(serviceId, `review_${Date.now()}`, rating);
      }
    } catch (error) {
      showError('후기 등록 중 오류가 발생했습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = (currentRating: number, isInteractive: boolean = false) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      const isFilled = i <= currentRating;
      const isHovered = isInteractive && i <= hoverRating;
      
      stars.push(
        <button
          key={i}
          type="button"
          className={`text-2xl transition-colors duration-200 ${
            isInteractive 
              ? 'hover:text-yellow-400 cursor-pointer' 
              : 'cursor-default'
          } ${
            isFilled || isHovered ? 'text-yellow-400' : 'text-gray-300'
          }`}
          onClick={() => isInteractive && setRating(i)}
          onMouseEnter={() => isInteractive && setHoverRating(i)}
          onMouseLeave={() => isInteractive && setHoverRating(0)}
          disabled={!isInteractive}
        >
          ★
        </button>
      );
    }
    return stars;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <h3 className="text-xl font-semibold text-gray-800">
        후기 ({reviews.length})
      </h3>

      {/* 후기 작성 폼 */}
      {user && (
        <Card>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  별점 평가
                </label>
                <div className="flex items-center gap-1">
                  {renderStars(rating, true)}
                  <span className="ml-2 text-sm text-gray-600">
                    {rating > 0 ? `${rating}점` : '별점을 선택하세요'}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  후기 작성
                </label>
                <Textarea
                  value={newReview}
                  onChange={(e) => setNewReview(e.target.value)}
                  placeholder="서비스 이용 후기를 남겨주세요..."
                  rows={4}
                  className="w-full"
                />
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleSubmitReview}
                  loading={isSubmitting}
                  disabled={!newReview.trim() || rating === 0}
                >
                  후기 등록
                </Button>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* 후기 목록 */}
      <div className="space-y-4">
        {reviews.length === 0 ? (
          <Card>
            <Card.Content className="text-center py-8 text-gray-500">
              아직 후기가 없습니다. 첫 번째 후기를 남겨보세요!
            </Card.Content>
          </Card>
        ) : (
          reviews.map((review) => (
            <Card key={review.id}>
              <Card.Content>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {review.author.display_name?.[0] || review.author.user_handle[0]}
                    </div>
                    <div>
                      <div className="font-medium text-gray-800">
                        {review.author.display_name || review.author.user_handle}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex">
                          {renderStars(review.rating)}
                        </div>
                        <span className="text-sm text-gray-500">
                          {formatRelativeTime(review.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-gray-700 whitespace-pre-wrap">
                  {review.content}
                </div>
              </Card.Content>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}