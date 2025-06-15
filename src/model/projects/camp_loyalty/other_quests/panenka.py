from web3 import Web3
import random
import asyncio
from loguru import logger
from faker import Faker

from src.model.help.cookies import CookieDatabase
from src.model.camp_network.constants import CampNetworkProtocol
from src.utils.decorators import retry_async


class Panenka:
    def __init__(self, instance: CampNetworkProtocol):
        self.camp_network = instance

        self.email_login: str | None = None
        self.email_password: str | None = None

    @retry_async(default_value=False)
    async def login(self) -> bool:
        try:
            if self.camp_network.email == "":
                logger.error(
                    f"{self.camp_network.account_index} | Panenka login error: Email not found"
                )
                return False

            self.email_login = self.camp_network.email.split(":")[0]
            self.email_password = self.camp_network.email.split(":")[1]

            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://panenkafc.gg",
                "priority": "u=1, i",
                "referer": "https://panenkafc.gg/",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            json_data = {
                "email": self.email_login,
                "password": self.email_password,
            }

            response = await self.camp_network.session.post(
                "https://prod-api.panenkafc.gg/api/v1/auth/login",
                headers=headers,
                json=json_data,
            )

            if not response.json()["success"]:
                if "Invalid email or password" in response.text:
                    # need to register
                    pass
                else:
                    logger.error(
                        f"{self.camp_network.account_index} | Panenka login error: {response.text}"
                    )
                    return False
            else:
                logger.success(
                    f"{self.camp_network.account_index} | Panenka login success"
                )
                return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Panenka login error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def _register_panenka(self) -> bool:
        try:
            fake = Faker()
            first_name = fake.first_name()
            last_name = fake.last_name()

            headers = {
                "accept": "application/json",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://panenkafc.gg",
                "priority": "u=1, i",
                "referer": "https://panenkafc.gg/",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            json_data = {
                "firstName": first_name,
                "lastName": last_name,
                "email": self.email_login,
                "password": self.email_password,
                "referralCode": None,
            }

            response = await self.camp_network.session.post(
                "https://prod-api.panenkafc.gg/api/v1/auth",
                headers=headers,
                json=json_data,
            )

            return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Panenka login error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise
