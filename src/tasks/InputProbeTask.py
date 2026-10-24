import time

import numpy as np
from qfluentwidgets import FluentIcon

from src.tasks.base import MyBaseTask


def _frame_diff(reference, current, sample_width=160):
    """下采样后计算平均绝对差异，降低分辨率与噪声影响。"""
    step = max(1, reference.shape[1] // sample_width)
    left = reference[::step, ::step].astype(np.int16)
    right = current[::step, ::step].astype(np.int16)
    if left.shape != right.shape:
        return 0.0
    return float(np.abs(left - right).mean())


class InputProbeTask(MyBaseTask):
    """按键通道自检：判断当前交互方式能否把按键送进游戏。

    原理：先测一段静止画面的基线抖动，再发送一次按键，比较按键前后
    画面变化是否显著高于基线。用于回答「PostMessage 对这个客户端是否有效」，
    避免盲目切换交互方式。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "按键自检"
        self.description = "检测当前交互方式能否生效：发送一次按键，比较画面变化是否高于基线。"
        self.icon = FluentIcon.SEND
        self.default_config.update({
            "测试按键": "f3",
            "按下时长": 0.15,
            "观察时长": 3.0,
            "判定阈值": 2.0,
        })
        self.config_description.update({
            "测试按键": "建议用会改变界面的按键：F3（调试信息）或 E（背包），不要用移动键。",
            "按下时长": "按住秒数。Minecraft 按 50ms 一个游戏刻采样，建议不低于 0.15 秒，否则可能被整刻丢弃。",
            "观察时长": "发送后持续对比画面的秒数。",
            "判定阈值": "画面平均差异超过该值即判定按键生效；会与基线抖动比较，取两者较大值。",
        })

    def run(self):
        key = str(self.config.get("测试按键") or "f3").strip()
        hold = max(0.02, float(self.config.get("按下时长", 0.15)))
        observe = max(0.5, float(self.config.get("观察时长", 3.0)))
        threshold = max(0.1, float(self.config.get("判定阈值", 2.0)))

        before = self.next_frame()
        if before is None:
            self.log_error("未获取到画面：请确认游戏窗口已连接并被选中。")
            return
        self.screenshot("input_probe_before", before)

        baseline = self._baseline_noise(before)
        self.log_info(
            "基线抖动 %.2f，准备发送按键 [%s]（按住 %.2fs）" % (baseline, key, hold))
        self.send_key(key, down_time=hold)

        limit = max(threshold, baseline * 3)
        max_diff = 0.0
        last = before
        deadline = time.monotonic() + observe
        while time.monotonic() < deadline:
            frame = self.next_frame()
            if frame is not None and frame.shape == before.shape:
                last = frame
                max_diff = max(max_diff, _frame_diff(before, frame))
            if max_diff >= limit:
                break
            self.sleep(0.1)

        self.screenshot("input_probe_after", last)
        effective = max_diff >= limit
        summary = "最大差异 %.2f / 判定线 %.2f（基线 %.2f）" % (max_diff, limit, baseline)
        if effective:
            self.log_info("按键已生效：" + summary + "，当前交互方式可用。", notify=True)
        else:
            self.log_warning(
                "未检测到画面变化：" + summary +
                "。可能原因：客户端用 Raw Input 读取键盘、窗口未聚焦，或该按键在此界面无效。",
                notify=True)

    def _baseline_noise(self, reference, rounds=6, interval=0.1):
        """在按键前采样，量化游戏自身的动画抖动。"""
        noise = 0.0
        for _ in range(rounds):
            frame = self.next_frame()
            if frame is not None and frame.shape == reference.shape:
                noise = max(noise, _frame_diff(reference, frame))
            self.sleep(interval)
        return noise
