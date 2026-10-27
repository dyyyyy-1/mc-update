"""应用配置入口。

窗口识别说明
------------
ok-script 的 ``windows.title`` 支持两种写法：

1. 字符串：与窗口标题**完全相等**才匹配（全半角、空格都必须一致）；
2. 正则：通过 ``re.search`` 模糊匹配，可兼容各种标题变体。

本项目按窗口名称识别目标游戏，因此使用正则匹配，兼容《》书名号、
全半角冒号、间隔号、连字符与空格等变体。若确认标题固定，可将
``GAME_WINDOW_TITLE`` 直接改成字符串 ``"维亚之巅 起源"`` 以获得严格匹配。

如需进一步提高稳定性，可在 ``WINDOWS_CONFIG`` 中补充 ``exe``（进程名），
例如 ``'exe': ['Xxx-Win64-Shipping.exe']``。进程名与标题同时存在时，
两者都必须匹配；进程名可避免同名窗口误判，也便于后续自动启动游戏。
"""

import os
import re

from ok import ConfigOption

version = "v0.1.3"
# 版本号由打包流程自动改写，请勿手工修改

app_profile = os.environ.get("PYAPPIFY_APP_PROFILE", "")
gui_config = {
    'type': 'web' if app_profile.casefold() == 'web' else 'qt',
    'window_size': {
        'width': 1200,
        'height': 800,
        'min_width': 600,
        'min_height': 450,
    },
}
if gui_config['type'] == 'web':
    gui_config['launch_mode'] = 'pywebview'

window_size = gui_config['window_size']

# ---------------------------------------------------------------------------
# 目标窗口
# ---------------------------------------------------------------------------
GAME_TITLE = "维亚之巅 起源"

# 标题前缀匹配：Minecraft 的窗口标题会随版本号变化（如「维亚之巅 起源 1.20.1」）
GAME_WINDOW_TITLE = re.compile(r'^维亚之巅')

# 进程名约束：Minecraft Java 版的窗口进程为 java.exe / javaw.exe
GAME_EXE = ['java.exe', 'javaw.exe']

# 说明：本工具自身窗口标题同样含「维亚之巅」，只按标题会抓到自己。
# 因此必须同时限定进程名，且工具窗口标题改为带后缀的独立名称。
WINDOWS_CONFIG = {
    'title': GAME_WINDOW_TITLE,
    'exe': GAME_EXE,
    # 交互方式候选列表：第一位是默认值；用户选过后会记在 configs/devices.json，
    # 改这里的顺序不会覆盖已保存的选择（需在 GUI 里切换或删除该文件）。
    # 本项目只做键盘操作，默认 PostMessage：走窗口消息，不抢焦点、不动物理鼠标。
    # 若客户端用 Raw Input 读键盘（部分整合包会这样），PostMessage 会静默失效，
    # 先用「按键自检」任务验证，再切 Genshin（SendInput 扫描码）或 Pynput。
    'interaction': ['PostMessage', 'Genshin', 'ForegroundPostMessage', 'Pynput', 'PyDirect'],
    # 截图方式，WGC 不支持时自动退回 BitBlt
    'capture_method': ['WGC', 'BitBlt_RenderFull', 'BitBlt'],
    'check_hdr': False,   # 检测到 AutoHDR 时提示，但不阻止运行
    'force_no_hdr': False,  # True = 检测到 AutoHDR 时禁止运行
    'require_bg': True,   # 要求后台截图，避免抢占前台
}

# 全局配置示例：与具体任务无关的按键映射
key_config_option = ConfigOption('Game Hotkey Config', {
    'Interact Key': 'f',
}, description='In Game Hotkey Config')

# 全局任务选项：所有任务共用的随机抖动，降低机械操作特征
options_config_option = ConfigOption('选项', {
    '点击随机区间': 0.3,
}, description='全局任务选项', show_at_tab=True)


def make_bottom_right_black(frame):
    """把截图右下角涂黑，用于遮挡 UID 等水印（可选截图处理器）。

    Args:
        frame: OpenCV 读取的单帧图像（NumPy 数组）。

    Returns:
        处理后的帧；出现异常时原样返回，保证识别流程不中断。
    """
    try:
        height, width = frame.shape[:2]
        black_width = int(0.13 * width)
        black_height = int(0.025 * height)
        start_x = width - black_width
        start_y = height - black_height
        frame[start_y:height, start_x:width] = 0
        return frame
    except Exception as e:
        print(f"Error processing frame: {e}")
        return frame


config = {
    'custom_tasks': True,  # 允许在 GUI 内创建、编辑自定义任务
    'debug': False,
    'gui': gui_config,
    'use_gui': True,
    'window_size': window_size,
    'config_folder': 'configs',  # 运行期配置目录，最好不要修改
    'global_configs': [key_config_option, options_config_option],
    # 'screenshot_processor': make_bottom_right_black,  # 需要遮挡 UID 时取消注释
    'gui_icon': 'icons/icon.png',
    'wait_until_before_delay': 0,
    'wait_until_check_delay': 0,
    'wait_until_settle_time': 0,  # 首次满足条件后二次确认，避开滑动动画中间帧

    'windows': WINDOWS_CONFIG,
    # 'adb': {  # 模拟器 / 安卓设备才需要，保留空字典会触发模拟器枚举并抢占默认设备
    #     'packages': ['com.example.game'],
    # },
    # 'browser': {  # 浏览器游戏才需要
    #     'url': 'https://example.com/game',
    #     'nick': 'Browser',
    #     'resolution': (1280, 720),
    # },
    'start_timeout': 120,
    'supported_resolution': {
        # 模板资产尚未固定，先关闭宽高比校验，避免 Minecraft 窗口客户区
        # （如 1920x1009）与 16:9 有偏差时每次启动都弹提示或被强制缩放。
        # 标注模板前请固定游戏窗口分辨率，再把 ratio 改回 '16:9'。
        'ratio': None,
        'min_size': (1280, 720),
        'resize_to': [],
    },
    'links': {},  # 关于页链接，按需补充 github / qq_group / faq 等
    'screenshots_folder': "screenshots",  # 每次启动会清空
    'gui_title': GAME_TITLE + ' · 助手',  # 工具窗口名；刻意与游戏窗口区分
    'template_matching': {  # 模板匹配（图像识别）参数
        'coco_feature_json': os.path.join('assets', 'coco_annotations.json'),
        'default_horizontal_variance': 0.002,
        'default_vertical_variance': 0.002,
        'default_threshold': 0.8,
    },
    'version': version,
    'my_app': ['src.globals', 'Globals'],  # 全局单例，可通过 og.my_app 访问

    # 用户手动触发的任务：新任务在此登记，模块路径 + 类名
    'onetime_tasks': [
        ["src.tasks.QRFarmTask", "QRFarmTask"],
        ["src.tasks.SkillLoopTask", "SkillLoopTask"],
        ["src.tasks.TemplateTask", "TemplateTask"],
        ["src.tasks.InputProbeTask", "InputProbeTask"],
    ],
    # 常驻触发器任务（每帧轮询 run），按需启用
    # 'trigger_tasks': [
    #     ["src.tasks.TemplateTriggerTask", "TemplateTriggerTask"],
    # ],
    # 自定义页面
    'custom_tabs': [
        ["src.ui.MyTab", "MyTab"],
    ],
}
