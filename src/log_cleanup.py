import os
import time

KEEP_DAYS = 3
LOG_FOLDER = "logs"


def clean_old_logs(folder=LOG_FOLDER, keep_days=KEEP_DAYS):
    """删除 logs 目录下超过保留天数的日志，返回删除数量。"""
    cutoff = time.time() - keep_days * 24 * 60 * 60
    removed = 0
    try:
        entries = os.listdir(folder)
    except OSError:
        return 0
    for name in entries:
        path = os.path.join(folder, name)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
                removed += 1
        except OSError:
            # 运行中的实例可能仍占用日志文件，跳过即可
            continue
    return removed
