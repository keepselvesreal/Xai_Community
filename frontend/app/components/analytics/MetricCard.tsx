import React from 'react';
import type { MetricCard as MetricCardType } from '~/types/analytics';

interface MetricCardProps extends MetricCardType {
  className?: string;
}

export function MetricCard({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  color = 'blue',
  format = 'number',
  className = ''
}: MetricCardProps) {
  // 값 포맷팅
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'percentage':
        return `${val.toFixed(1)}%`;
      case 'currency':
        return `₩${val.toLocaleString()}`;
      case 'duration':
        const minutes = Math.floor(val / 60);
        const seconds = val % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
      case 'number':
      default:
        return val.toLocaleString();
    }
  };

  // 변화율 표시
  const renderChange = () => {
    if (change === undefined) return null;

    const changeIcon = changeType === 'increase' ? '↗' : changeType === 'decrease' ? '↘' : '→';
    const changeColor = changeType === 'increase' ? 'text-green-600' : changeType === 'decrease' ? 'text-red-600' : 'text-gray-600';

    return (
      <div className={`flex items-center text-sm ${changeColor}`}>
        <span className="mr-1">{changeIcon}</span>
        <span>{Math.abs(change).toFixed(1)}%</span>
      </div>
    );
  };

  // 색상 테마 설정
  const colorClasses = {
    blue: {
      background: 'bg-blue-50',
      border: 'border-blue-200',
      icon: 'text-blue-600',
      title: 'text-blue-800'
    },
    green: {
      background: 'bg-green-50',
      border: 'border-green-200',
      icon: 'text-green-600',
      title: 'text-green-800'
    },
    red: {
      background: 'bg-red-50',
      border: 'border-red-200',
      icon: 'text-red-600',
      title: 'text-red-800'
    },
    yellow: {
      background: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: 'text-yellow-600',
      title: 'text-yellow-800'
    },
    purple: {
      background: 'bg-purple-50',
      border: 'border-purple-200',
      icon: 'text-purple-600',
      title: 'text-purple-800'
    }
  };

  const theme = colorClasses[color];

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{formatValue(value)}</p>
          {renderChange()}
        </div>
        {icon && (
          <div className={`text-3xl ml-4 ${theme.icon}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export default MetricCard;