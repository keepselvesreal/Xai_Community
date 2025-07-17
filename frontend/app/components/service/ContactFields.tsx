/**
 * 업체 등록 페이지용 연락처 및 문의 가능시간 입력 필드 컴포넌트
 */

import React from 'react';

interface ContactFieldsProps {
  contact: string;
  availableHours: string;
  onContactChange: (contact: string) => void;
  onAvailableHoursChange: (hours: string) => void;
}

export default function ContactFields({
  contact,
  availableHours,
  onContactChange,
  onAvailableHoursChange
}: ContactFieldsProps) {
  const handleContactChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onContactChange(e.target.value);
  };

  const handleAvailableHoursChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onAvailableHoursChange(e.target.value);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          연락처 <span className="text-red-500">*</span>
        </label>
        <input
          type="tel"
          value={contact}
          onChange={handleContactChange}
          placeholder="연락처를 입력하세요"
          className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          문의 가능시간 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={availableHours}
          onChange={handleAvailableHoursChange}
          placeholder="예: 09:00~18:00"
          className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );
}