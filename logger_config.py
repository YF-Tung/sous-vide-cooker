# logger_config.py
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # 或改成 logging.INFO
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )