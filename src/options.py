import random

OPTIONS_NAME = '选项'
RANDOM_RANGE_KEY = '点击随机区间'


def get_click_random_range(task):
    """读取全局选项中的点击随机抖动区间，异常时回退为 0。"""
    options = task.get_global_config(OPTIONS_NAME)
    if options is None:
        return 0.0
    try:
        return max(0.0, float(options.get(RANDOM_RANGE_KEY) or 0))
    except (TypeError, ValueError):
        return 0.0


def random_interval(task, base):
    """在 base 秒附近加入随机抖动，避免固定节拍。"""
    spread = get_click_random_range(task)
    if spread <= 0:
        return base
    return max(0.1, base + random.uniform(-spread, spread))
