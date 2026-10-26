# 维亚之巅 起源 · ok-script 框架

基于 ok-script 2.0.0b7 的自动化脚本，目标窗口按名称识别为 **《维亚之巅 起源》**（Minecraft Java 版）。
当前包含技能循环、斗士QR刷怪两个任务，图像识别资源仍需按需标注。

## 下载与更新

- **首次安装**：在 [Releases](https://github.com/dyyyyy-1/mc-/releases) 下载 `mc-auto-win32-Global-setup.exe` 安装，安装包自带 Python 运行时，无需自行配置环境。
- **版本更新**：启动后在「关于」页点击检查更新，从独立更新库 `dyyyyy-1/mc-update` 拉取变更文件并重启生效。
- **数据保留**：`configs/`、`logs/`、`screenshots/` 不参与更新，升级不会覆盖本地配置。

## 许可证

本项目采用 **AGPL-3.0**，完整许可见 [LICENSE](LICENSE)。

- 源码地址：https://github.com/dyyyyy-1/mc-
- 本项目基于 [ok-script](https://github.com/ok-oldking/ok-script)（AGPL-3.0）构建，发行包内含其代码，遵循同一许可证。

## 环境与启动

要求 Python 3.12（ok-script 限制 `>=3.12,<3.13`）。**不要用系统的 3.13 / 3.14 直接运行**，
依赖只装在项目 `.venv` 中。

```bat
setup.bat        :: 首次：创建 .venv 并安装依赖
run.bat          :: 正常启动
run_debug.bat    :: 调试模式：保留调试截图，便于标注模板
```

命令行等价写法：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt --no-deps
.venv/Scripts/python.exe main.py
```

`main.py` 会先经过 `bootstrap.py` 校验：解释器版本不符或缺少 `ok` 时，自动用
`.venv/Scripts/python.exe` 重新执行同一入口，因此误用系统解释器也不会报
`ModuleNotFoundError`。若 `.venv` 不存在，会给出明确提示而非堆栈。

VS Code 中请把解释器切到 `.venv\Scripts\python.exe`（Ctrl+Shift+P → Python: Select Interpreter），
避免编辑器终端继续使用全局 3.14。

## 目录结构

| 路径 | 作用 |
| --- | --- |
| `main.py` / `main_debug.py` | 启动入口，调试入口仅额外开启 `debug` |
| `web_main.py` | Web 界面入口，配合 `requirements-web.txt` |
| `src/config.py` | 全部应用配置：窗口识别、分辨率、任务登记、模板匹配参数 |
| `src/globals.py` | 全局单例 `og.my_app`，承载跨任务共享状态 |
| `src/library.py` | 特征注册表 `FEATURES` 与 `find_one` / `wait_click` 封装（当前为空） |
| `src/flow.py` | 通用流程控制：`click_until_next`、`drive_until_next_screen` |
| `src/options.py` | 全局选项读取与点击随机抖动 |
| `src/log_cleanup.py` | 启动时清理超过 3 天的日志 |
| `src/tasks/base.py` | 任务基类 `MyBaseTask`，所有任务继承它 |
| `src/tasks/TemplateTask.py` | 任务骨架模板，无识别逻辑 |
| `src/tasks/TemplateTriggerTask.py` | 触发器骨架模板，默认未登记 |
| `src/ui/MyTab.py` | 自定义页面骨架，已登记到 `custom_tabs` |
| `assets/coco_annotations.json` | 模板标注（COCO 格式），当前为空 |
| `configs/` | 运行期生成的配置与设备记录，不入库 |

## 窗口识别

目标游戏是 **Minecraft（Java 版）**，其窗口标题以「维亚之巅」开头，进程为 `java.exe`。
`src/config.py` 中：

```python
GAME_WINDOW_TITLE = re.compile(r'^维亚之巅')
GAME_EXE = ['java.exe', 'javaw.exe']
```

关键点：**仅凭标题会抓错窗口**。工具自身窗口标题同样含「维亚之巅」，系统里会同时存在
`java.exe`（游戏）与 `python.exe`（本工具）两个同名窗口。因此必须同时限定进程名，
且工具窗口名已改为「维亚之巅 起源 · 助手」以示区分。

- `windows.title` 传字符串时是完全相等匹配，传正则时走 `re.search`；
  这里用 `^维亚之巅` 前缀匹配，兼容标题带版本号等后缀。
- 若同机开启多个 Minecraft 实例，可再加 `'hwnd_class': 'LWJGL'` 或改用更严格的标题。
- 按窗口标题识别时**不会自动启动游戏**，需先打开游戏再启动工具。

## 输入方式（纯键盘场景）

`interaction` 是**候选列表而非回退链**：只有第一项作为默认值，用户选过的项会记在
`configs/devices.json`，之后改顺序不会覆盖。当前默认 `PostMessage`。

| 方式 | 机制 | 抢焦点 | 动物理鼠标 | 说明 |
| --- | --- | --- | --- | --- |
| `PostMessage` | `WM_KEYDOWN` 窗口消息 | 否 | 否 | 真后台；被 Raw Input 客户端忽略时会静默失效 |
| `Genshin` | `SendInput` + 扫描码 | 是 | 否 | 比 Pynput 更底层，游戏更容易接受 |
| `ForegroundPostMessage` | 置前 + 窗口消息 | 是 | 否 | 需管理员权限 |
| `Pynput` / `PyDirect` | 系统级真实输入 | 是 | 是 | 最通用，但会夺走鼠标 |

纯键盘任务优先 `PostMessage`。它不移动光标、不切换前台窗口，代价是
**可能静默失效**——所以先用「按键自检」任务验证，再决定是否继续：

1. 进入游戏内一个界面变化明显的场景（如站立不动）；
2. 运行「按键自检」，默认按 `F3`（调试信息）；
3. 日志给出「基线抖动 / 最大差异 / 判定线」，据此判断当前通道是否生效。

Minecraft 有三个具体约束：

- **Raw Input**：部分整合包/客户端用 Raw Input 读键盘，窗口消息收不到。此时切 `Genshin`。
- **50ms 刻采样**：游戏每刻（50ms）轮询一次按键状态，`down_time` 低于约 0.1 秒的
  按下-抬起可能落在同一刻内被丢弃。移动类操作请用
  `send_key_down` → `sleep` → `send_key_up`，不要用短按。
- **单人模式失焦暂停**：Java 版单人存档在窗口失焦时会暂停世界（`pauseOnLostFocus`），
  纯后台方案会卡住；多人服务器不受影响。单人场景应改用会置前的方式。

框架之外的替代方案：客户端 mod（直接调用按键映射，最稳但需开发）、
服务端 RCON/插件（完全脱离客户端输入）、Interception 驱动（可后台注入且被 Raw Input 接受，
但需装内核驱动，成本与风险都高）。

## 已实现任务

### 技能循环（`src/tasks/SkillLoopTask.py`）

Q/R/F/G 四个技能各自独立开关与独立间隔，到点施放，循环执行。

| 配置项 | 默认 | 说明 |
| --- | --- | --- |
| `Q/R/F/G 启用` | 仅 Q 开启 | 每个技能单独开关 |
| `Q/R/F/G 间隔(秒)` | 3 / 5 / 8 / 12 | 各自计时，互不影响，下限 0.2 秒 |
| `按键按下时长` | 0.15 | 低于 0.1 秒可能被 50ms 刻采样丢弃 |
| `启动后延迟` | 1.0 | 留出切到游戏窗口的时间 |

计时不叠加全局点击随机抖动，避免技能节奏漂移；单次施放落后超过一个间隔时不补按，
直接对齐到下一轮，防止连发。

### 斗士QR刷怪（`src/tasks/QRFarmTask.py`）

斗士刷怪专用：Q、R 两个技能各按 14 秒循环施放，等价于技能循环里只开启 Q 和 R
且两者间隔都设为 14 秒，但独立配置、只暴露这两个键，避免误改到 F/G。

| 配置项 | 默认 | 说明 |
| --- | --- | --- |
| `Q 启用` / `Q 间隔(秒)` | 开启 / 14 | Q 的开关与间隔 |
| `R 启用` / `R 间隔(秒)` | 开启 / 14 | R 的开关与间隔 |
| `按键按下时长` | 0.15 | 低于 0.1 秒可能被 50ms 刻采样丢弃 |
| `启动后延迟` | 1.0 | 留出切到游戏窗口的时间 |

复用 `SkillLoopTask` 的循环内核，仅通过覆盖 `skill_defs` 收窄技能集合。
施放顺序由 `skill_defs` 的排列决定：Q 在前，因此两者同时到期时恒定先 Q 后 R，
Q 领先时长即按键按下时长（默认 0.15 秒）。

## 扩展方式

### 1. 新增识别特征

1. `main_debug.py` 启动，抓取目标界面截图；
2. 标注目标区域，类别名即特征 key（如 `main_menu`）；
3. 导出 COCO 格式覆盖 `assets/coco_annotations.json`；
4. 在 `src/library.py` 的 `FEATURES` 登记同名条目（阈值、超时、点击偏移）。

任务中统一通过 `find_one(task, key)` / `wait_click(task, key)` 调用，不直接写模板路径。

### 2. 新增任务

复制 `src/tasks/TemplateTask.py`，改名后登记到 `src/config.py` 的 `onetime_tasks`：

```python
'onetime_tasks': [
    ["src.tasks.YourTask", "YourTask"],
],
```

常驻轮询型任务改为继承 `TriggerTask`，登记到 `trigger_tasks`。

### 3. 新增页面

在 `src/ui/` 下继承 `ok.ui.qt.widget.CustomTab`，登记到 `custom_tabs`。

## 与旧项目的关系

本框架沿用 ok-DNA-me 的分层模式（config / globals / library / flow / tasks / ui），
但**未包含**任何具体任务实现、特征注册项、模板图片与运行期配置，
`configs/`、`logs/`、`screenshots/` 均在首次运行时自动生成。
