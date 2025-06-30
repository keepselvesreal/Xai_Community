import { useState } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import type { MockTip } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "전문가 꿀정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가들이 제공하는 검증된 생활 꿀팁" },
  ];
};

export const loader: LoaderFunction = async () => {
  // Mock 전문가 꿀정보 데이터
  const tips = [
    {
      id: 1,
      title: "겨울철 실내 화분 관리법",
      content: "실내 온도와 습도 조절을 통한 효과적인 식물 관리 방법을 알려드립니다. 겨울철 특히 주의해야 할 포인트들을 정리했습니다.",
      expert_name: "김○○",
      expert_title: "클린 라이프 🌱 원예 전문가",
      created_at: "2일 전",
      category: "원예",
      tags: ["#실내화분", "#겨울관리", "#습도조절"],
      views_count: 245,
      likes_count: 32,
      saves_count: 18,
      is_new: true
    },
    {
      id: 2,
      title: "아파트 곰팡이 예방법",
      content: "습도가 높은 계절에 발생하기 쉬운 곰팡이를 예방하는 실용적인 방법들을 소개합니다. 천연 재료로도 가능한 방법들이 있어요.",
      expert_name: "박○○",
      expert_title: "하우스키퍼 🧹 청소 전문가",
      created_at: "3일 전",
      category: "청소/정리",
      tags: ["#곰팡이예방", "#천연재료", "#습도관리"],
      views_count: 189,
      likes_count: 28,
      saves_count: 15,
      is_new: false
    },
    {
      id: 3,
      title: "전기요금 절약하는 10가지 방법",
      content: "아파트 생활에서 실제로 효과가 있는 전기요금 절약 노하우를 공유합니다. 월 10만원 이상 절약도 가능해요!",
      expert_name: "이○○",
      expert_title: "스마트홈 💡 생활 전문가",
      created_at: "1주일 전",
      category: "절약",
      tags: ["#전기요금절약", "#생활비절약", "#에너지효율"],
      views_count: 456,
      likes_count: 67,
      saves_count: 34,
      is_new: false
    },
    {
      id: 4,
      title: "좁은 공간 넓어 보이게 하는 인테리어",
      content: "작은 평수도 넓고 쾌적하게 꾸밀 수 있는 인테리어 팁들을 소개합니다. 색상과 조명 활용법이 핵심입니다.",
      expert_name: "최○○",
      expert_title: "모던스페이스 🎨 인테리어 전문가",
      created_at: "1주일 전",
      category: "인테리어",
      tags: ["#공간활용", "#색상조합", "#조명인테리어"],
      views_count: 312,
      likes_count: 45,
      saves_count: 22,
      is_new: false
    },
    {
      id: 5,
      title: "에어컨 필터 청소 완벽 가이드",
      content: "에어컨 필터를 제대로 청소하는 방법과 주기, 필요한 도구들을 상세히 설명해드립니다. 전기요금 절약 효과도 얻을 수 있어요.",
      expert_name: "정○○",
      expert_title: "퍼펙트클린 🧼 청소 전문가",
      created_at: "2주일 전",
      category: "청소/정리",
      tags: ["#에어컨청소", "#필터청소", "#전기요금절약"],
      views_count: 378,
      likes_count: 52,
      saves_count: 29,
      is_new: false
    },
    {
      id: 6,
      title: "베란다 텃밭 만들기 A to Z",
      content: "아파트 베란다에서도 충분히 키울 수 있는 채소들과 관리 방법을 소개합니다. 초보자도 쉽게 따라할 수 있는 실용적인 팁들이에요.",
      expert_name: "한○○",
      expert_title: "그린가든 🍀 원예 전문가",
      created_at: "3주일 전",
      category: "원예",
      tags: ["#베란다텃밭", "#채소재배", "#초보자가이드"],
      views_count: 267,
      likes_count: 39,
      saves_count: 21,
      is_new: false
    }
  ];

  return json({ tips });
};

const categories = ["전체", "청소/정리", "인테리어", "생활", "절약", "원예"];

export default function Tips() {
  const { tips: initialTips } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  
  const [tips, setTips] = useState(initialTips);
  const [selectedCategory, setSelectedCategory] = useState("전체");
  const [searchQuery, setSearchQuery] = useState("");

  const handleCategoryFilter = (category: string) => {
    setSelectedCategory(category);
    applyFilters(category);
  };


  const applyFilters = (category: string) => {
    let filteredTips = initialTips;
    
    if (category !== "전체") {
      filteredTips = filteredTips.filter((tip: MockTip) => tip.category === category);
    }
    
    setTips(filteredTips);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const filteredTips = initialTips.filter((tip: MockTip) =>
        tip.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tip.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setTips(filteredTips);
    } else {
      setTips(initialTips);
    }
  };


  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 검색 및 필터 섹션 */}
      <div className="mb-8">
        {/* 검색 */}
        <div className="flex justify-center items-center gap-4 mb-6">
          <div className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
            <span className="text-var-muted">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch(e as any)}
              placeholder="전문가 꿀정보를 검색하세요..."
              className="flex-1 bg-transparent border-none outline-none text-var-primary placeholder-var-muted"
            />
          </div>
        </div>

        {/* 필터바 */}
        <div className="flex gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => handleCategoryFilter(category)}
              className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 ${
                selectedCategory === category
                  ? 'border-accent-primary bg-accent-primary text-white'
                  : 'border-var-color bg-var-card text-var-secondary hover:border-accent-primary hover:text-accent-primary'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

      </div>

      {/* 전문가 꿀정보 목록 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {tips.length > 0 ? (
          tips.map((tip: MockTip) => (
            <Link key={tip.id} to={`/expert/${tip.id}`}>
              <div className="card p-6 hover:shadow-var-card transition-all duration-200 cursor-pointer h-full">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-var-primary font-bold text-lg mb-2 line-clamp-2 flex-1">
                      {tip.title}
                      {tip.is_new && (
                        <span className="inline-block ml-2 px-2 py-1 bg-blue-500 text-white text-xs rounded-full font-medium">
                          NEW
                        </span>
                      )}
                    </h3>
                  </div>
                  
                  <p className="text-var-secondary text-sm mb-4 line-clamp-2">
                    {tip.content}
                  </p>

                  {/* 태그 */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {tip.tags.map((tag: string, index: number) => (
                      <span key={index} className="px-3 py-1 bg-green-50 text-green-700 text-xs rounded-full font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* 통계 및 날짜 */}
                  <div className="flex items-center justify-between text-var-muted text-sm">
                    <span className="text-var-secondary font-medium">{tip.created_at}</span>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        👁️ {tip.views_count}
                      </span>
                      <span className="flex items-center gap-1">
                        👍 {tip.likes_count}
                      </span>
                      <span className="flex items-center gap-1">
                        📌 {tip.saves_count}
                      </span>
                    </div>
                  </div>
              </div>
            </Link>
          ))
        ) : (
          <div className="col-span-full card p-12 text-center">
            <div className="text-6xl mb-4">💡</div>
            <h3 className="text-var-primary font-semibold text-lg mb-2">
              전문가 꿀정보가 없습니다
            </h3>
            <p className="text-var-secondary mb-6">
              {searchQuery ? '검색 결과가 없습니다. 다른 키워드로 검색해보세요.' : '첫 번째 전문가 꿀정보를 기다리고 있습니다!'}
            </p>
          </div>
        )}
      </div>

    </AppLayout>
  );
}