"""多开窗口广播：把同一按键同时投递给所有匹配的游戏窗口。

框架的按键链路绑定单个 hwnd（``PostMessageInteraction.hwnd``），多开时只会命中
其中一个窗口。本模块在任务层补齐这一层：先用标题正则 + 进程名枚举全部匹配窗口，
再复用当前交互实例的键码转换与 lparam 构造，把 WM_KEYDOWN/UP 逐个投递给每个窗口，
语义与单窗口路径保持一致。
"""

import time
from dataclasses import dataclass

import win32con
import win32gui

from ok.util.logger import Logger
from ok.util.window import find_all_visible_windows

logger = Logger.get_logger(__name__)


@dataclass(frozen=True)
class GameWindow:
    """一个可下发按键的游戏窗口。"""

    hwnd: int
    title: str
    exe: str


def _exe_matches(exe_name, exe_names):
    """进程名比对，忽略大小写。"""
    if not exe_names:
        return True
    if isinstance(exe_names, str):
        exe_names = [exe_names]
    name = (exe_name or "").casefold()
    return any(name == str(item).casefold() for item in exe_names)


def list_game_windows(title_pattern, exe_names=None):
    """枚举所有标题与进程名同时匹配的可见窗口。

    Args:
        title_pattern: 标题匹配规则，传正则（``re.Pattern``）或子串。
        exe_names: 进程名白名单，如 ``['java.exe', 'javaw.exe']``；None 表示不限。

    Returns:
        GameWindow 列表，按 hwnd 升序；无匹配时为空列表。
    """
    windows = []
    for hwnd, title, exe_name, _full_path in find_all_visible_windows():
        if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowEnabled(hwnd):
            continue
        text = title or ""
        if title_pattern is not None:
            if hasattr(title_pattern, "search"):
                if not title_pattern.search(text):
                    continue
            elif str(title_pattern) not in text:
                continue
        if not _exe_matches(exe_name, exe_names):
            continue
        windows.append(GameWindow(hwnd=hwnd, title=text, exe=exe_name or ""))
    windows.sort(key=lambda item: item.hwnd)
    return windows


class BroadcastKeyboard:
    """基于窗口消息的多窗口按键广播。

    只复用 interaction 的纯计算方法（``get_key_by_str`` / ``make_lparam`` /
    ``post`` / ``activate``），不改变其绑定窗口，因此不影响框架自身的截图与识别链路。

    Args:
        interaction: ``PostMessageInteraction`` 实例，由任务层传入。
    """

    def __init__(self, interaction):
        self.interaction = interaction
        self.windows = []

    @property
    def count(self):
        return len(self.windows)

    def bind(self, windows):
        """替换目标窗口列表并剔除已关闭句柄，返回剩余可用数量。"""
        self.windows = [w for w in windows if win32gui.IsWindow(w.hwnd)]
        return len(self.windows)

    def send_key(self, key, down_time=0.15, activate=True):
        """向所有目标窗口投递一次按键，返回实际投递的窗口数。

        所有窗口先统一按下、等待 ``down_time`` 后再统一抬起，避免串行按键造成
        窗口之间的相位差；抬键放在 finally 中，异常时也不会留下按住不放的键。
        """
        targets = [w.hwnd for w in self.windows if win32gui.IsWindow(w.hwnd)]
        self.windows = [w for w in self.windows if w.hwnd in targets]
        if not targets:
            return 0

        vk_code = self.interaction.get_key_by_str(key)
        lparam_down = self.interaction.make_lparam(vk_code, is_up=False)
        lparam_up = self.interaction.make_lparam(vk_code, is_up=True)

        if activate:
            for hwnd in targets:
                self.interaction.activate(hwnd)
        try:
            for hwnd in targets:
                self.interaction.post(win32con.WM_KEYDOWN, vk_code, lparam_down, hwnd=hwnd)
            time.sleep(down_time)
        finally:
            for hwnd in targets:
                self.interaction.post(win32con.WM_KEYUP, vk_code, lparam_up, hwnd=hwnd)
        return len(targets)

    def describe(self):
        """返回窗口清单的可读描述，用于日志确认实际生效的窗口。"""
        return "，".join(f"{w.title}#{w.hwnd}" for w in self.windows) or "无"
