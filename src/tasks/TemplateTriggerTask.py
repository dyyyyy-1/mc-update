from ok import TriggerTask


class TemplateTriggerTask(TriggerTask):
    """触发器骨架：run() 会被持续调用，适合「出现即处理」的常驻逻辑。

    注意：触发频率很高，run() 内不要放长耗时操作；
    先做轻量判断（例如单次 find_one），命中后再执行完整流程。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例触发器"
        self.description = "框架占位触发器：未接入识别逻辑。"
        self.trigger_count = 0

    def run(self):
        self.trigger_count += 1
        self.log_debug(f'TemplateTriggerTask run {self.trigger_count}')
