import { useState } from 'react';
import { useNavigate } from '@remix-run/react';
import { AppLayout } from '~/components/layout/AppLayout';
import { Card } from '~/components/ui/Card';
import { Button } from '~/components/ui/Button';
import { Input } from '~/components/ui/Input';
import { Textarea } from '~/components/ui/Textarea';
import { Select } from '~/components/ui/Select';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { useForm } from '~/hooks/useForm';
import { apiClient } from '~/lib/api';
import { SERVICE_OPTIONS, POST_TYPE_OPTIONS } from '~/lib/constants';
import type { CreatePostRequest, ServiceType, PostType } from '~/types';

interface PostFormData {
  title: string;
  content: string;
  service: ServiceType;
  type: PostType;
  tags: string;
}

export default function CreatePost() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 인증되지 않은 사용자 리다이렉션
  if (!user) {
    navigate('/auth/login');
    return null;
  }

  const { values, errors, getFieldProps, handleSubmit, isValid } = useForm<PostFormData>({
    initialValues: {
      title: '',
      content: '',
      service: 'community',
      type: '자유게시판',
      tags: '',
    },
    validate: (values) => {
      const errors: Partial<Record<keyof PostFormData, string>> = {};
      
      if (!values.title.trim()) {
        errors.title = '제목을 입력해주세요';
      } else if (values.title.length < 2) {
        errors.title = '제목은 최소 2자 이상 입력해주세요';
      } else if (values.title.length > 200) {
        errors.title = '제목은 200자를 초과할 수 없습니다';
      }

      if (!values.content.trim()) {
        errors.content = '내용을 입력해주세요';
      } else if (values.content.length < 10) {
        errors.content = '내용은 최소 10자 이상 입력해주세요';
      } else if (values.content.length > 10000) {
        errors.content = '내용은 10,000자를 초과할 수 없습니다';
      }

      if (!values.service) {
        errors.service = '서비스를 선택해주세요';
      }

      if (!values.type) {
        errors.type = '게시글 타입을 선택해주세요';
      }

      return errors;
    },
    onSubmit: async (values) => {
      setIsSubmitting(true);
      
      try {
        // 태그 처리 (쉼표로 구분된 문자열을 배열로 변환)
        const tags = values.tags
          .split(',')
          .map(tag => tag.trim())
          .filter(tag => tag.length > 0);

        const postData: CreatePostRequest = {
          title: values.title.trim(),
          content: values.content.trim(),
          service: values.service,
          type: values.type,
          tags: tags.length > 0 ? tags : undefined,
        };

        const response = await apiClient.createPost(postData);
        
        if (response.success && response.data) {
          showSuccess('게시글이 성공적으로 작성되었습니다');
          navigate(`/posts/${response.data.slug}`);
        } else {
          showError(response.error || '게시글 작성에 실패했습니다');
        }
      } catch (error) {
        showError('게시글 작성 중 오류가 발생했습니다');
        console.error('게시글 작성 오류:', error);
      } finally {
        setIsSubmitting(false);
      }
    },
  });

  const handleCancel = () => {
    if (values.title.trim() || values.content.trim()) {
      if (window.confirm('작성 중인 내용이 있습니다. 정말로 취소하시겠습니까?')) {
        navigate('/posts');
      }
    } else {
      navigate('/posts');
    }
  };

  return (
    <AppLayout title="새 게시글 작성" user={user}>
      <div className="max-w-4xl mx-auto">
        <Card>
          <Card.Header>
            <Card.Title level={1}>새 게시글 작성</Card.Title>
            <p className="text-gray-600 mt-2">
              커뮤니티에 새로운 게시글을 작성해보세요. 
              다른 사용자들과 정보를 공유하고 소통할 수 있습니다.
            </p>
          </Card.Header>
          
          <Card.Content>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* 제목 */}
              <div>
                <Input
                  {...getFieldProps('title')}
                  label="제목"
                  placeholder="게시글 제목을 입력하세요"
                  required
                  error={errors.title}
                />
                <div className="mt-1 text-sm text-gray-500">
                  {values.title.length}/200자
                </div>
              </div>

              {/* 서비스 및 타입 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  {...getFieldProps('service')}
                  label="서비스"
                  options={SERVICE_OPTIONS}
                  required
                  error={errors.service}
                />
                
                <Select
                  {...getFieldProps('type')}
                  label="게시글 타입"
                  options={POST_TYPE_OPTIONS}
                  required
                  error={errors.type}
                />
              </div>

              {/* 내용 */}
              <div>
                <Textarea
                  {...getFieldProps('content')}
                  label="내용"
                  placeholder="게시글 내용을 입력하세요..."
                  rows={12}
                  required
                  error={errors.content}
                />
                <div className="mt-1 text-sm text-gray-500">
                  {values.content.length}/10,000자
                </div>
              </div>

              {/* 태그 */}
              <div>
                <Input
                  {...getFieldProps('tags')}
                  label="태그 (선택사항)"
                  placeholder="태그1, 태그2, 태그3"
                  error={errors.tags}
                />
                <div className="mt-1 text-sm text-gray-500">
                  쉼표(,)로 구분하여 여러 태그를 입력할 수 있습니다
                </div>
              </div>

              {/* 미리보기 */}
              {values.tags && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    태그 미리보기
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {values.tags
                      .split(',')
                      .map(tag => tag.trim())
                      .filter(tag => tag.length > 0)
                      .map((tag, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          #{tag}
                        </span>
                      ))}
                  </div>
                </div>
              )}

              {/* 작성 가이드라인 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📝 게시글 작성 가이드라인</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• 제목은 내용을 명확히 나타내도록 작성해주세요</li>
                  <li>• 다른 사용자를 배려하는 건전한 내용으로 작성해주세요</li>
                  <li>• 개인정보나 민감한 정보는 포함하지 마세요</li>
                  <li>• 태그를 활용해 다른 사용자들이 쉽게 찾을 수 있도록 해주세요</li>
                </ul>
              </div>

              {/* 버튼 */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isSubmitting}
                >
                  취소
                </Button>
                <Button
                  type="submit"
                  disabled={!isValid || isSubmitting}
                  loading={isSubmitting}
                >
                  {isSubmitting ? '게시글 작성 중...' : '게시글 작성'}
                </Button>
              </div>
            </form>
          </Card.Content>
        </Card>
      </div>
    </AppLayout>
  );
}