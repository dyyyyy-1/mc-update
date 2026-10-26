from qfluentwidgets import FluentIcon

from src.tasks.SkillLoopTask import SkillLoopTask


class QRFarmTask(SkillLoopTask):
    """斗士刷怪：Q、R 两个技能各 14 秒循环，Q 先于 R。

    与「技能循环」的关系：完全复用其循环内核，只把技能集合收窄为 Q/R 两键，
    效果等价于技能循环里开启 Q、R 且间隔都设为 14 秒，但配置项更少、不易误改。

    施放顺序：``skill_defs`` 按 Q → R 排列，两个技能同一时刻到期时，
    循环内核按该顺序依次按键，因此恒定先 Q 后 R。此顺序依赖技能集合的排列，
    调整顺序会改变先手技能，如非必要请勿改动。
    """

    skill_defs = (
        ("q", "Q", 14.0),
        ("r", "R", 14.0),
    )
    loop_label = "斗士QR刷怪"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "斗士QR刷怪"
        self.description = "斗士刷怪循环：Q、R 各 14 秒施放一次，同时到点时先 Q 后 R，循环执行。"
        self.icon = FluentIcon.GAME

        # 基类只默认开启 Q，本任务需要 Q、R 同时开启
        for _, label, interval in self.skill_defs:
            self.default_config[f"{label} 启用"] = True
            self.default_config[f"{label} 间隔(秒)"] = interval
