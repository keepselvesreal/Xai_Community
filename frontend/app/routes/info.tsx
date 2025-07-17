import type { MetaFunction } from "@remix-run/node";
import { ListPage } from "~/components/common/ListPage";
import { infoConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";
export const meta: MetaFunction = () => {
  return [
    { title: "정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들을 위한 유용한 정보" },
  ];
};

export default function Info() {
  const { user, logout } = useAuth();

  return (
    <ListPage
      config={infoConfig}
      user={user}
      onLogout={logout}
    />
  );
}