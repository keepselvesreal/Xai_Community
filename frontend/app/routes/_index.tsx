import { redirect, type LoaderFunction } from "@remix-run/node";

export const loader: LoaderFunction = async () => {
  // 홈페이지 방문 시 대시보드로 리다이렉트
  return redirect("/dashboard");
};

export default function Index() {
  return null;
}