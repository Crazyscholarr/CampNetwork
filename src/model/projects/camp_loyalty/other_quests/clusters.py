from web3 import Web3
import random
import asyncio
from loguru import logger
from faker import Faker
from datetime import datetime, timezone

from src.model.help.captcha import Capsolver, Solvium, TwoCaptchaEnterprise
from src.model.help.cookies import CookieDatabase
from src.model.camp_network.constants import CampNetworkProtocol
from src.utils.decorators import retry_async


class Clusters:
    def __init__(self, instance: CampNetworkProtocol):
        self.camp_network = instance

    def _generate_random_name(self) -> str:
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        digits = "0123456789"

        # Randomly decide if we'll use all caps or all lowercase
        use_caps = random.choice([True, False])

        # Generate base name (8-12 characters)
        name_length = random.randint(8, 14)
        name = []

        # Track consecutive vowels and consonants
        consecutive_vowels = 0
        consecutive_consonants = 0

        for i in range(name_length):
            if consecutive_vowels >= 2:
                # Must add consonant
                char = random.choice(consonants)
                consecutive_vowels = 0
                consecutive_consonants = 1
            elif consecutive_consonants >= 2:
                # Must add vowel
                char = random.choice(vowels)
                consecutive_consonants = 0
                consecutive_vowels = 1
            else:
                # Can add either
                if random.random() < 0.5:
                    char = random.choice(vowels)
                    consecutive_vowels += 1
                    consecutive_consonants = 0
                else:
                    char = random.choice(consonants)
                    consecutive_consonants += 1
                    consecutive_vowels = 0

            name.append(char)

        # Convert to caps or lowercase based on random choice
        name = "".join(name)
        if use_caps:
            name = name.upper()

        # Randomly decide if first letter should be capitalized
        if random.choice([True, False]):
            name = name.capitalize()

        # Add 1-3 random digits at the end
        num_digits = random.randint(1, 3)
        name += "".join(random.choices(digits, k=num_digits))

        return name

    @retry_async(default_value=False)
    async def claim_clusters(self) -> bool:
        try:
            auth_token = await self._login()
            if auth_token is None:
                raise Exception("Clusters login error")

            cluster_name = None
            for _ in range(10):
                cluster_name = self._generate_random_name()
                is_available = await self._check_if_available(cluster_name)
                if is_available:
                    break

            if cluster_name is None:
                logger.error(
                    f"{self.camp_network.account_index} | Unable to generate cluster name."
                )
                return False

            # TODO: Add captcha key
            solvium = Solvium(
                api_key=self.camp_network.config.CAPTCHA.SOLVIUM_API_KEY,
                session=self.camp_network.session,
                proxy=self.camp_network.proxy,
            )

            # For enterprise reCAPTCHA v3
            captcha_token = await solvium.solve_recaptcha_v3(
                sitekey="6Lf7zhkrAAAAAL9QP8CptZhGtgOp-lA5Oi3VGlu5",
                pageurl="https://clusters.xyz",
                action="SIGNUP",
                enterprise=True,
            )
            # capsolver = Capsolver(
            #     api_key="CAP-X",
            #     proxy=self.camp_network.proxy,
            #     session=self.camp_network.session,
            # )
            # captcha_token = await capsolver.solve_recaptcha(
            #     sitekey="6Lf7zhkrAAAAAL9QP8CptZhGtgOp-lA5Oi3VGlu5",
            #     pageurl="https://clusters.xyz",
            #     page_action="SIGNUP",
            #     enterprise=True,
            # )
            if captcha_token is None:
                raise Exception("Unable to solve captcha")

            logger.success(
                f"{self.camp_network.account_index} | Captcha for Clusters solved successfully!"
            )

            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "authorization": f"Bearer {auth_token}",
                "content-type": "application/json",
                "origin": "https://clusters.xyz",
                "priority": "u=1, i",
                "referer": "https://clusters.xyz/",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "x-testnet": "false",
            }

            json_data = {
                "clusterName": "campnetwork",
                "walletName": cluster_name,
                "recaptchaToken": {
                    "type": "invisible",
                    "token": captcha_token,
                },
            }

            response = await self.camp_network.session.post(
                "https://api.clusters.xyz/v1/trpc/names.community.register",
                headers=headers,
                json=json_data,
            )

            if response.status_code != 200:
                raise Exception(f"Clusters claim error: {response.text}")

            if (
                response.json()["result"]["data"]["clusterName"]
                == f"campnetwork/{cluster_name}"
            ):
                logger.success(
                    f"{self.camp_network.account_index} | Clusters claimed successfully!"
                )
                return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Clusters claim error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def _check_if_available(self, cluster_name: str) -> bool:
        try:
            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://clusters.xyz",
                "priority": "u=1, i",
                "referer": "https://clusters.xyz/",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "x-testnet": "false",
            }

            params = {
                "input": '{"clusterName":"campnetwork","name":"' + cluster_name + '"}',
            }

            response = await self.camp_network.session.get(
                "https://api.clusters.xyz/v1/trpc/names.community.isAvailable",
                params=params,
                headers=headers,
            )

            if response.status_code != 200:
                raise Exception(f"Clusters check error: {response.text}")

            if response.json()["result"]["data"]["isAvailable"]:
                return True
            else:
                return False

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Clusters check error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def _login(self) -> str:
        try:
            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://clusters.xyz",
                "priority": "u=1, i",
                "referer": "https://clusters.xyz/",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "x-testnet": "false",
            }

            signing_date = (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )

            message = (
                f"clusters.xyz verification\n\n"
                "Before interacting with certain functionality, we require a wallet signature for verification.\n\n"
                f"{signing_date}"
            )
            signature = "0x" + self.camp_network.web3.get_signature(
                message, self.camp_network.wallet
            )

            params = {
                "input": '{"signature":"'
                + signature
                + '","signingDate":"'
                + signing_date
                + '","type":"evm","wallet":"'
                + self.camp_network.wallet.address
                + '"}',
            }

            response = await self.camp_network.session.get(
                "https://api.clusters.xyz/v1/trpc/auth.getToken",
                params=params,
                headers=headers,
            )

            if response.status_code != 200:
                raise Exception(f"Clusters login error: {response.text}")

            auth_token = response.json()["result"]["data"]["token"]
            return auth_token

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Clusters login error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise
