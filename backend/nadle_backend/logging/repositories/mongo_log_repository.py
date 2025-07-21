"""
MongoDB implementation of the LogRepositoryInterface.

Uses Motor (async MongoDB driver) with native operations instead of Beanie ODM
to avoid enum extension issues and provide better performance for high-volume logs.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, IndexModel
import hashlib
import logging

from ...core.logging import (
    LogRepositoryInterface,
    LogEntry,
    LogFilter,
    LogStats,
    LogListResponse,
    ErrorGrouping,
    TimeSeriesData,
    TopEndpoint,
    RepositoryError,
    LogLevel,
    LogServiceType,
    LogSource,
)

logger = logging.getLogger(__name__)


class MongoLogRepository(LogRepositoryInterface):
    """
    MongoDB implementation of log repository using Motor native operations.

    This implementation uses Motor directly instead of Beanie to avoid
    enum extension issues and provide better control over indexes and queries.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize the MongoDB log repository.

        Args:
            database: AsyncIOMotorDatabase instance
        """
        self.database = database
        self.logs_collection: AsyncIOMotorCollection = database.logs
        self._indexes_created = False

    async def setup_indexes(self) -> None:
        """
        Create optimized indexes for log queries.

        Creates compound indexes for efficient filtering and sorting.
        """
        try:
            if self._indexes_created:
                return

            # Create indexes for optimal query performance
            indexes = [
                # Primary query index: level + service + timestamp
                IndexModel(
                    [
                        ("level", ASCENDING),
                        ("service", ASCENDING),
                        ("timestamp", DESCENDING),
                    ],
                    name="level_service_timestamp",
                ),
                # Source and timestamp index
                IndexModel(
                    [("source", ASCENDING), ("timestamp", DESCENDING)],
                    name="source_timestamp",
                ),
                # Context-based indexes
                IndexModel(
                    [("context.user_id", ASCENDING), ("timestamp", DESCENDING)],
                    name="user_timestamp",
                    sparse=True,
                ),
                IndexModel(
                    [
                        ("context.endpoint", ASCENDING),
                        ("level", ASCENDING),
                        ("timestamp", DESCENDING),
                    ],
                    name="endpoint_level_timestamp",
                    sparse=True,
                ),
                # Text search index for messages and stack traces
                IndexModel(
                    [("message", "text"), ("stack_trace", "text")], name="text_search"
                ),
                # Error grouping index
                IndexModel(
                    [
                        ("level", ASCENDING),
                        ("service", ASCENDING),
                        ("metadata.error_hash", ASCENDING),
                    ],
                    name="error_grouping",
                    sparse=True,
                ),
                # Performance analysis index
                IndexModel(
                    [
                        ("context.endpoint", ASCENDING),
                        ("context.response_time", ASCENDING),
                        ("timestamp", DESCENDING),
                    ],
                    name="performance_analysis",
                    sparse=True,
                ),
                # Cleanup index for log retention
                IndexModel(
                    [("timestamp", ASCENDING), ("level", ASCENDING)],
                    name="cleanup_index",
                ),
            ]

            await self.logs_collection.create_indexes(indexes)
            self._indexes_created = True
            logger.info("MongoDB log indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise RepositoryError(f"Index creation failed: {str(e)}")

    async def save_log(self, log_entry: LogEntry) -> LogEntry:
        """
        Save a single log entry to MongoDB.

        Args:
            log_entry: The log entry to save

        Returns:
            The saved log entry with populated ID
        """
        try:
            # Convert log entry to dict, excluding None id
            doc = log_entry.model_dump(exclude={"id"}, exclude_none=True)

            # Add error hash for grouping if it's an error
            if log_entry.level == LogLevel.ERROR and log_entry.stack_trace:
                error_content = f"{log_entry.message}:{log_entry.stack_trace}"
                error_hash = hashlib.md5(error_content.encode()).hexdigest()
                if "metadata" not in doc:
                    doc["metadata"] = {}
                doc["metadata"]["error_hash"] = error_hash

            # Insert document
            result = await self.logs_collection.insert_one(doc)

            # Update log entry with generated ID
            log_entry.id = str(result.inserted_id)

            return log_entry

        except Exception as e:
            logger.error(f"Failed to save log entry: {e}")
            raise RepositoryError(f"Failed to save log: {str(e)}")

    async def save_logs_batch(self, log_entries: List[LogEntry]) -> List[LogEntry]:
        """
        Save multiple log entries in a batch operation.

        Args:
            log_entries: List of log entries to save

        Returns:
            List of saved log entries with populated IDs
        """
        try:
            if not log_entries:
                return []

            # Convert log entries to documents
            docs = []
            for log_entry in log_entries:
                doc = log_entry.model_dump(exclude={"id"}, exclude_none=True)

                # Add error hash for errors
                if log_entry.level == LogLevel.ERROR and log_entry.stack_trace:
                    error_content = f"{log_entry.message}:{log_entry.stack_trace}"
                    error_hash = hashlib.md5(error_content.encode()).hexdigest()
                    if "metadata" not in doc:
                        doc["metadata"] = {}
                    doc["metadata"]["error_hash"] = error_hash

                docs.append(doc)

            # Batch insert
            result = await self.logs_collection.insert_many(docs)

            # Update log entries with generated IDs
            for i, inserted_id in enumerate(result.inserted_ids):
                log_entries[i].id = str(inserted_id)

            return log_entries

        except Exception as e:
            logger.error(f"Failed to save log batch: {e}")
            raise RepositoryError(f"Failed to save log batch: {str(e)}")

    async def search_logs(self, filter_obj: LogFilter) -> LogListResponse:
        """
        Search logs with filtering and pagination.

        Args:
            filter_obj: Filter criteria and pagination parameters

        Returns:
            LogListResponse with logs and pagination info
        """
        try:
            # Build query
            query = self._build_query(filter_obj)

            # Get total count
            total_count = await self.logs_collection.count_documents(query)

            # Get paginated logs
            cursor = self.logs_collection.find(query)
            cursor = cursor.sort("timestamp", DESCENDING)
            cursor = cursor.skip(filter_obj.skip).limit(filter_obj.page_size)

            docs = await cursor.to_list(length=filter_obj.page_size)

            # Convert documents to LogEntry objects
            logs = []
            for doc in docs:
                doc["id"] = str(doc.pop("_id"))
                logs.append(LogEntry(**doc))

            return LogListResponse.create(
                logs=logs,
                total_count=total_count,
                page=filter_obj.page,
                page_size=filter_obj.page_size,
            )

        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            raise RepositoryError(f"Failed to search logs: {str(e)}")

    async def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """
        Retrieve a single log entry by ID.

        Args:
            log_id: The log entry ID

        Returns:
            The log entry if found, None otherwise
        """
        try:
            from bson import ObjectId

            doc = await self.logs_collection.find_one({"_id": ObjectId(log_id)})

            if not doc:
                return None

            doc["id"] = str(doc.pop("_id"))
            return LogEntry(**doc)

        except Exception as e:
            logger.error(f"Failed to get log by ID: {e}")
            raise RepositoryError(f"Failed to get log: {str(e)}")

    async def get_stats(self, start_time: datetime, end_time: datetime) -> LogStats:
        """
        Get log statistics for a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            LogStats with aggregated statistics
        """
        try:
            query = {"timestamp": {"$gte": start_time, "$lte": end_time}}

            # Aggregate statistics
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_count": {"$sum": 1},
                        "error_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "ERROR"]}, 1, 0]}
                        },
                        "warn_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "WARN"]}, 1, 0]}
                        },
                        "info_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "INFO"]}, 1, 0]}
                        },
                        "debug_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "DEBUG"]}, 1, 0]}
                        },
                        "avg_response_time": {"$avg": "$context.response_time"},
                        "max_response_time": {"$max": "$context.response_time"},
                    }
                },
            ]

            stats_result = await self.logs_collection.aggregate(pipeline).to_list(1)

            if not stats_result:
                return LogStats(start_time=start_time, end_time=end_time)

            stats = stats_result[0]

            # Get service breakdown
            service_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$service", "count": {"$sum": 1}}},
            ]

            service_stats = {}
            async for doc in self.logs_collection.aggregate(service_pipeline):
                service_stats[doc["_id"]] = doc["count"]

            # Get source breakdown
            source_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            ]

            source_stats = {}
            async for doc in self.logs_collection.aggregate(source_pipeline):
                source_stats[doc["_id"]] = doc["count"]

            # Calculate error rate
            total_count = stats.get("total_count", 0)
            error_count = stats.get("error_count", 0)
            error_rate = LogStats.calculate_error_rate(error_count, total_count)

            return LogStats(
                total_count=total_count,
                error_count=error_count,
                warn_count=stats.get("warn_count", 0),
                info_count=stats.get("info_count", 0),
                debug_count=stats.get("debug_count", 0),
                service_stats=service_stats,
                source_stats=source_stats,
                start_time=start_time,
                end_time=end_time,
                avg_response_time=stats.get("avg_response_time"),
                max_response_time=stats.get("max_response_time"),
                error_rate=error_rate,
            )

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise RepositoryError(f"Failed to get stats: {str(e)}")

    async def get_error_groupings(
        self, start_time: datetime, end_time: datetime, limit: int = 10
    ) -> List[ErrorGrouping]:
        """
        Get top error groupings for a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of error groupings to return

        Returns:
            List of error groupings sorted by frequency
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "level": "ERROR",
                        "timestamp": {"$gte": start_time, "$lte": end_time},
                        "metadata.error_hash": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.error_hash",
                        "count": {"$sum": 1},
                        "service": {"$first": "$service"},
                        "endpoint": {"$first": "$context.endpoint"},
                        "first_seen": {"$min": "$timestamp"},
                        "last_seen": {"$max": "$timestamp"},
                        "sample_message": {"$first": "$message"},
                        "sample_stack_trace": {"$first": "$stack_trace"},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit},
            ]

            error_groupings = []
            async for doc in self.logs_collection.aggregate(pipeline):
                error_grouping = ErrorGrouping(
                    id=doc["_id"],
                    error_hash=doc["_id"],
                    service=LogServiceType(doc["service"]),
                    endpoint=doc.get("endpoint"),
                    count=doc["count"],
                    first_seen=doc["first_seen"],
                    last_seen=doc["last_seen"],
                    sample_message=doc["sample_message"],
                    sample_stack_trace=doc.get("sample_stack_trace"),
                )
                error_groupings.append(error_grouping)

            return error_groupings

        except Exception as e:
            logger.error(f"Failed to get error groupings: {e}")
            raise RepositoryError(f"Failed to get error groupings: {str(e)}")

    async def get_time_series(
        self, start_time: datetime, end_time: datetime, interval_minutes: int = 60
    ) -> List[TimeSeriesData]:
        """
        Get time series data for charts.

        Args:
            start_time: Start of time range
            end_time: End of time range
            interval_minutes: Time interval in minutes for data points

        Returns:
            List of time series data points
        """
        try:
            # Create time buckets
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time, "$lte": end_time}}},
                {
                    "$group": {
                        "_id": {
                            "timestamp": {
                                "$dateTrunc": {
                                    "date": "$timestamp",
                                    "unit": "minute",
                                    "binSize": interval_minutes,
                                }
                            },
                            "level": "$level",
                        },
                        "count": {"$sum": 1},
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.timestamp",
                        "error": {
                            "$sum": {
                                "$cond": [{"$eq": ["$_id.level", "ERROR"]}, "$count", 0]
                            }
                        },
                        "warn": {
                            "$sum": {
                                "$cond": [{"$eq": ["$_id.level", "WARN"]}, "$count", 0]
                            }
                        },
                        "info": {
                            "$sum": {
                                "$cond": [{"$eq": ["$_id.level", "INFO"]}, "$count", 0]
                            }
                        },
                        "debug": {
                            "$sum": {
                                "$cond": [{"$eq": ["$_id.level", "DEBUG"]}, "$count", 0]
                            }
                        },
                    }
                },
                {"$sort": {"_id": 1}},
            ]

            time_series = []
            async for doc in self.logs_collection.aggregate(pipeline):
                time_series.append(
                    TimeSeriesData(
                        timestamp=doc["_id"],
                        error=doc.get("error", 0),
                        warn=doc.get("warn", 0),
                        info=doc.get("info", 0),
                        debug=doc.get("debug", 0),
                    )
                )

            return time_series

        except Exception as e:
            logger.error(f"Failed to get time series: {e}")
            raise RepositoryError(f"Failed to get time series: {str(e)}")

    async def get_top_endpoints(
        self, start_time: datetime, end_time: datetime, limit: int = 10
    ) -> List[TopEndpoint]:
        """
        Get top endpoints by request count and error rate.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of endpoints to return

        Returns:
            List of top endpoints with statistics
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lte": end_time},
                        "context.endpoint": {"$exists": True, "$ne": None},
                    }
                },
                {
                    "$group": {
                        "_id": "$context.endpoint",
                        "total_requests": {"$sum": 1},
                        "error_count": {
                            "$sum": {"$cond": [{"$eq": ["$level", "ERROR"]}, 1, 0]}
                        },
                        "avg_response_time": {"$avg": "$context.response_time"},
                    }
                },
                {
                    "$addFields": {
                        "error_rate": {
                            "$multiply": [
                                {"$divide": ["$error_count", "$total_requests"]},
                                100,
                            ]
                        }
                    }
                },
                {"$sort": {"total_requests": -1}},
                {"$limit": limit},
            ]

            top_endpoints = []
            async for doc in self.logs_collection.aggregate(pipeline):
                top_endpoint = TopEndpoint(
                    endpoint=doc["_id"],
                    total_requests=doc["total_requests"],
                    error_count=doc["error_count"],
                    error_rate=doc.get("error_rate", 0.0),
                    avg_response_time=doc.get("avg_response_time", 0.0),
                )
                top_endpoints.append(top_endpoint)

            return top_endpoints

        except Exception as e:
            logger.error(f"Failed to get top endpoints: {e}")
            raise RepositoryError(f"Failed to get top endpoints: {str(e)}")

    async def delete_logs_before(
        self, cutoff_date: datetime, level: Optional[str] = None
    ) -> int:
        """
        Delete logs older than the cutoff date.

        Args:
            cutoff_date: Delete logs older than this date
            level: Optional log level filter

        Returns:
            Number of deleted log entries
        """
        try:
            query = {"timestamp": {"$lt": cutoff_date}}

            if level:
                query["level"] = level

            result = await self.logs_collection.delete_many(query)

            logger.info(f"Deleted {result.deleted_count} logs before {cutoff_date}")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Failed to delete logs: {e}")
            raise RepositoryError(f"Failed to delete logs: {str(e)}")

    async def count_logs(self, filter_obj: LogFilter) -> int:
        """
        Count logs matching the filter criteria.

        Args:
            filter_obj: Filter criteria

        Returns:
            Number of matching logs
        """
        try:
            query = self._build_query(filter_obj)
            return await self.logs_collection.count_documents(query)

        except Exception as e:
            logger.error(f"Failed to count logs: {e}")
            raise RepositoryError(f"Failed to count logs: {str(e)}")

    def _build_query(self, filter_obj: LogFilter) -> Dict[str, Any]:
        """
        Build MongoDB query from filter object.

        Args:
            filter_obj: Filter criteria

        Returns:
            MongoDB query dictionary
        """
        query = {}

        # Time range
        if filter_obj.start_time or filter_obj.end_time:
            time_query = {}
            if filter_obj.start_time:
                time_query["$gte"] = filter_obj.start_time
            if filter_obj.end_time:
                time_query["$lte"] = filter_obj.end_time
            query["timestamp"] = time_query

        # Log levels
        if filter_obj.levels:
            query["level"] = {"$in": [level.value for level in filter_obj.levels]}

        # Services
        if filter_obj.services:
            query["service"] = {
                "$in": [service.value for service in filter_obj.services]
            }

        # Sources
        if filter_obj.sources:
            query["source"] = {"$in": [source.value for source in filter_obj.sources]}

        # Text search
        if filter_obj.search_query:
            query["$text"] = {"$search": filter_obj.search_query}

        # Context filters
        if filter_obj.user_id:
            query["context.user_id"] = filter_obj.user_id

        if filter_obj.endpoint:
            query["context.endpoint"] = {"$regex": filter_obj.endpoint, "$options": "i"}

        if filter_obj.status_codes:
            query["context.status_code"] = {"$in": filter_obj.status_codes}

        # Infrastructure filters
        if filter_obj.regions:
            query["context.region"] = {"$in": filter_obj.regions}

        if filter_obj.instance_ids:
            query["context.instance_id"] = {"$in": filter_obj.instance_ids}

        if filter_obj.deployment_ids:
            query["context.deployment_id"] = {"$in": filter_obj.deployment_ids}

        return query
