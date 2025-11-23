import re
from datetime import datetime, timedelta

def parse_weibo_time(time_str):
    """
    将微博的时间字符串转换为 datetime 对象。
    支持格式：
    - 刚刚
    - x分钟前
    - x小时前
    - 昨天 HH:MM
    - MM-DD HH:MM (今年)
    - YYYY-MM-DD (往年)
    - YYYY-MM-DD HH:MM
    """
    now = datetime.now()
    time_str = time_str.strip()

    if "刚刚" in time_str:
        return now

    # x分钟前
    match = re.match(r"(\d+)分钟前", time_str)
    if match:
        minutes = int(match.group(1))
        return now - timedelta(minutes=minutes)

    # x小时前
    match = re.match(r"(\d+)小时前", time_str)
    if match:
        hours = int(match.group(1))
        return now - timedelta(hours=hours)

    # 昨天 HH:MM
    if "昨天" in time_str:
        time_part = time_str.replace("昨天", "").strip()
        try:
            t = datetime.strptime(time_part, "%H:%M")
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            pass

    # MM-DD HH:MM (今年)
    # 微博显示的 "11-23 12:30" 通常指今年
    # 但如果是 "2022-11-23" 则指往年
    
    # 尝试匹配 YYYY-MM-DD
    try:
        return datetime.strptime(time_str, "%Y-%m-%d")
    except ValueError:
        pass
        
    # 尝试匹配 YYYY-MM-DD HH:MM
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    # 尝试匹配 MM-DD HH:MM (默认为今年)
    try:
        dt = datetime.strptime(time_str, "%m-%d %H:%M")
        return dt.replace(year=now.year)
    except ValueError:
        pass
    
    # 尝试匹配 MM-DD (默认为今年)
    try:
        dt = datetime.strptime(time_str, "%m-%d")
        return dt.replace(year=now.year)
    except ValueError:
        pass

    # 如果都匹配不上，返回 None 或当前时间（视情况而定，这里返回 None 以便报错）
    print(f"Warning: Unknown time format: {time_str}")
    return None
