import base64
from web3 import Web3
import random
import asyncio
from loguru import logger
from datetime import datetime, timezone
import aiohttp

from src.model.projects.camp_loyalty.quests import LoyaltyQuests
from src.model.projects.camp_loyalty.connect_socials import ConnectLoyaltySocials
from src.model.help.captcha import Solvium
from src.model.help.cookies import CookieDatabase
from src.model.camp_network.constants import CampNetworkProtocol
from src.utils.decorators import retry_async


class CampLoyalty:
    def __init__(self, instance: CampNetworkProtocol):
        self.camp_network = instance

        self.cf_clearance = None
        self.cookie_db = CookieDatabase()

        self.login_session_token: str | None = None
        self.login_csrf_token: str | None = None
        self.user_info: dict | None = None

    async def execute_quest(self, task: str) -> bool:
        task = task.lower()
        logger.info(
            f"{self.camp_network.account_index} | Executing Loyalty Quest: {task}"
        )
        self.complete_quests_service = LoyaltyQuests(self)
        return await self.complete_quests_service.complete_quest(task)

    @retry_async(default_value=False)
    async def login(self) -> bool:
        try:
            # First check if we have a valid cookie in the database
            await self.cookie_db.init_db()
            self.cf_clearance = await self.cookie_db.get_valid_cookie(
                self.camp_network.private_key
            )

            if self.cf_clearance:
                logger.success(
                    f"{self.camp_network.account_index} | Using existing Cloudflare cookie from database"
                )
            else:
                headers = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                    "cache-control": "max-age=0",
                    "priority": "u=0, i",
                    "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="24"',
                    "sec-ch-ua-arch": '"x86"',
                    "sec-ch-ua-bitness": '"64"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-model": '""',
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-ch-ua-platform-version": '"19.0.0"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "same-origin",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                }

                response = await self.camp_network.session.get(
                    "https://loyalty.campnetwork.xyz/loyalty", headers=headers
                )

                if "Just a moment" in response.text:
                    logger.info(
                        f"{self.camp_network.account_index} | Cloudflare challenge detected. Solving..."
                    )

                    # for x in range(10):
                    #     ok = await self._check_proxy(self.camp_network.proxy)
                    #     if not ok:
                    #         logger.info(
                    #             f"{self.camp_network.account_index} | Proxy is too slow. Retrying... {x+1}/{10}"
                    #         )
                    #         await asyncio.sleep(5)
                    #     else:
                    #         break

                    #     if x == 9:
                    #         raise Exception(
                    #             "Your proxies is too slow. It should response in 5 seconds to solve Cloudflare challenge"
                    #         )

                    solvium = Solvium(
                        api_key=self.camp_network.config.CAPTCHA.SOLVIUM_API_KEY,
                        session=self.camp_network.session,
                        proxy=self.camp_network.proxy,
                    )
                    cf_clearance = await solvium.solve_cf_clearance(
                        pageurl="https://loyalty.campnetwork.xyz/loyalty",
                        body_b64=base64.b64encode(response.content).decode(),
                        proxy=self.camp_network.proxy,
                    )
                    if cf_clearance:
                        logger.success(
                            f"{self.camp_network.account_index} | Cloudflare challenge solved"
                        )
                        self.cf_clearance = cf_clearance

                        # Save the cookie to the database with default expiration (1 hour)
                        await self.cookie_db.save_cookie(
                            self.camp_network.private_key, self.cf_clearance
                        )
                    else:
                        raise Exception("Failed to solve Cloudflare challenge")

            current_time = (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )
            nonce = await self._get_nonce()
            if nonce is None:
                raise Exception("Failed to get nonce")

            self.login_csrf_token = nonce

            message_to_sign = (
                "loyalty.campnetwork.xyz wants you to sign in with your Ethereum account:\n"
                f"{self.camp_network.wallet.address}\n\n"
                "Sign in to the app. Powered by Snag Solutions.\n\n"
                "URI: https://loyalty.campnetwork.xyz\n"
                "Version: 1\n"
                f"Chain ID: 123420001114\n"
                f"Nonce: {nonce}\n"
                f"Issued At: {current_time}"
            )

            signature = self.camp_network.web3.get_signature(
                message_to_sign, self.camp_network.wallet
            )

            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://loyalty.campnetwork.xyz",
                "priority": "u=1, i",
                "referer": "https://loyalty.campnetwork.xyz/loyalty",
                "sec-ch-ua": '"Chromium";v="135", "Google Chrome";v="135", "Not.A/Brand";v="99"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"19.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            data = {
                "message": '{"domain":"loyalty.campnetwork.xyz","address":"'
                + self.camp_network.wallet.address
                + '","statement":"Sign in to the app. Powered by Snag Solutions.","uri":"https://loyalty.campnetwork.xyz","version":"1","chainId":123420001114,"nonce":"'
                + nonce
                + '","issuedAt":"'
                + current_time
                + '"}',
                "accessToken": "0x" + signature,
                "signature": "0x" + signature,
                "walletConnectorName": "Rabby Wallet",
                "walletAddress": self.camp_network.wallet.address,
                "redirect": "false",
                "callbackUrl": "/protected",
                "chainType": "evm",
                "csrfToken": nonce,
                "json": "true",
            }

            response = await self.camp_network.session.post(
                "https://loyalty.campnetwork.xyz/api/auth/callback/credentials",
                headers=headers,
                data=data,
                cookies={"cf_clearance": self.cf_clearance},
            )

            cookies = response.cookies
            self.login_session_token = cookies.get("__Secure-next-auth.session-token")

            if self.login_session_token:
                logger.success(
                    f"{self.camp_network.account_index} | Login to Loyalty is successful!"
                )

                self.user_info = await self.get_user_info()

                return True
            else:
                raise Exception("Failed to login to Loyalty")

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Login to Loyalty error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def _get_nonce(self) -> str:
        try:
            headers = {
                "accept": "*/*",
                "content-type": "application/json",
                "referer": "https://loyalty.campnetwork.xyz/loyalty",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            response = await self.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/auth/csrf",
                headers=headers,
                cookies={"cf_clearance": self.cf_clearance},
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get nonce: {response.status_code}")

            return response.json()["csrfToken"]

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Get Loyalty nonce error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def get_user_info(self) -> dict:
        """Get user info from Loyalty
        Exampple:
        {
            "data": [
                {
                    "id": "asdfasdfasdfasdf",
                    "temporaryLoyaltyUser": false,
                    "isSnagSuperAdmin": false,
                    "walletAddress": "0xasdkjfal;ksjdfasdfasd",
                    "walletType": "evm",
                    "stardustProfileId": null,
                    "privyUserId": null,
                    "notifications": null,
                    "delegationsFrom": [],
                    "userMetadata": [
                        {
                            "emailAddress": null,
                            "emailVerifiedAt": null,
                            "discordUser": null,
                            "discordVerifiedAt": null,
                            "twitterUser": null,
                            "twitterVerifiedAt": null,
                            "instagramUser": null,
                            "instagramVerifiedAt": null,
                            "logoUrl": null,
                            "displayName": null,
                            "location": null,
                            "bio": null,
                            "portfolioUrl": null,
                            "meta": null,
                            "walletGroupIdentifier": null,
                            "twitterUserFollowersCount": 1,
                            "telegramUserId": null,
                            "telegramVerifiedAt": null,
                            "telegramUsername": null,
                            "isBlocked": false,
                            "steamUserId": null,
                            "steamUsername": null,
                            "epicUsername": null,
                            "epicAccountIdentifier": null,
                            "userGroupId": null,
                            "externalLoyaltyScore": null,
                            "userGroup": null,
                            "externalIdentifier": null,
                            "YTChannelId": null,
                            "googleUserId": null,
                            "googleUser": null
                        }
                    ]
                }
            ],
            "hasNextPage": false
        }
        """
        try:
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=1, i",
                "referer": "https://loyalty.campnetwork.xyz/loyalty",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            params = {
                "walletAddress": self.camp_network.wallet.address,
                "includeDelegation": "false",
                "websiteId": "32afc5c9-f0fb-4938-9572-775dee0b4a2b",
                "organizationId": "26a1764f-5637-425e-89fa-2f3fb86e758c",
            }

            response = await self.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/users",
                params=params,
                cookies={"cf_clearance": self.cf_clearance},
                headers=headers,
            )
            await self.update_session_token(response.cookies)
            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.status_code}")

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Get Loyalty user info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def get_account_info(self) -> dict:
        """Get user info from Loyalty
        Exampple:
        {
            "data": [
                {
                    "id": "1234123rdfasdf",
                    "userId": "23ewfdasedfasdfasdf",
                    "loyaltyCurrencyId": "asdfawfeq23fdwaef0",
                    "amount": "7",
                    "lockVersion": "7",
                    "organizationId": "2asdfasdfasdcasdcc",
                    "websiteId": "3asdfasdcasdcasdcasdcb",
                    "createdAt": "asdfasdcasdc1Z",
                    "updatedAt": "asdcasdcasdc.828Z",
                    "loyaltyAccountGroupId": null,
                    "user": {
                        "id": "aasdcasdcasdca",
                        "walletAddress": "0xasdfasdcasdcasdcasdcf",
                        "userMetadata": [
                            {
                                "walletGroupIdentifier": null,
                                "userGroupId": null,
                                "userGroup": null,
                                "twitterUser": null,
                                "discordUser": null,
                                "telegramUsername": null,
                                "logoUrl": null,
                                "displayName": null,
                                "externalIdentifier": null,
                                "externalLoyaltyScore": null
                            }
                        ]
                    }
                }
            ],
            "hasNextPage": false
        }
        """
        try:

            headers = {
                "accept": "*/*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=1, i",
                "referer": "https://loyalty.campnetwork.xyz/loyalty",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            params = {
                "limit": "1000",
                "websiteId": "32afc5c9-f0fb-4938-9572-775dee0b4a2b",
                "organizationId": "26a1764f-5637-425e-89fa-2f3fb86e758c",
                "walletAddress": self.camp_network.wallet.address,
            }

            response = await self.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/loyalty/accounts",
                params=params,
                cookies={"cf_clearance": self.cf_clearance},
                headers=headers,
            )

            await self.update_session_token(response.cookies)

            if response.status_code != 200:
                raise Exception(f"Failed to get account info: {response.status_code}")

            return response.json()

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | Get Loyalty account info error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    async def update_session_token(self, response_cookies: dict):
        for cookie_name, cookie_value in response_cookies.items():
            if cookie_name == "__Secure-next-auth.session-token":
                self.login_session_token = cookie_value

    async def connect_socials(self):
        self.connect_socials_service = ConnectLoyaltySocials(self)
        return await self.connect_socials_service.connect_socials()

    async def set_display_name(self):
        self.set_display_name_service = ConnectLoyaltySocials(self)
        return await self.set_display_name_service.set_display_name()

    async def set_email(self):
        if self.camp_network.email is None:
            logger.error(
                f"{self.camp_network.account_index} | Email is not set. Please set email in data/emails.txt"
            )
            return False

        self.set_email_service = ConnectLoyaltySocials(self)
        return await self.set_email_service.set_email()

    async def set_email(self):
        self.set_email_verification_service = ConnectLoyaltySocials(self)
        return await self.set_email_verification_service.set_email()

    async def complete_quests(self, task: str = None):
        self.complete_quests_service = LoyaltyQuests(self)
        return await self.complete_quests_service.complete_quests(task)

    async def _check_proxy(self, proxy: str):
        success = True
        async with aiohttp.ClientSession() as session:
            try:
                # Parse proxy string in format user:pass@ip:port
                if "@" in proxy:
                    auth, server = proxy.split("@")
                    username, password = auth.split(":")
                    proxy_auth = aiohttp.BasicAuth(username, password)
                    proxy_url = f"http://{server}"
                else:
                    proxy_url = f"http://{proxy}"
                    proxy_auth = None

                async with await session.get(
                    "http://example.com",
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status != 200:
                        success = False
            except aiohttp.ClientProxyConnectionError:
                success = False
            except aiohttp.ConnectionTimeoutError:
                success = False
            except Exception:
                success = False
        return success
