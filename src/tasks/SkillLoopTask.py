import time

from qfluentwidgets import FluentIcon

from src.tasks.base import MyBaseTask

# 四个技能键：固定按键，GUI 中按 Q/R/F/G 分组配置
SKILLS = (
    ("q", "Q", 3.0),
    ("r", "R", 5.0),
    ("f", "F", 8.0),
    ("g", "G", 12.0),
)

MIN_INTERVAL = 0.2   # 间隔下限，防止误填 0 导致疯狂连按
MAX_WAIT = 0.25      # 单次休眠上限，保证停止响应及时


class SkillLoopTask(MyBaseTask):
    """技能循环施法：四个技能各自独立计时，到点按一次。

    设计要点：
    - 每个键独立开关、独立间隔，互不干扰（不是固定连招顺序）；
    - 间隔精确计时，不叠加全局点击随机抖动，避免技能节奏漂移；
    - 按键按下时长默认 0.15s，满足 Minecraft 50ms 刻采样，过短会被整刻丢弃。

    子类可通过覆盖 ``skill_defs`` 收窄技能集合，``skill_defs`` 的排列顺序同时决定
    同一时刻多个技能同时到期时的施放顺序（靠前者先按），循环内核无需改动。
    """

    # 本任务支持的技能集合：(发送给游戏的键, GUI 显示名, 默认间隔秒)
    skill_defs = SKILLS
    loop_label = "技能循环"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "技能循环"
        self.description = "Q/R/F/G 四个技能独立开关与独立间隔，到点自动施放，循环执行。"
        self.icon = FluentIcon.SYNC

        for key, label, interval in self.skill_defs:
            self.default_config[f"{label} 启用"] = key == "q"
            self.default_config[f"{label} 间隔(秒)"] = interval
        self.default_config.update({
            "按键按下时长": 0.15,
            "启动后延迟": 1.0,
        })

        for key, label, _ in self.skill_defs:
            self.config_description[f"{label} 启用"] = f"是否循环施放 {label.upper()} 键。"
            self.config_description[f"{label} 间隔(秒)"] = (
                f"{label.upper()} 的施放间隔，单位秒，最小 {MIN_INTERVAL} 秒。")
        self.config_description.update({
            "按键按下时长": "每次按键按住的秒数。低于 0.1 秒可能被游戏刻采样丢弃。",
            "启动后延迟": "点击开始后等待的秒数，留出切换到游戏窗口的时间。",
        })

    def run(self):
        skills = self._build_skills()
        if not skills:
            self.log_warning("没有启用任何技能，任务结束。请至少开启一个技能。", notify=True)
            return

        press = self._clamp_float("按键按下时长", 0.15, 0.05, 1.0)
        delay = max(0.0, self._clamp_float("启动后延迟", 1.0, 0.0, 60.0))

        plan = "，".join(
            f"{s['label']} 每 {s['interval']:.1f}s" for s in skills)
        self.log_info(f"{self.loop_label}启动：{plan}；按键时长 {press:.2f}s", notify=True)
        if delay > 0:
            self.sleep(delay)

        now = time.monotonic()
        for skill in skills:
            skill["next_at"] = now
            skill["count"] = 0
            self.info_set(f"{skill['label']} 次数", 0)

        while True:
            now = time.monotonic()
            for skill in skills:
                if skill["next_at"] > now:
                    continue
                self.send_key(skill["key"], down_time=press)
                skill["count"] += 1
                skill["next_at"] += skill["interval"]
                # 一帧耗时超过一个间隔时不再补按，直接对齐到下一轮，避免连发
                if skill["next_at"] <= now:
                    skill["next_at"] = now + skill["interval"]
                self.info_set(f"{skill['label']} 次数", skill["count"])
                self.log_debug(
                    f"{skill['label']} 第 {skill['count']} 次施放，下次 {skill['interval']:.1f}s 后")

            now = time.monotonic()
            wait = min(skill["next_at"] for skill in skills) - now
            self.sleep(max(0.02, min(wait, MAX_WAIT)))

    def _build_skills(self):
        skills = []
        for key, label, default_interval in self.skill_defs:
            if not bool(self.config.get(f"{label} 启用", False)):
                continue
            interval = self._clamp_float(
                f"{label} 间隔(秒)", default_interval, MIN_INTERVAL, 3600.0)
            skills.append({
                "key": key,
                "label": label,
                "interval": interval,
            })
        return skills

    def _clamp_float(self, key, default, low, high):
        try:
            value = float(self.config.get(key, default))
        except (TypeError, ValueError):
            value = default
        return min(high, max(low, value))
