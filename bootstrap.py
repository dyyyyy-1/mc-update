"""运行时引导：保证脚本用项目内的 Python 3.12 虚拟环境执行。

背景
----
ok-script 要求 Python ``>=3.12,<3.13``，且依赖只安装在项目 ``.venv`` 中。
若直接用系统的 3.13/3.14 或未装依赖的解释器运行 ``main.py``，
会得到 ``ModuleNotFoundError: No module named 'ok'``。

本模块在 import ok 之前调用：条件不满足时用 ``.venv/Scripts/python.exe``
重新执行同一入口，并透传命令行参数与返回码。

注意：Windows 上 ``os.execv`` 会启动新进程后让当前进程立即以 0 退出，
终端表现为「命令秒退、GUI 游离」，因此这里使用 ``subprocess`` 等待子进程，
保证 Ctrl+C、退出码与终端行为一致。
"""

import importlib.util
import os
import subprocess
import sys

REQUIRED_PYTHON = (3, 12)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VENV_ROOT = os.path.join(PROJECT_ROOT, ".venv")
VENV_PYTHON = os.path.join(VENV_ROOT, "Scripts", "python.exe")


def _same_path(left, right):
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def _in_project_venv():
    return _same_path(sys.prefix, VENV_ROOT)


def _compatible_interpreter():
    return sys.version_info[:2] == REQUIRED_PYTHON and importlib.util.find_spec("ok") is not None


def ensure_runtime(script_path):
    """在当前进程不满足运行条件时切换到项目 venv，无法切换则给出明确提示。"""
    if _in_project_venv() or _compatible_interpreter():
        return

    if os.path.isfile(VENV_PYTHON):
        sys.stdout.write(
            "检测到当前解释器 %s (Python %s) 不满足运行条件，已切换到项目虚拟环境。\n"
            % (sys.executable, ".".join(str(part) for part in sys.version_info[:3]))
        )
        sys.stdout.flush()
        result = subprocess.run([VENV_PYTHON, os.path.abspath(script_path)] + sys.argv[1:])
        raise SystemExit(result.returncode)

    raise SystemExit(
        "未找到可用的运行环境：\n"
        "  当前解释器: %s (Python %s)\n"
        "  需要的环境: Python 3.12 + ok-script，位于 %s\n"
        "请先执行 setup.bat 安装依赖，或用以下命令启动：\n"
        "  %s main.py\n"
        % (
            sys.executable,
            ".".join(str(part) for part in sys.version_info[:3]),
            VENV_PYTHON,
            VENV_PYTHON,
        )
    )
