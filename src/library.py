"""特征（模板）注册表。

框架说明
--------
这里的字典是「图像识别特征」的统一入口，当前为空，需要按项目自行填充。
每条特征的 key 必须与 ``assets/coco_annotations.json`` 中的类别名（category name）
完全一致，框架才能完成模板切图与匹配。

新增一条特征的步骤：
1. 以 debug 模式运行 ``main_debug.py``，在 GUI 的模板/截图页抓取目标界面；
2. 用标注工具画出目标区域，类别名填 feature key（例如 ``main_menu``）；
3. 导出 Label Studio / X-AnyLabeling 格式，生成 ``assets/coco_annotations.json``；
4. 在下方 ``FEATURES`` 中登记同名字段（阈值、超时、点击偏移等）。

示例::

    FEATURES = {
        "main_menu": {
            "name_zh": "主界面",
            "description": "进入游戏后的主界面标识",
            "threshold": 0.8,
            "time_out": 10,
            "click": (0.5, 0.5),
            "click_delay": 0.5,
        },
    }
"""

FEATURES = {}


def get_feature(name):
    return FEATURES.get(name) or {}


def find_one(task, name, **kwargs):
    """按特征名查找单个目标，阈值默认取注册表中的配置。"""
    meta = get_feature(name)
    threshold = kwargs.pop("threshold", meta.get("threshold", 0.8))
    return task.find_one(name, threshold=threshold, **kwargs)


def wait_click(task, name, time_out=None, **kwargs):
    """等待特征出现并点击，超时返回 False 而不抛异常。"""
    meta = get_feature(name)
    threshold = kwargs.pop("threshold", meta.get("threshold", 0.8))
    if time_out is None:
        time_out = meta.get("time_out", 10)
    click_delay = kwargs.pop("click_delay", meta.get("click_delay", 0.0))
    return task.wait_click_feature(
        name,
        threshold=threshold,
        time_out=time_out,
        raise_if_not_found=False,
        click_after_delay=click_delay,
        **kwargs
    )
