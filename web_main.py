from bootstrap import ensure_runtime

ensure_runtime(__file__)

if __name__ == "__main__":
    from ok import OK
    from src.config import config

    config["gui"] = {
        "type": "web",
        "launch_mode": "pywebview",
    }
    ok = OK(config)
    ok.start()
