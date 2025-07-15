/**
 * 통합 모니터링 시스템 타입 정의
 */

export type Environment = 'development' | 'staging' | 'production';

export interface ExternalMonitoring {
  service: string;
  total_monitors: number;
  monitors: Array<{
    id: string;
    name: string;
    url: string;
    status: string;
    uptime: number;
    response_time: Record<string, number>;
    last_check: number;
  }>;
  error?: string;
}

export interface ApplicationMonitoring {
  health_status: string;
  service: string;
  timestamp: string;
  error?: string;
}

export interface CloudRunMetrics {
  status: string;
  cpu_usage: number;
  memory_usage: number;
  instances: number;
  requests_per_second?: number;
  latency_p95?: number;
}

export interface VercelMetrics {
  status: string;
  deployment_status: string;
  function_executions: number;
  bandwidth_usage: number;
  core_web_vitals?: {
    lcp: number;
    fid: number;
    cls: number;
  };
}

export interface AtlasMetrics {
  status: string;
  connections: number;
  read_latency: number;
  write_latency: number;
  cpu_usage?: number;
  memory_usage?: number;
}

export interface UpstashMetrics {
  status: string;
  hit_rate: number;
  memory_usage: number;
  connections: number;
  operations_per_second?: number;
}

export interface InfrastructureMonitoring {
  cloud_run?: CloudRunMetrics;
  vercel?: VercelMetrics;
  atlas?: AtlasMetrics;
  upstash?: UpstashMetrics;
  error?: string;
}

export interface UnifiedMonitoringData {
  environment: Environment;
  timestamp: string;
  external_monitoring: ExternalMonitoring;
  application_monitoring: ApplicationMonitoring;
  infrastructure_monitoring: InfrastructureMonitoring;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code?: string;
    details?: any;
  };
}

export interface EnvironmentConfig {
  name: Environment;
  label: string;
  emoji: string;
  description: string;
  color: 'yellow' | 'blue' | 'green';
}

export interface MonitoringApiEndpoints {
  dashboard: (environment: Environment) => string;
  environments: string;
  hetrixMonitors: (environment?: Environment) => string;
  infrastructureStatus: (environment?: Environment) => string;
  healthSimple: string;
  healthComprehensive: string;
}

export interface StatusIcon {
  healthy: string;
  unhealthy: string;
  warning: string;
  unknown: string;
}

export interface MonitoringConfig {
  autoRefresh: boolean;
  refreshInterval: number;
  statusIcons: StatusIcon;
  environments: EnvironmentConfig[];
  apiEndpoints: MonitoringApiEndpoints;
}