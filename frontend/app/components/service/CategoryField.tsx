/**
 * 업체 등록 페이지용 카테고리 선택 필드 컴포넌트
 */

import React from 'react';

interface CategoryFieldProps {
  value: string;
  onChange: (category: string) => void;
}

const categories = [
  { value: "moving", label: "이사" },
  { value: "cleaning", label: "청소" },
  { value: "aircon", label: "에어컨" }
];

export default function CategoryField({ value, onChange }: CategoryFieldProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange(e.target.value);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-3">
        카테고리 <span className="text-red-500">*</span>
      </label>
      <select
        value={value}
        onChange={handleChange}
        className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        {categories.map((category) => (
          <option key={category.value} value={category.value}>
            {category.label}
          </option>
        ))}
      </select>
    </div>
  );
}