"""通用流程控制工具。

这里只放与具体业务无关的「等待 / 点击 / 状态推进」逻辑，
具体识别内容全部来自 ``src/library.py`` 的特征注册表。
"""

import time

from src.library import find_one, wait_click
from src.options import random_interval


def click_until_next(task, current, expected, *, click_timeout=10.0, verify_timeout=6.0,
                     attempts=3, poll=1.0):
    """点击 current，直到 expected 出现。

    每次点击后在 verify_timeout 内检测 expected；若 current 连续两次仍可见，
    视为点击未生效（动画或延迟），继续重试。检测到 expected 时返回 True。
    """
    for _ in range(attempts):
        if not wait_click(task, current, time_out=click_timeout):
            if find_one(task, expected):
                return True
            task.sleep(random_interval(task, poll))
            continue
        waited = 0.0
        current_seen = 0
        while waited < verify_timeout:
            if find_one(task, expected):
                return True
            if find_one(task, current):
                current_seen += 1
                if current_seen >= 2:
                    break
            else:
                current_seen = 0
            task.sleep(random_interval(task, poll))
            waited += poll
        if find_one(task, expected):
            return True
    return False


def drive_until_next_screen(task, current_feature, next_feature, *, current_key="",
                            next_key="", action_delay=2.0):
    """在两个界面之间反复推进，直到 next 已被激活且两个界面都不再出现。

    配置了按键则发送按键，否则执行普通点击。用于结算页 / 确认页这类
    需要连续确认的场景，不会自行放弃。
    """
    pressed_next = False
    idle_started = None
    while True:
        if find_one(task, next_feature):
            if next_key:
                task.send_key(next_key, down_time=0.05)
            else:
                wait_click(task, next_feature, time_out=5)
            pressed_next = True
            idle_started = None
            task.sleep(random_interval(task, action_delay))
            continue
        if find_one(task, current_feature):
            if current_key:
                task.send_key(current_key, down_time=0.05)
            else:
                wait_click(task, current_feature, time_out=5)
            pressed_next = False
            idle_started = None
            task.sleep(random_interval(task, action_delay))
            continue
        if pressed_next:
            return True
        now = time.monotonic()
        if idle_started is None:
            idle_started = now
            task.log_info("idle: waiting for %s/%s" % (current_feature, next_feature))
        elif now - idle_started >= 15:
            frame_note = ""
            if getattr(task.executor, "frame", None) is None:
                frame_note = " frame=None"
            task.log_warning(
                "idle for %ds: %s/%s not visible, keep polling%s"
                % (int(now - idle_started), current_feature, next_feature, frame_note))
            idle_started = now
        task.sleep(random_interval(task, max(1.0, action_delay)))
