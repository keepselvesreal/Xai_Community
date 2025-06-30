import { useState } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "전문가 꿀정보 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가 꿀정보 상세 내용" },
  ];
};

export const loader: LoaderFunction = async ({ params }) => {
  const { id } = params;
  
  // Mock 전문가 글 데이터
  const expertPosts = {
    1: {
      id: 1,
      category: "클린 라이프",
      title: "겨울철 실내 화분 관리법",
      author: "원예 전문가 김○○",
      date: "2024-01-15",
      viewCount: 245,
      likeCount: 32,
      bookmarkCount: 18,
      description: "겨울철에는 실내 온도와 습도 변화로 인해 화분 관리가 까다로워집니다. 올바른 관리법을 통해 건강한 식물을 키워보세요.",
      content: [
        {
          type: "text",
          content: "겨울철에는 실내 온도와 습도 변화로 인해 화분 관리가 까다로워집니다. 올바른 관리법을 통해 건강한 식물을 키워보세요."
        },
        {
          type: "section",
          title: "1. 온도 관리",
          items: [
            "실내 온도를 18-22°C로 유지해주세요",
            "갑작스러운 온도 변화를 피해주세요",
            "난방기 바로 옆에 두지 마세요"
          ]
        },
        {
          type: "section", 
          title: "2. 습도 관리",
          items: [
            "겨울철 실내 습도를 40-60%로 유지해주세요",
            "가습기를 사용하거나 물을 담은 그릇을 근처에 두세요",
            "분무기로 잎에 물을 뿌려주세요 (주 2-3회)"
          ]
        },
        {
          type: "section",
          title: "3. 물주기",
          items: [
            "겨울철에는 물 주는 횟수를 줄여주세요",
            "흙 표면이 마르면 물을 주세요",
            "뿌리가 썩지 않도록 배수에 주의하세요"
          ]
        },
        {
          type: "section",
          title: "4. 빛 관리",
          items: [
            "창가 근처에 배치하여 충분한 햇빛을 받도록 해주세요",
            "하루 4-6시간 이상 밝은 빛을 받을 수 있도록 해주세요",
            "필요시 LED 식물등을 사용하세요"
          ]
        },
        {
          type: "tip",
          title: "💡 전문가 팁",
          content: "화분의 잎이 노랗게 변하거나 떨어진다면 과습이나 온도 스트레스를 의심해보세요. 환경을 점검하고 조절해주세요."
        }
      ],
      tags: ["화분관리", "겨울철", "실내식물", "원예"],
      relatedPosts: [
        { id: 2, title: "봄철 화분 분갈이 가이드", author: "원예 전문가 이○○" },
        { id: 3, title: "실내 공기정화 식물 추천", author: "원예 전문가 박○○" }
      ]
    }
  };

  const post = expertPosts[Number(id) as keyof typeof expertPosts];
  
  if (!post) {
    throw new Response("Not Found", { status: 404 });
  }

  return json({ post });
};

export default function ExpertDetail() {
  const { post } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likeCount, setLikeCount] = useState(post.likeCount);
  const [bookmarkCount, setBookmarkCount] = useState(post.bookmarkCount);

  const handleLike = () => {
    setIsLiked(!isLiked);
    setLikeCount(prev => isLiked ? prev - 1 : prev + 1);
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    setBookmarkCount(prev => isBookmarked ? prev - 1 : prev + 1);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: post.title,
        text: post.description,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('링크가 복사되었습니다.');
    }
  };

  const renderContent = (contentItem: any) => {
    switch (contentItem.type) {
      case 'text':
        return (
          <p className="text-var-secondary leading-relaxed mb-6">
            {contentItem.content}
          </p>
        );
      
      case 'section':
        return (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-var-primary mb-4 flex items-center gap-2">
              <span className="text-green-600">🌿</span>
              {contentItem.title}
            </h3>
            <ul className="space-y-3">
              {contentItem.items.map((item: string, index: number) => (
                <li key={index} className="flex items-start gap-3 text-var-secondary">
                  <span className="text-green-500 mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        );
      
      case 'tip':
        return (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg mb-6">
            <h4 className="font-semibold text-blue-800 mb-2">{contentItem.title}</h4>
            <p className="text-blue-700">{contentItem.content}</p>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <AppLayout 
      title={post.title}
      subtitle="전문가 꿀정보"
      user={user}
      onLogout={logout}
    >
      {/* 뒤로가기 버튼 */}
      <div className="mb-6">
        <Link 
          to="/tips"
          className="inline-flex items-center gap-2 text-var-secondary hover:text-var-primary transition-colors"
        >
          <span>←</span>
          <span>목록으로</span>
        </Link>
      </div>

      {/* 글 헤더 */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-8 mb-8 text-white">
        <div className="mb-4">
          <span className="bg-white/20 text-white px-3 py-1 rounded-full text-sm font-medium">
            {post.category}
          </span>
        </div>
        <h1 className="text-3xl font-bold mb-4">{post.title}</h1>
        <div className="flex items-center justify-between">
          <div className="text-white/90">
            <p className="font-medium">{post.author}</p>
            <p className="text-sm opacity-75">{post.date}</p>
          </div>
          <div className="flex items-center gap-6 text-white/90">
            <button
              onClick={handleLike}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className={`text-lg ${isLiked ? '❤️' : '🤍'}`}>
                {isLiked ? '❤️' : '🤍'}
              </span>
              <span className="text-sm">추천</span>
            </button>
            <button
              onClick={handleBookmark}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className={`text-lg ${isBookmarked ? '🔖' : '📝'}`}>
                {isBookmarked ? '🔖' : '📝'}
              </span>
              <span className="text-sm">저장</span>
            </button>
            <button
              onClick={handleShare}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className="text-lg">📤</span>
              <span className="text-sm">공유</span>
            </button>
          </div>
        </div>
      </div>

      {/* 글 제목 */}
      <div className="bg-var-card border border-var-color rounded-2xl p-8 mb-8">
        <h2 className="text-2xl font-bold text-var-primary mb-6">{post.title}</h2>
        
        {/* 통계 정보 */}
        <div className="flex items-center justify-center gap-12 mb-8 py-6 border-y border-var-light">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{post.viewCount}</div>
            <div className="text-sm text-var-muted">조회수</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{likeCount}</div>
            <div className="text-sm text-var-muted">추천</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{bookmarkCount}</div>
            <div className="text-sm text-var-muted">저장</div>
          </div>
        </div>

        {/* 글 내용 */}
        <div className="prose max-w-none">
          {post.content.map((contentItem: any, index: number) => (
            <div key={index}>
              {renderContent(contentItem)}
            </div>
          ))}
        </div>

        {/* 태그 */}
        <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t border-var-light">
          {post.tags.map((tag: string, index: number) => (
            <span 
              key={index}
              className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm"
            >
              #{tag}
            </span>
          ))}
        </div>
      </div>

      {/* 관련 글 */}
      <div className="bg-var-card border border-var-color rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-var-primary mb-4 flex items-center gap-2">
          <span>📚</span>
          관련 글 추천
        </h3>
        <div className="space-y-3">
          {post.relatedPosts.map((relatedPost: any) => (
            <Link
              key={relatedPost.id}
              to={`/expert/${relatedPost.id}`}
              className="block p-4 bg-var-section rounded-lg hover:bg-var-light transition-colors"
            >
              <h4 className="font-medium text-var-primary mb-1">{relatedPost.title}</h4>
              <p className="text-sm text-var-muted">{relatedPost.author}</p>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}