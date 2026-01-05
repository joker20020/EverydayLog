# -*- UTF-8 -*-
# @author   : 40599
# @time     : 2026/1/5 20:45
# @version  : V1
import logging

# log init

logger = logging.getLogger("agent_logger")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

