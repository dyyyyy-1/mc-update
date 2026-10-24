from PySide6.QtCore import QObject, QTimer

from ok import Logger
from src.log_cleanup import clean_old_logs

logger = Logger.get_logger(__name__)


class Globals(QObject):
    """全局单例（config['my_app'] 注册），用于存放跨任务共享状态。

    访问方式：``from ok import og`` 后使用 ``og.my_app``。
    如需跨任务共享识别模型、缓存或连接对象，在这里初始化并挂到实例上。
    """

    def __init__(self, exit_event):
        super().__init__()
        self.exit_event = exit_event
        try:
            self._cleanup_timer = QTimer(self)
            self._cleanup_timer.timeout.connect(self._clean_old_logs)
            self._cleanup_timer.start(24 * 60 * 60 * 1000)
        except Exception as e:
            logger.warning(f'log cleanup timer not started: {e}')

    def on_show_main_window(self, main_window):
        main_window.setWindowTitle('维亚之巅 起源 · 助手')

    def _clean_old_logs(self):
        clean_old_logs()
