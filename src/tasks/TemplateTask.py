from qfluentwidgets import FluentIcon

from src.options import random_interval
from src.tasks.base import MyBaseTask


class TemplateTask(MyBaseTask):
    """任务骨架模板，不含任何识别逻辑。

    复制本文件即可开始编写新任务，要点：
    1. ``self.name`` / ``self.description`` 是 GUI 中显示的标题与说明；
    2. ``self.default_config`` 定义任务级配置项，``self.config_description`` 写中文说明；
    3. ``run()`` 在独立线程中执行，用 ``self.sleep`` 代替 ``time.sleep`` 以便及时响应停止；
    4. 识别统一走 ``src.library`` 的特征注册表，不要在任务里硬编码模板路径。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例任务"
        self.description = "框架占位任务：未接入任何识别逻辑，仅演示任务结构与配置项。"
        self.icon = FluentIcon.SYNC
        self.default_config.update({
            "循环次数": 3,
            "循环间隔": 1.0,
        })
        self.config_description.update({
            "循环次数": "演示用的循环轮数，0 表示一直循环。",
            "循环间隔": "每轮之间的等待秒数，会叠加全局点击随机抖动。",
        })

    def run(self):
        total = max(0, int(self.config.get("循环次数", 3)))
        interval = float(self.config.get("循环间隔", 1.0))
        self.log_info("示例任务启动（框架占位，无识别逻辑）。")
        round_index = 0
        while total == 0 or round_index < total:
            round_index += 1
            self.log_debug("示例任务第 %d 轮" % round_index)
            self.info_set("当前轮次", round_index)
            self.sleep(random_interval(self, interval))
        self.log_info("示例任务结束。", notify=True)
