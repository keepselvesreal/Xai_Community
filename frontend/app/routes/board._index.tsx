import { type MetaFunction } from "@remix-run/node";
import { UnifiedListPage } from "~/components/common/UnifiedListPage";
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
  
  return (
    <UnifiedListPage
      config={boardConfig}
      user={user}
      onLogout={logout}
    />
  );
}