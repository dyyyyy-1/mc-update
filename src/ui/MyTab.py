from qfluentwidgets import BodyLabel, FluentIcon, PrimaryPushButton

from ok import Config
from ok.ui.qt.widget.CustomTab import CustomTab
from src.tasks.TemplateTask import TemplateTask


class MyTab(CustomTab):
    """自定义页面骨架（config['custom_tabs'] 注册）。

    可直接使用 PySide6 / qfluentwidgets 控件扩展界面，
    通过 ``self.get_task(任务类)`` 触发任务，或读写独立的配置文件。
    """

    def __init__(self):
        super().__init__()
        self.logger.info(f'MyTab init {self.__class__.__name__}')
        self.config = Config(self.__class__.__name__, {
            'config1': 0,
            'config2': "test_value",
        })
        self.icon = FluentIcon.FLAG

        self.label = BodyLabel("自定义页面占位，可在此扩展工具栏、状态看板等。")
        self.add_widget(self.label)

        self.button = PrimaryPushButton("运行示例任务")
        self.button.clicked.connect(self.button_clicked)
        self.add_widget(self.button)

    @property
    def name(self):
        return "自定义页面"

    def button_clicked(self):
        self.get_task(TemplateTask).run()
