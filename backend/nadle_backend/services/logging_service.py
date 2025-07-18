"""
기본 로깅 서비스

내부 애플리케이션 로그 수집, 저장, 조회를 담당하는 핵심 서비스
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING, ASCENDING

from ..models.logging import (
    LogEntry, LogLevel, LogSource, ServiceType, LogContext, LogMetadata,
    LogFilter, LogStats, ErrorGrouping, LogEntryResponse, LogListResponse,
    LogDashboardResponse, PerformanceMetric
)
from ..database.manager import get_database
from ..services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class LoggingService:
    """
    통합 로깅 서비스
    
    로그 수집, 저장, 조회, 통계 생성을 담당
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        
    async def get_database(self) -> AsyncIOMotorDatabase:
        """데이터베이스 연결 반환"""
        return await get_database()
    
    async def log_entry(
        self,
        level: LogLevel,
        service: ServiceType,
        source: LogSource,
        message: str,
        context: Optional[LogContext] = None,
        metadata: Optional[LogMetadata] = None,
        stack_trace: Optional[str] = None
    ) -> LogEntry:
        """
        로그 엔트리 생성 및 저장
        
        Args:
            level: 로그 레벨
            service: 서비스 타입
            source: 로그 소스
            message: 로그 메시지
            context: 컨텍스트 정보
            metadata: 메타데이터
            stack_trace: 스택 트레이스
            
        Returns:
            저장된 로그 엔트리
        """
        try:
            # 로그 엔트리 생성
            log_entry = LogEntry(
                level=level,
                service=service,
                source=source,
                message=message,
                context=context,
                metadata=metadata,
                stack_trace=stack_trace
            )
            
            # 데이터베이스에 저장
            await log_entry.insert()
            
            # 에러인 경우 에러 그룹핑 처리
            if level == LogLevel.ERROR:
                await self._handle_error_grouping(log_entry)
            
            # 캐시 무효화 (통계 캐시)
            await self._invalidate_stats_cache()
            
            logger.debug(f"로그 엔트리 저장 완료: {log_entry.id}")
            return log_entry
            
        except Exception as e:
            logger.error(f"로그 엔트리 저장 실패: {e}")
            raise
    
    async def get_logs(
        self,
        filter_criteria: LogFilter
    ) -> LogListResponse:
        """
        필터 조건에 따른 로그 목록 조회
        
        Args:
            filter_criteria: 필터링 조건
            
        Returns:
            로그 목록 응답
        """
        try:
            # 쿼리 조건 구성
            query = await self._build_query(filter_criteria)
            
            # 총 개수 조회
            total_count = await LogEntry.find(query).count()
            
            # 페이징 계산
            skip = (filter_criteria.page - 1) * filter_criteria.page_size
            
            # 로그 목록 조회
            logs = await LogEntry.find(query) \
                .sort([("timestamp", DESCENDING)]) \
                .skip(skip) \
                .limit(filter_criteria.page_size) \
                .to_list()
            
            # 응답 모델로 변환
            log_responses = [
                LogEntryResponse(
                    id=str(log.id),
                    timestamp=log.timestamp,
                    level=log.level,
                    service=log.service,
                    source=log.source,
                    message=log.message,
                    context=log.context,
                    metadata=log.metadata,
                    stack_trace=log.stack_trace
                ) for log in logs
            ]
            
            return LogListResponse(
                logs=log_responses,
                total_count=total_count,
                page=filter_criteria.page,
                page_size=filter_criteria.page_size,
                has_next=skip + filter_criteria.page_size < total_count,
                has_prev=filter_criteria.page > 1
            )
            
        except Exception as e:
            logger.error(f"로그 목록 조회 실패: {e}")
            raise
    
    async def get_log_by_id(self, log_id: str) -> Optional[LogEntryResponse]:
        """
        ID로 특정 로그 조회
        
        Args:
            log_id: 로그 ID
            
        Returns:
            로그 엔트리 응답 또는 None
        """
        try:
            log = await LogEntry.get(log_id)
            if not log:
                return None
            
            return LogEntryResponse(
                id=str(log.id),
                timestamp=log.timestamp,
                level=log.level,
                service=log.service,
                source=log.source,
                message=log.message,
                context=log.context,
                metadata=log.metadata,
                stack_trace=log.stack_trace
            )
            
        except Exception as e:
            logger.error(f"로그 ID {log_id} 조회 실패: {e}")
            return None
    
    async def get_dashboard_data(
        self,
        hours: int = 24
    ) -> LogDashboardResponse:
        """
        대시보드 데이터 조회
        
        Args:
            hours: 조회 시간 범위 (시간)
            
        Returns:
            대시보드 데이터
        """
        try:
            # 캐시 확인
            cache_key = f"logs:dashboard:{hours}h"
            cached_data = await self.cache_service.get_json(cache_key)
            if cached_data:
                return LogDashboardResponse(**cached_data)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # 병렬로 데이터 수집
            stats_task = self._get_log_stats(start_time, end_time)
            errors_task = self._get_recent_errors(limit=5)
            time_series_task = self._get_time_series_data(start_time, end_time)
            endpoints_task = self._get_top_endpoints(start_time, end_time)
            performance_task = self._get_performance_summary(start_time, end_time)
            
            stats, recent_errors, time_series, top_endpoints, performance = await asyncio.gather(
                stats_task, errors_task, time_series_task, endpoints_task, performance_task
            )
            
            dashboard_data = LogDashboardResponse(
                stats=stats,
                recent_errors=recent_errors,
                time_series=time_series,
                top_endpoints=top_endpoints,
                performance_summary=performance
            )
            
            # 캐시 저장 (5분)
            await self.cache_service.set_json(
                cache_key,
                dashboard_data.dict(),
                expire_time=300
            )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"대시보드 데이터 조회 실패: {e}")
            raise
    
    async def search_logs(
        self,
        query: str,
        filters: Optional[LogFilter] = None,
        limit: int = 100
    ) -> List[LogEntryResponse]:
        """
        로그 텍스트 검색
        
        Args:
            query: 검색 쿼리
            filters: 추가 필터
            limit: 결과 제한
            
        Returns:
            검색 결과 로그 목록
        """
        try:
            # 기본 텍스트 검색 쿼리
            search_query = {
                "$text": {"$search": query}
            }
            
            # 추가 필터 적용
            if filters:
                additional_filters = await self._build_query(filters)
                search_query.update(additional_filters)
            
            # 검색 실행
            logs = await LogEntry.find(search_query) \
                .sort([("score", {"$meta": "textScore"}), ("timestamp", DESCENDING)]) \
                .limit(limit) \
                .to_list()
            
            return [
                LogEntryResponse(
                    id=str(log.id),
                    timestamp=log.timestamp,
                    level=log.level,
                    service=log.service,
                    source=log.source,
                    message=log.message,
                    context=log.context,
                    metadata=log.metadata,
                    stack_trace=log.stack_trace
                ) for log in logs
            ]
            
        except Exception as e:
            logger.error(f"로그 검색 실패: {e}")
            return []
    
    async def log_performance_metric(
        self,
        service: ServiceType,
        metric_name: str,
        metric_value: float,
        unit: str,
        endpoint: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> PerformanceMetric:
        """
        성능 메트릭 로깅
        
        Args:
            service: 서비스 타입
            metric_name: 메트릭 이름
            metric_value: 메트릭 값
            unit: 단위
            endpoint: 엔드포인트
            tags: 태그
            
        Returns:
            저장된 성능 메트릭
        """
        try:
            metric = PerformanceMetric(
                service=service,
                metric_name=metric_name,
                metric_value=metric_value,
                unit=unit,
                endpoint=endpoint,
                tags=tags or {}
            )
            
            await metric.insert()
            logger.debug(f"성능 메트릭 저장: {metric_name}={metric_value}{unit}")
            return metric
            
        except Exception as e:
            logger.error(f"성능 메트릭 저장 실패: {e}")
            raise
    
    # 내부 헬퍼 메서드들
    
    async def _build_query(self, filter_criteria: LogFilter) -> Dict[str, Any]:
        """필터 조건을 MongoDB 쿼리로 변환"""
        query = {}
        
        # 시간 범위
        if filter_criteria.start_time or filter_criteria.end_time:
            time_filter = {}
            if filter_criteria.start_time:
                time_filter["$gte"] = filter_criteria.start_time
            if filter_criteria.end_time:
                time_filter["$lte"] = filter_criteria.end_time
            query["timestamp"] = time_filter
        
        # 로그 레벨
        if filter_criteria.levels:
            query["level"] = {"$in": filter_criteria.levels}
        
        # 서비스
        if filter_criteria.services:
            query["service"] = {"$in": filter_criteria.services}
        
        # 소스
        if filter_criteria.sources:
            query["source"] = {"$in": filter_criteria.sources}
        
        # 사용자 ID
        if filter_criteria.user_id:
            query["context.user_id"] = filter_criteria.user_id
        
        # 엔드포인트
        if filter_criteria.endpoint:
            query["context.endpoint"] = {"$regex": filter_criteria.endpoint, "$options": "i"}
        
        # 텍스트 검색
        if filter_criteria.search_query:
            query["$or"] = [
                {"message": {"$regex": filter_criteria.search_query, "$options": "i"}},
                {"stack_trace": {"$regex": filter_criteria.search_query, "$options": "i"}}
            ]
        
        return query
    
    async def _handle_error_grouping(self, log_entry: LogEntry):
        """에러 그룹핑 처리"""
        try:
            # 에러 해시 생성
            error_hash = hashlib.md5(
                f"{log_entry.service}:{log_entry.message}".encode()
            ).hexdigest()
            
            # 기존 그룹 찾기
            existing_group = await ErrorGrouping.find_one({
                "error_hash": error_hash,
                "service": log_entry.service
            })
            
            if existing_group:
                # 기존 그룹 업데이트
                existing_group.count += 1
                existing_group.last_seen = log_entry.timestamp
                await existing_group.save()
            else:
                # 새 그룹 생성
                new_group = ErrorGrouping(
                    error_hash=error_hash,
                    service=log_entry.service,
                    endpoint=log_entry.context.endpoint if log_entry.context else None,
                    sample_message=log_entry.message,
                    sample_stack_trace=log_entry.stack_trace
                )
                await new_group.insert()
                
        except Exception as e:
            logger.error(f"에러 그룹핑 처리 실패: {e}")
    
    async def _get_log_stats(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> LogStats:
        """로그 통계 조회"""
        try:
            # 집계 파이프라인
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "level": "$level",
                            "service": "$service"
                        },
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            db = await self.get_database()
            results = await db.log_entries.aggregate(pipeline).to_list(None)
            
            # 통계 초기화
            stats = LogStats(
                start_time=start_time,
                end_time=end_time
            )
            
            # 결과 처리
            for result in results:
                level = result["_id"]["level"]
                service = result["_id"]["service"]
                count = result["count"]
                
                # 레벨별 카운트
                if level == "ERROR":
                    stats.error_count += count
                elif level == "WARN":
                    stats.warn_count += count
                elif level == "INFO":
                    stats.info_count += count
                elif level == "DEBUG":
                    stats.debug_count += count
                
                # 서비스별 카운트
                if service not in stats.service_stats:
                    stats.service_stats[service] = 0
                stats.service_stats[service] += count
                
                # 총 카운트
                stats.total_count += count
            
            return stats
            
        except Exception as e:
            logger.error(f"로그 통계 조회 실패: {e}")
            return LogStats(start_time=start_time, end_time=end_time)
    
    async def _get_recent_errors(self, limit: int = 5) -> List[ErrorGrouping]:
        """최근 에러 TOP N 조회"""
        try:
            errors = await ErrorGrouping.find({"is_resolved": False}) \
                .sort([("count", DESCENDING), ("last_seen", DESCENDING)]) \
                .limit(limit) \
                .to_list()
            
            return errors
            
        except Exception as e:
            logger.error(f"최근 에러 조회 실패: {e}")
            return []
    
    async def _get_time_series_data(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """시계열 데이터 조회"""
        try:
            # 시간 간격별 집계
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "interval": {
                                "$dateTrunc": {
                                    "date": "$timestamp",
                                    "unit": "hour"
                                }
                            },
                            "level": "$level"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id.interval": 1}
                }
            ]
            
            db = await self.get_database()
            results = await db.log_entries.aggregate(pipeline).to_list(None)
            
            # 시계열 데이터 구성
            time_series = []
            interval_data = {}
            
            for result in results:
                interval = result["_id"]["interval"]
                level = result["_id"]["level"]
                count = result["count"]
                
                interval_str = interval.isoformat()
                if interval_str not in interval_data:
                    interval_data[interval_str] = {
                        "timestamp": interval_str,
                        "error": 0,
                        "warn": 0,
                        "info": 0,
                        "debug": 0
                    }
                
                interval_data[interval_str][level.lower()] = count
            
            time_series = list(interval_data.values())
            return sorted(time_series, key=lambda x: x["timestamp"])
            
        except Exception as e:
            logger.error(f"시계열 데이터 조회 실패: {e}")
            return []
    
    async def _get_top_endpoints(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """상위 엔드포인트 조회"""
        try:
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time},
                        "context.endpoint": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$context.endpoint",
                        "total_requests": {"$sum": 1},
                        "error_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "ERROR"]}, 1, 0]}
                        },
                        "avg_response_time": {"$avg": "$context.response_time"}
                    }
                },
                {
                    "$sort": {"total_requests": -1}
                },
                {
                    "$limit": limit
                }
            ]
            
            db = await self.get_database()
            results = await db.log_entries.aggregate(pipeline).to_list(None)
            
            return [
                {
                    "endpoint": result["_id"],
                    "total_requests": result["total_requests"],
                    "error_count": result["error_count"],
                    "error_rate": (result["error_count"] / result["total_requests"]) * 100,
                    "avg_response_time": round(result["avg_response_time"] or 0, 2)
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"상위 엔드포인트 조회 실패: {e}")
            return []
    
    async def _get_performance_summary(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """성능 요약 데이터 조회"""
        try:
            # 평균 응답 시간 계산
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time},
                        "context.response_time": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$service",
                        "avg_response_time": {"$avg": "$context.response_time"},
                        "max_response_time": {"$max": "$context.response_time"},
                        "request_count": {"$sum": 1}
                    }
                }
            ]
            
            db = await self.get_database()
            results = await db.log_entries.aggregate(pipeline).to_list(None)
            
            performance_summary = {
                "services": {},
                "overall": {
                    "avg_response_time": 0,
                    "max_response_time": 0,
                    "total_requests": 0
                }
            }
            
            total_response_time = 0
            max_response_time = 0
            total_requests = 0
            
            for result in results:
                service = result["_id"]
                avg_time = round(result["avg_response_time"], 2)
                max_time = result["max_response_time"]
                count = result["request_count"]
                
                performance_summary["services"][service] = {
                    "avg_response_time": avg_time,
                    "max_response_time": max_time,
                    "request_count": count
                }
                
                total_response_time += avg_time * count
                max_response_time = max(max_response_time, max_time)
                total_requests += count
            
            if total_requests > 0:
                performance_summary["overall"] = {
                    "avg_response_time": round(total_response_time / total_requests, 2),
                    "max_response_time": max_response_time,
                    "total_requests": total_requests
                }
            
            return performance_summary
            
        except Exception as e:
            logger.error(f"성능 요약 조회 실패: {e}")
            return {"services": {}, "overall": {"avg_response_time": 0, "max_response_time": 0, "total_requests": 0}}
    
    async def _invalidate_stats_cache(self):
        """통계 캐시 무효화"""
        try:
            cache_patterns = [
                "logs:dashboard:*",
                "logs:stats:*"
            ]
            
            for pattern in cache_patterns:
                await self.cache_service.delete_pattern(pattern)
                
        except Exception as e:
            logger.error(f"캐시 무효화 실패: {e}")


def get_logging_service() -> LoggingService:
    """로깅 서비스 팩토리 함수"""
    return LoggingService()