import time

from ok.device.interaction_methods.post_message import PostMessageInteraction
from qfluentwidgets import FluentIcon

from src.tasks.base import MyBaseTask
from src.window_broadcast import BroadcastKeyboard, list_game_windows

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

    多开支持：启用「多窗口同步下发」时，按键会同时投递给所有匹配的游戏窗口
    （标题正则 + 进程名），运行中按「窗口刷新间隔」重扫，窗口开关自动跟随。
    """

    # 本任务支持的技能集合：(发送给游戏的键, GUI 显示名, 默认间隔秒)
    skill_defs = SKILLS
    loop_label = "技能循环"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "技能循环"
        self.description = "Q/R/F/G 四个技能独立开关与独立间隔，到点自动施放，循环执行。"
        self.icon = FluentIcon.SYNC
        self._activate_before_press = True

        for key, label, interval in self.skill_defs:
            self.default_config[f"{label} 启用"] = key == "q"
            self.default_config[f"{label} 间隔(秒)"] = interval
        self.default_config.update({
            "按键按下时长": 0.15,
            "启动后延迟": 1.0,
            "多窗口同步下发": True,
            "窗口刷新间隔(秒)": 5.0,
            "按键前激活窗口": True,
        })

        for key, label, _ in self.skill_defs:
            self.config_description[f"{label} 启用"] = f"是否循环施放 {label.upper()} 键。"
            self.config_description[f"{label} 间隔(秒)"] = (
                f"{label.upper()} 的施放间隔，单位秒，最小 {MIN_INTERVAL} 秒。")
        self.config_description.update({
            "按键按下时长": "每次按键按住的秒数。低于 0.1 秒可能被游戏刻采样丢弃。",
            "启动后延迟": "点击开始后等待的秒数，留出切换到游戏窗口的时间。",
            "多窗口同步下发": (
                "开启后按键同时发给所有标题与进程名匹配的游戏窗口，用于多开；"
                "仅 PostMessage 交互方式有效，其他方式会自动退回单窗口。"),
            "窗口刷新间隔(秒)": "运行中重新扫描窗口列表的间隔，关掉的窗口自动剔除，新开的自动加入。",
            "按键前激活窗口": (
                "按键前向目标窗口发送激活消息，与原单窗口逻辑一致；"
                "多开时若出现暂停/恢复异常可关闭此项。"),
        })

    def run(self):
        skills = self._build_skills()
        if not skills:
            self.log_warning("没有启用任何技能，任务结束。请至少开启一个技能。", notify=True)
            return

        press = self._clamp_float("按键按下时长", 0.15, 0.05, 1.0)
        delay = max(0.0, self._clamp_float("启动后延迟", 1.0, 0.0, 60.0))
        refresh_interval = self._clamp_float("窗口刷新间隔(秒)", 5.0, 1.0, 60.0)
        self._activate_before_press = bool(self.config.get("按键前激活窗口", True))

        sender = self._build_sender()

        plan = "，".join(
            f"{s['label']} 每 {s['interval']:.1f}s" for s in skills)
        target = f"同步 {sender.count} 个窗口" if sender else "单窗口模式"
        self.info_set("同步窗口", sender.count if sender else 1)
        self.log_info(
            f"{self.loop_label}启动：{plan}；按键时长 {press:.2f}s；{target}", notify=True)
        if sender:
            self.log_info(f"窗口清单：{sender.describe()}")
        if delay > 0:
            self.sleep(delay)

        now = time.monotonic()
        for skill in skills:
            skill["next_at"] = now
            skill["count"] = 0
            self.info_set(f"{skill['label']} 次数", 0)

        next_refresh = now + refresh_interval
        while True:
            now = time.monotonic()
            if sender is not None and now >= next_refresh:
                self._refresh_sender(sender)
                next_refresh = now + refresh_interval

            for skill in skills:
                if skill["next_at"] > now:
                    continue
                if not self._press(sender, skill["key"], press):
                    self.log_warning("所有目标窗口均已失效，任务结束。", notify=True)
                    return
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

    def _press(self, sender, key, press):
        """下发一次按键；返回 False 表示没有任何可用窗口。"""
        if sender is None:
            self.send_key(key, down_time=press)
            return True
        if sender.send_key(key, down_time=press, activate=self._activate_before_press) > 0:
            return True
        # 投递瞬间窗口全关，重扫一次确认是否真的没窗口了
        self._refresh_sender(sender)
        return sender.count > 0

    def _build_sender(self):
        """按配置决定是否启用多窗口广播；不可用时返回 None（回退单窗口）。"""
        if not bool(self.config.get("多窗口同步下发", True)):
            self.log_info("「多窗口同步下发」已关闭，按键只发给当前选中窗口。")
            return None

        interaction = getattr(self.executor, "interaction", None)
        if not isinstance(interaction, PostMessageInteraction):
            self.log_warning(
                "当前交互方式不是 PostMessage，无法向多个窗口同时下发按键，已退回单窗口模式。",
                notify=True)
            return None

        sender = BroadcastKeyboard(interaction)
        if sender.bind(self._scan_windows()) == 0:
            self.log_warning("未枚举到匹配的游戏窗口，已退回单窗口模式。", notify=True)
            return None
        return sender

    def _scan_windows(self):
        """按当前窗口配置（标题正则 + 进程名）枚举所有匹配的游戏窗口。"""
        device_manager = getattr(self.executor, "device_manager", None)
        windows_config = getattr(device_manager, "windows_capture_config", None) or {}
        return list_game_windows(windows_config.get("title"), windows_config.get("exe"))

    def _refresh_sender(self, sender):
        """重扫窗口列表，数量变化时写日志并更新信息面板。"""
        before = sender.count
        after = sender.bind(self._scan_windows())
        if after == before:
            return
        self.info_set("同步窗口", after)
        if after == 0:
            self.log_warning("当前没有可用的游戏窗口，等待窗口重新出现……")
        else:
            self.log_info(f"同步窗口数量 {before} → {after}：{sender.describe()}")

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
