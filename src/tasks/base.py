from ok import BaseTask


class MyBaseTask(BaseTask):
    """本项目所有任务的基类。

    统一在这里挂公共能力（日志前缀、通用配置项、异常兜底等），
    具体任务继承本类，而不是直接继承 ``BaseTask``。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
