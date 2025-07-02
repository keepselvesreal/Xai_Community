import { type MetaFunction } from "@remix-run/node";
import { ListPage } from "~/components/common/ListPage";
import { tipsConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "전문가 꿀정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가들이 제공하는 검증된 생활 꿀팁" },
  ];
};

export default function Tips() {
  const { user, logout } = useAuth();
  
  // 환경 변수나 기능 플래그로 전환 제어
  const USE_NEW_SYSTEM = process.env.NODE_ENV === 'development' || true;
  
  if (USE_NEW_SYSTEM) {
    return (
      <ListPage
        config={tipsConfig}
        user={user}
        onLogout={logout}
      />
    );
  }
  
  // 기존 구현은 tips.tsx.backup에서 참고 가능
  return null;
}