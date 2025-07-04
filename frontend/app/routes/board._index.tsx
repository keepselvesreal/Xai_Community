import { type MetaFunction } from "@remix-run/node";
import { ListPage } from "~/components/common/ListPage";
import { boardConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "게시판 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들의 소통 공간" },
  ];
};

export default function Board() {
  const { user, logout } = useAuth();
  
  // 환경 변수나 기능 플래그로 전환 제어
  const USE_NEW_SYSTEM = process.env.NODE_ENV === 'development' || true;
  
  if (USE_NEW_SYSTEM) {
    return (
      <ListPage
        config={boardConfig}
        user={user}
        onLogout={logout}
      />
    );
  }
  
  // 기존 구현은 board.tsx.backup에서 참고 가능
  return null;
}