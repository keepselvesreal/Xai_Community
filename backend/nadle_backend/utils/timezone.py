"""시간대 관련 유틸리티 함수들"""
from datetime import datetime
from zoneinfo import ZoneInfo


def get_kst_now() -> datetime:
    """현재 한국 시간(KST)을 반환 (timezone-naive)"""
    # 한국 시간을 구하되, timezone 정보는 제거하여 반환
    kst_time = datetime.now(ZoneInfo("Asia/Seoul"))
    return kst_time.replace(tzinfo=None)


def utc_to_kst(utc_dt: datetime) -> datetime:
    """UTC 시간을 한국 시간으로 변환"""
    if utc_dt.tzinfo is None:
        # timezone이 없으면 UTC로 가정
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(ZoneInfo("Asia/Seoul"))


def kst_to_utc(kst_dt: datetime) -> datetime:
    """한국 시간을 UTC로 변환"""
    if kst_dt.tzinfo is None:
        # timezone이 없으면 KST로 가정
        kst_dt = kst_dt.replace(tzinfo=ZoneInfo("Asia/Seoul"))
    return kst_dt.astimezone(ZoneInfo("UTC"))