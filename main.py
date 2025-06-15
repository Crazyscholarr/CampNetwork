from loguru import logger
import urllib3
import sys
import asyncio
import platform
import logging

from process import start
from src.utils.output import show_logo, show_dev_info
from src.utils.check_github_version import check_version


VERSION = "1.0.0"


if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    show_logo()
    show_dev_info()

    # You can pass a proxy string in format "user:pass@ip:port" if needed
    await check_version(VERSION, proxy="")

    configuration()
    await start()


log_format = (
    "<cyan>[{time:HH:mm:ss|DD-MM-YYYY}]</cyan> "
    "<magenta>[Crazyscholar @ CampNetwork]</magenta> "
    "<level>[{level}]</level> | "
    "<blue>Account</blue> - "
    "<level>{message}</level>"
)


def configuration():
    urllib3.disable_warnings()
    logger.remove()

    # Tắt log của primp và web3
    logging.getLogger("primp").setLevel(logging.WARNING)
    logging.getLogger("web3").setLevel(logging.WARNING)

    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format,
        level="INFO"
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 month",
        format="[ {time:HH:mm:ss | DD-MM-YYYY} ] [ Crazyscholar @ CampNetwork ] [ {level} ] |Account - {message}",
        level="INFO"
    )

if __name__ == "__main__":
    asyncio.run(main())
