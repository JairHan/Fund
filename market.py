import datetime as dt
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
TRADING_SESSIONS = (
    (dt.time(9, 30), dt.time(11, 30)),
    (dt.time(13, 0), dt.time(15, 0)),
)


def get_market_clock(now=None):
    now = now or dt.datetime.now(SHANGHAI_TZ)
    current_time = now.time()
    is_weekday = now.weekday() < 5
    is_trading = is_weekday and any(
        start <= current_time <= end
        for start, end in TRADING_SESSIONS
    )

    if not is_weekday:
        status = "非交易日"
        detail = "自动刷新已暂停"
    elif current_time < TRADING_SESSIONS[0][0]:
        status = "未开盘"
        detail = "自动刷新将在 09:30 后开启"
    elif TRADING_SESSIONS[0][1] < current_time < TRADING_SESSIONS[1][0]:
        status = "午间休市"
        detail = "自动刷新将在 13:00 后恢复"
    elif current_time > TRADING_SESSIONS[1][1]:
        status = "已收盘"
        detail = "自动刷新已暂停"
    else:
        status = "交易中"
        detail = "自动刷新运行中"

    return {
        "now": now,
        "is_trading": is_trading,
        "status": status,
        "detail": detail,
        "time_text": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
