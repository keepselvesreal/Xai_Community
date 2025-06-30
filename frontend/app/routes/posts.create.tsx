import { useEffect } from 'react';
import { useNavigate } from '@remix-run/react';

export default function CreatePost() {
  const navigate = useNavigate();

  // 이 페이지는 더 이상 사용하지 않음. board/write로 리다이렉션
  useEffect(() => {
    navigate('/board/write', { replace: true });
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">페이지를 이동 중입니다...</p>
      </div>
    </div>
  );
}