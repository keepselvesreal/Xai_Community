/**
 * 환경 선택 컴포넌트
 * 
 * 개발/스테이징/프로덕션 환경을 선택할 수 있는 탭 형태의 컴포넌트
 */
import { useState } from 'react';

export type Environment = 'development' | 'staging' | 'production';

interface EnvironmentSelectorProps {
  selectedEnvironment: Environment;
  onEnvironmentChange: (environment: Environment) => void;
  className?: string;
}

export function EnvironmentSelector({
  selectedEnvironment,
  onEnvironmentChange,
  className = ''
}: EnvironmentSelectorProps) {
  const environments: Array<{
    value: Environment;
    label: string;
    emoji: string;
    description: string;
    color: string;
  }> = [
    {
      value: 'development',
      label: '개발',
      emoji: '🚧',
      description: '개발 환경',
      color: 'yellow'
    },
    {
      value: 'staging',
      label: '스테이징',
      emoji: '🔍',
      description: '검증 환경',
      color: 'blue'
    },
    {
      value: 'production',
      label: '프로덕션',
      emoji: '🚀',
      description: '운영 환경',
      color: 'green'
    }
  ];

  const getTabClasses = (env: Environment) => {
    const baseClasses = 'flex items-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 cursor-pointer';
    
    if (selectedEnvironment === env) {
      switch (env) {
        case 'development':
          return `${baseClasses} bg-yellow-100 text-yellow-900 border-2 border-yellow-300 shadow-sm`;
        case 'staging':
          return `${baseClasses} bg-blue-100 text-blue-900 border-2 border-blue-300 shadow-sm`;
        case 'production':
          return `${baseClasses} bg-green-100 text-green-900 border-2 border-green-300 shadow-sm`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-900 border-2 border-gray-300 shadow-sm`;
      }
    } else {
      return `${baseClasses} bg-white text-gray-600 border-2 border-gray-200 hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300`;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">환경 선택</h3>
        <div className="text-sm text-gray-500">
          현재: {environments.find(env => env.value === selectedEnvironment)?.label}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {environments.map((env) => (
          <button
            key={env.value}
            onClick={() => onEnvironmentChange(env.value)}
            className={getTabClasses(env.value)}
            title={env.description}
          >
            <span className="text-lg">{env.emoji}</span>
            <div className="text-left">
              <div className="font-semibold">{env.label}</div>
              <div className="text-xs opacity-70">{env.description}</div>
            </div>
          </button>
        ))}
      </div>
      
      {/* 환경별 설명 */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-sm text-gray-600">
          <div className="font-medium mb-2">환경별 특징:</div>
          <ul className="space-y-1 text-xs">
            <li>• <span className="font-medium">개발:</span> 개발자 테스트 환경 (로컬 서버, 개발 데이터베이스)</li>
            <li>• <span className="font-medium">스테이징:</span> 배포 전 검증 환경 (클라우드 인프라, 테스트 데이터)</li>
            <li>• <span className="font-medium">프로덕션:</span> 실제 서비스 환경 (클라우드 인프라, 실제 사용자 데이터)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default EnvironmentSelector;