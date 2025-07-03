/**
 * 카테고리 관련 유틸리티 함수들
 */

import type { CategoryType } from "~/types";

export const categories = [
  { value: "info", label: "입주정보" },
  { value: "life", label: "생활정보" },
  { value: "story", label: "이야기" }
] as const;

/**
 * 카테고리 label을 value로 변환하는 함수
 */
export const getCategoryValue = (label: string): string => {
  const category = categories.find(cat => cat.label === label);
  return category?.value || "info";
};

/**
 * 카테고리 value를 label로 변환하는 함수
 */
export const getCategoryLabel = (value: string): CategoryType => {
  const category = categories.find(cat => cat.value === value);
  return (category?.label as CategoryType) || "입주정보";
};