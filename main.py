from bootstrap import ensure_runtime

ensure_runtime(__file__)

import ok

from src.config import config
from src.log_cleanup import clean_old_logs

if __name__ == '__main__':
    clean_old_logs()
    ok = ok.OK(config)
    ok.start()
