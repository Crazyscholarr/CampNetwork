from web3 import Web3
import random
import asyncio
from loguru import logger
from faker import Faker

from src.model.help.email_parser import AsyncEmailChecker
from src.model.help.cookies import CookieDatabase
from src.model.camp_network.constants import CampNetworkProtocol
from src.utils.decorators import retry_async


class Awana:
    def __init__(self, instance: CampNetworkProtocol):
        self.camp_network = instance

        self.email_login: str | None = None
        self.email_password: str | None = None

        self.awana_auth_token: str | None = None

    async def complete_quest(self) -> bool:
        try:
            is_logged_in = await self.login()
            if not is_logged_in:
                return False

            is_wallet_connected = await self.connect_wallet()
            if not is_wallet_connected:
                return False

            input("STOP")
            # submit wallet
            pass

        except Exception as e:
            logger.error(
                f"{self.camp_network.account_index} | Awana submit wallet error: {e}"
            )

    @retry_async(default_value=False)
    async def login(self) -> bool:
        try:
            if self.camp_network.email == "":
                logger.error(
                    f"{self.camp_network.account_index} | Awana login error: Email not found"
                )
                return False

            self.email_login = self.camp_network.email.split(":")[0]
            self.email_password = self.camp_network.email.split(":")[1]

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://tech.awana.world",
                "priority": "u=1, i",
                "referer": "https://tech.awana.world/login",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            json_data = {
                "email": self.email_login,
                "invitationCode": "",
            }

            response = await self.camp_network.session.post(
                "https://tech.awana.world/apis/user/sendWeb",
                headers=headers,
                json=json_data,
            )
            if response.status_code != 200 or response.json()["msg"] != "SUCCESS":
                logger.error(
                    f"{self.camp_network.account_index} | Awana login error: {response.text}"
                )
                return False

            logger.info(
                f"{self.camp_network.account_index} | Waiting 15 seconds for email code to be sent..."
            )
            await asyncio.sleep(15)
            # check email
            checker = AsyncEmailChecker(self.email_login, self.email_password)
            is_valid = await checker.check_if_email_valid()
            if not is_valid:
                logger.error(
                    f"{self.camp_network.account_index} | Awana login error: Email is invalid"
                )
                return False

            # get code
            code = await checker.check_email_for_verification_link(
                pattern=r'<div[^>]*class="[^"]*verification-code[^"]*"[^>]*>(\d{6})</div>',
                is_regex=True,
            )
            if not code:
                logger.error(
                    f"{self.camp_network.account_index} | Awana login error: Email code not found"
                )
                return False

            # Извлекаем только цифры из div
            code = "".join(filter(str.isdigit, code))

            logger.success(
                f"{self.camp_network.account_index} | Received Awana email code: {code}"
            )

            json_data = {
                "email": self.email_login,
                "code": code,
                "invitationCode": "",
            }

            response = await self.camp_network.session.post(
                "https://tech.awana.world/apis/user/loginWeb",
                headers=headers,
                json=json_data,
            )

            if response.status_code != 200 or response.json()["msg"] != "SUCCESS":
                logger.error(
                    f"{self.camp_network.account_index} | Awana login error: email code is invalid"
                )
                return False

            self.awana_auth_token = response.json()["data"]["token"]

            logger.success(f"{self.camp_network.account_index} | Awana login success")
            return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Awana login error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def connect_wallet(self) -> bool:
        try:
            
            logger.success(
                f"{self.camp_network.account_index} | Awana wallet connected!"
            )
            return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Awana connect wallet error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise
