from bootstrap import ensure_runtime

ensure_runtime(__file__)

import ok

from src.config import config

if __name__ == '__main__':
    # debug 模式：保留调试截图、输出更详细的识别日志，用于早期标注模板
    config = config
    config['debug'] = True
    ok = ok.OK(config)
    ok.start()
