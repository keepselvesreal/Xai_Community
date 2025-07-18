import React from 'react';
import type { ChartData } from '~/types/analytics';

interface TrendChartProps {
  title: string;
  data: ChartData;
  type?: 'line' | 'bar' | 'pie' | 'doughnut';
  height?: number;
  className?: string;
}

export function TrendChart({
  title,
  data,
  type = 'line',
  height = 300,
  className = ''
}: TrendChartProps) {
  // Chart.js가 설치되지 않은 경우를 위한 간단한 시각화
  // 실제 환경에서는 Chart.js나 Recharts를 사용
  
  const renderSimpleLineChart = () => {
    if (!data.datasets.length || !data.datasets[0].data.length) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          데이터가 없습니다
        </div>
      );
    }

    const dataset = data.datasets[0];
    const maxValue = Math.max(...dataset.data);
    const minValue = Math.min(...dataset.data);
    const range = maxValue - minValue || 1;

    return (
      <div className="relative h-full p-4">
        {/* Y축 레이블 */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 pr-2">
          <span>{maxValue.toLocaleString()}</span>
          <span>{Math.round((maxValue + minValue) / 2).toLocaleString()}</span>
          <span>{minValue.toLocaleString()}</span>
        </div>

        {/* 차트 영역 */}
        <div className="ml-8 h-full flex items-end space-x-1">
          {dataset.data.map((value, index) => {
            const height = ((value - minValue) / range) * 100;
            return (
              <div key={index} className="flex-1 flex flex-col items-center">
                {/* 바 또는 포인트 */}
                <div 
                  className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                  style={{ height: `${Math.max(height, 2)}%` }}
                  title={`${data.labels[index]}: ${value.toLocaleString()}`}
                />
                {/* X축 레이블 */}
                <span className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-top-left">
                  {data.labels[index]}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderSimplePieChart = () => {
    if (!data.datasets.length || !data.datasets[0].data.length) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          데이터가 없습니다
        </div>
      );
    }

    const dataset = data.datasets[0];
    const total = dataset.data.reduce((sum, value) => sum + value, 0);
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

    return (
      <div className="flex items-center justify-center h-full">
        <div className="relative">
          {/* 원형 차트 (CSS로 구현) */}
          <div className="w-48 h-48 rounded-full relative overflow-hidden">
            {dataset.data.map((value, index) => {
              const percentage = (value / total) * 100;
              const rotation = dataset.data.slice(0, index).reduce((sum, v) => sum + (v / total) * 360, 0);
              
              return (
                <div
                  key={index}
                  className="absolute inset-0"
                  style={{
                    background: `conic-gradient(from ${rotation}deg, ${colors[index % colors.length]} ${percentage}%, transparent ${percentage}%)`
                  }}
                />
              );
            })}
          </div>
          
          {/* 레전드 */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            {data.labels.map((label, index) => (
              <div key={index} className="flex items-center text-sm">
                <div 
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-gray-700">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div style={{ height: `${height}px` }}>
        {type === 'pie' || type === 'doughnut' ? renderSimplePieChart() : renderSimpleLineChart()}
      </div>
      
      {/* Chart.js 미설치 안내 */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        💡 더 정교한 차트를 위해 Chart.js 설치 권장
      </div>
    </div>
  );
}

export default TrendChart;