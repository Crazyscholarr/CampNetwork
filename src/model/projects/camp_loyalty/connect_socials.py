import random
import asyncio
import secrets
from loguru import logger

from src.model.projects.camp_loyalty.constants import CampLoyaltyProtocol
from src.utils.decorators import retry_async


class ConnectLoyaltySocials:
    def __init__(self, camp_loyalty_instance: CampLoyaltyProtocol):
        self.camp_loyalty = camp_loyalty_instance

    async def connect_socials(self):
        try:
            success = True
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Starting connect socials..."
            )

            account_info = await self.camp_loyalty.get_user_info()
            if account_info is None:
                raise Exception("Account info is None")

            if account_info["data"][0]["userMetadata"][0]["twitterUser"] is None:
                if not self.camp_loyalty.camp_network.twitter_token:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Twitter token is None. Please add token to data/twitter_tokens.txt"
                    )
                else:
                    if not await self.connect_twitter():
                        success = False
            else:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Twitter already connected"
                )

            if account_info["data"][0]["userMetadata"][0]["discordUser"] is None:
                if not self.camp_loyalty.camp_network.discord_token:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Discord token is None. Please add token to data/discord_tokens.txt"
                    )
                else:
                    if not await self.connect_discord():
                        success = False
            else:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Discord already connected"
                )

            if success:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Successfully connected socials"
                )
            else:
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Failed to connect socials"
                )

            return success

        except Exception as e:
            random_pause = random.randint(
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    0
                ],
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    1
                ],
            )
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Connect socials error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            return False

    @retry_async(default_value=False)
    async def connect_twitter(self):
        try:
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Starting connect twitter..."
            )

            cookies = {
                "__Secure-next-auth.callback-url": "https%3A%2F%2Floyalty.campnetwork.xyz",
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
                "__Secure-next-auth.csrf-token": self.camp_loyalty.login_csrf_token,
            }

            headers = {
                "cache-control": "max-age=0",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-bitness": '"64"',
                "origin": "https://loyalty.campnetwork.xyz",
                "content-type": "application/x-www-form-urlencoded",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=0, i",
            }

            response = await self.camp_loyalty.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/twitter/auth",
                cookies=cookies,
                headers=headers,
            )

            response_url = response.url

            code_challenge = response_url.split("code_challenge=")[1].split("&")[0]
            state = response_url.split("state=")[1].split("&")[0]
            code_challenge_method = response_url.split("code_challenge_method=")[
                1
            ].split("&")[0]
            client_id = response_url.split("client_id=")[1].split("&")[0]

            generated_csrf_token = secrets.token_hex(16)

            cookies = {
                "ct0": generated_csrf_token,
                "auth_token": self.camp_loyalty.camp_network.twitter_token,
            }
            cookies_headers = "; ".join(f"{k}={v}" for k, v in cookies.items())

            headers = {
                "cookie": cookies_headers,
                "x-csrf-token": generated_csrf_token,
                "upgrade-insecure-requests": "1",
                "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            params = {
                "client_id": client_id,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "redirect_uri": "https://snag-render.com/api/twitter/auth/callback",
                "response_type": "code",
                "scope": "users.read tweet.read",
                "state": state,
            }

            response = await self.camp_loyalty.camp_network.session.get(
                "https://x.com/i/api/2/oauth2/authorize", params=params, headers=headers
            )
            if "X / Error" in response.text:
                raise Exception("X error. Just try again, if it doesn't work, change the token. Platform bugs :)")
            
            if not response.json().get("auth_code"):
                raise Exception(
                    f"Failed to connect twitter: no auth_code in response: {response.status_code} | {response.text}"
                )

            auth_code = response.json().get("auth_code")

            data = {
                "approval": "true",
                "code": auth_code,
            }

            response = await self.camp_loyalty.camp_network.session.post(
                "https://x.com/i/api/2/oauth2/authorize", headers=headers, data=data
            )

            redirect_url = response.json()["redirect_uri"]
            code = redirect_url.split("code=")[1]

            headers = {
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-bitness": '"64"',
                "sec-fetch-site": "cross-site",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=0, i",
            }

            cookies = {
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
                "__Secure-next-auth.callback-url": "https://loyalty.campnetwork.xyz",
                "__Secure-next-auth.csrf-token": self.camp_loyalty.login_csrf_token,
            }

            response = await self.camp_loyalty.camp_network.session.get(
                f"https://loyalty.campnetwork.xyz/api/twitter/auth/connect?code={code}&state={state}",
                cookies=cookies,
                headers=headers,
            )

            random_pause = random.randint(5, 10)
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Sleeping {random_pause} seconds before checking Twitter connection..."
            )
            await asyncio.sleep(random_pause)

            account_info = await self.camp_loyalty.get_user_info()
            if account_info is None:
                raise Exception("Account info is None")

            if account_info["data"][0]["userMetadata"][0]["twitterUser"] is None:
                raise Exception(
                    f"Failed to confirm twitter connection to Loyalty: {response.status_code} | {response.text}"
                )
            else:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Successfully connected twitter to Loyalty"
                )
                return True

        except Exception as e:
            if "Could not authenticate you" in str(e):
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Twitter token is invalid"
                )
                return False

            random_pause = random.randint(
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    0
                ],
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    1
                ],
            )
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Connect twitter error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def connect_discord(self):
        try:
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Starting connect discord..."
            )

            cookies = {
                "__Secure-next-auth.callback-url": "https%3A%2F%2Floyalty.campnetwork.xyz",
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
                "__Secure-next-auth.csrf-token": self.camp_loyalty.login_csrf_token,
            }

            headers = {
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-bitness": '"64"',
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
                "referer": "https://loyalty.campnetwork.xyz/home?editProfile=1&modalTab=social",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=0, i",
            }

            response = await self.camp_loyalty.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/discord/auth",
                cookies=cookies,
                headers=headers,
            )

            response_url = response.url
            state = response_url.split("state=")[1]

            headers = {
                "Upgrade-Insecure-Requests": "1",
            }

            response = await self.camp_loyalty.camp_network.session.get(
                f"https://discord.com/api/v9/oauth2/authorize?client_id=1082817417195040808&response_type=code&redirect_uri=https%3A%2F%2Fsnag-render.com%2Fapi%2Fdiscord%2Fauth%2Fcallback&scope=identify&state={state}&integration_type=0",
                headers=headers,
            )

            headers = {
                "authorization": self.camp_loyalty.camp_network.discord_token,
                f"referer": f"https://discord.com/oauth2/authorize?response_type=code&client_id=1082817417195040808&redirect_uri=https%3A%2F%2Fsnag-render.com%2Fapi%2Fdiscord%2Fauth%2Fcallback&scope=identify&state={state}",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
            }

            params = {
                "client_id": "1082817417195040808",
                "response_type": "code",
                "redirect_uri": "https://snag-render.com/api/discord/auth/callback",
                "scope": "identify",
                "state": state,
                "integration_type": "0",
            }

            response = await self.camp_loyalty.camp_network.session.get(
                "https://discord.com/api/v9/oauth2/authorize",
                params=params,
                headers=headers,
            )

            headers = {
                "authorization": self.camp_loyalty.camp_network.discord_token,
                "content-type": "application/json",
                "origin": "https://discord.com",
                "referer": f"https://discord.com/oauth2/authorize?response_type=code&client_id=1318915934878040064&scope=identify&state={state}",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
            }

            params = {
                "client_id": "1082817417195040808",
                "response_type": "code",
                "redirect_uri": "https://snag-render.com/api/discord/auth/callback",
                "scope": "identify",
                "state": state,
            }

            json_data = {
                "permissions": "0",
                "authorize": True,
                "integration_type": 0,
                "location_context": {
                    "guild_id": "10000",
                    "channel_id": "10000",
                    "channel_type": 10000,
                },
                "dm_settings": {
                    "allow_mobile_push": False,
                },
            }

            response = await self.camp_loyalty.camp_network.session.post(
                "https://discord.com/api/v9/oauth2/authorize",
                params=params,
                headers=headers,
                json=json_data,
            )

            if not response.json()["location"]:
                raise Exception("Failed to connect discord: no location in response")

            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "referer": "https://discord.com/",
                "upgrade-insecure-requests": "1",
            }

            code = response.json()["location"].split("code=")[1].split("&")[0]

            headers = {
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-ch-ua": '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-bitness": '"64"',
                "sec-fetch-site": "cross-site",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "priority": "u=0, i",
            }

            cookies = {
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
                "__Secure-next-auth.callback-url": "https://loyalty.campnetwork.xyz",
                "__Secure-next-auth.csrf-token": self.camp_loyalty.login_csrf_token,
            }

            response = await self.camp_loyalty.camp_network.session.get(
                f"https://loyalty.campnetwork.xyz/api/discord/auth/connect?code={code}&state={state}",
                cookies=cookies,
                headers=headers,
            )

            random_pause = random.randint(5, 10)
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Sleeping {random_pause} seconds before checking Discord connection..."
            )
            await asyncio.sleep(random_pause)

            account_info = await self.camp_loyalty.get_user_info()
            if account_info is None:
                raise Exception("Account info is None")

            if account_info["data"][0]["userMetadata"][0]["discordUser"] is None:
                raise Exception(
                    f"Failed to confirm discord connection to Loyalty: {response.status_code} | {response.text}"
                )
            else:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Successfully connected discord to Loyalty"
                )
                return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    0
                ],
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    1
                ],
            )
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Loyalty connect discord error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=False)
    async def set_display_name(self):
        try:
            account_info = await self.camp_loyalty.get_user_info()
            if account_info is None:
                raise Exception("Account info is None")

            if account_info["data"][0]["userMetadata"][0]["displayName"] is not None:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Display name already set at Loyalty: {account_info['data'][0]['userMetadata'][0]['displayName']}"
                )
                return True

            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Starting set display name at Loyalty..."
            )

            cookies = {
                "__Secure-next-auth.callback-url": "https://loyalty.campnetwork.xyz",
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
            }

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "content-type": "application/json",
                "origin": "https://loyalty.campnetwork.xyz",
                "priority": "u=1, i",
                "referer": "https://loyalty.campnetwork.xyz/home?editProfile=1&modalTab=about",
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

            # Generate random username 6-10 chars, max 2 consecutive vowels or consonants
            vowels = "aeiouy"
            consonants = "bcdfghjklmnpqrstvwxz"
            length = random.randint(6, 10)
            name = []
            for i in range(length):
                if i > 1 and all(c in vowels for c in name[-2:]):
                    name.append(random.choice(consonants))
                elif i > 1 and all(c in consonants for c in name[-2:]):
                    name.append(random.choice(vowels))
                else:
                    name.append(random.choice(vowels + consonants))
            display_name = "".join(name)
            if random.choice([True, False]):
                display_name = display_name.capitalize()

            json_data = {
                "bio": (
                    account_info["data"][0]["userMetadata"][0]["bio"]
                    if account_info["data"][0]["userMetadata"][0]["bio"] is not None
                    else ""
                ),
                "displayName": display_name,
                "location": (
                    account_info["data"][0]["userMetadata"][0]["location"]
                    if account_info["data"][0]["userMetadata"][0]["location"]
                    is not None
                    else ""
                ),
                "portfolioUrl": (
                    account_info["data"][0]["userMetadata"][0]["portfolioUrl"]
                    if account_info["data"][0]["userMetadata"][0]["portfolioUrl"]
                    is not None
                    else ""
                ),
                "logoUrl": (
                    account_info["data"][0]["userMetadata"][0]["logoUrl"]
                    if account_info["data"][0]["userMetadata"][0]["logoUrl"] is not None
                    else ""
                ),
            }

            user_id = account_info["data"][0]["id"]

            response = await self.camp_loyalty.camp_network.session.post(
                f"https://loyalty.campnetwork.xyz/api/users/{user_id}",
                cookies=cookies,
                headers=headers,
                json=json_data,
            )

            if response.json()["success"]:
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Successfully set display name at Loyalty: {json_data['displayName']}"
                )
                return True
            else:
                raise Exception(
                    f"Failed to set display name at Loyalty: {response.status_code} | {response.text}"
                )

        except Exception as e:
            if "Could not authenticate you" in str(e):
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Twitter token is invalid"
                )
                return False

            random_pause = random.randint(
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    0
                ],
                self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
                    1
                ],
            )
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Set Loyalty display name error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    # @retry_async(default_value=False)
    # async def set_email(self):
    #     try:
    #         account_info = await self.camp_loyalty.get_user_info()
    #         if account_info is None:
    #             raise Exception("Account info is None")

    #         user_id = account_info["data"][0]["id"]
    #         if account_info["data"][0]["userMetadata"][0]["emailAddress"] is not None:
    #             logger.success(
    #                 f"{self.camp_loyalty.camp_network.account_index} | Email already set at Loyalty: {account_info['data'][0]['userMetadata'][0]['emailAddress']}"
    #             )
    #             return True

    #         logger.info(
    #             f"{self.camp_loyalty.camp_network.account_index} | Starting set email at Loyalty..."
    #         )

            
    #         cookies = {
    #             '__Secure-next-auth.callback-url': 'https://loyalty.campnetwork.xyz',
    #             'cf_clearance': self.camp_loyalty.cf_clearance,
    #             '__Secure-next-auth.session-token': self.camp_loyalty.login_session_token,
    #         }

    #         headers = {
    #             'accept': 'application/json, text/plain, */*',
    #             'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4',
    #             'content-type': 'application/json',
    #             'origin': 'https://loyalty.campnetwork.xyz',
    #             'priority': 'u=1, i',
    #             'sec-ch-ua': '"Chromium";v="133", "Google Chrome";v="133", "Not.A/Brand";v="99"',
    #             'sec-ch-ua-arch': '"x86"',
    #             'sec-ch-ua-bitness': '"64"',
    #             'sec-ch-ua-mobile': '?0',
    #             'sec-ch-ua-model': '""',
    #             'sec-ch-ua-platform': '"Windows"',
    #             'sec-fetch-dest': 'empty',
    #             'sec-fetch-mode': 'cors',
    #             'sec-fetch-site': 'same-origin',
    #             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    #         }

    #         json_data = {
    #             'emailAddress': self.camp_loyalty.camp_network.email.split(":")[0],
    #         }

    #         response = await self.camp_loyalty.camp_network.session.post(
    #             f'https://loyalty.campnetwork.xyz/api/users/{user_id}',
    #             cookies=cookies,
    #             headers=headers,
    #             json=json_data,
    #         )

    #         if not response.json()["success"]:
    #             raise Exception(
    #                 f"Failed to start set email at Loyalty: {response.status_code} | {response.text}"
    #             )

    #         logger.info(
    #             f"{self.camp_loyalty.camp_network.account_index} | Email code sent to {self.camp_loyalty.camp_network.email} at Loyalty"
    #         )

    #         email_checker = email_parser.SyncEmailChecker(
    #             email=self.camp_loyalty.camp_network.email.split(":")[0], password=self.camp_loyalty.camp_network.email.split(":")[1]
    #         )

    #         if email_checker.check_if_email_valid():
    #             # Search for verification code
    #             logger.info(f"{self.camp_loyalty.camp_network.account_index} | Searching for email code...")
    #             verify_link = email_checker.check_email_for_verification_link()
    #             if verify_link:
    #                 logger.success(f"{self.camp_loyalty.camp_network.account_index} | Email code: {verify_link}")
    #                 verify_link = verify_link.strip()
    #             else:
    #                 raise Exception("Failed to get email verification link")
    #         else:
    #             logger.error(f"{self.camp_loyalty.camp_network.account_index} | Invalid email credentials")
    #             return False
            
    #         await self.camp_loyalty.camp_network.session.get(
    #             verify_link,
    #             cookies=cookies,
    #             headers=headers,
    #         )

    #         random_pause = random.randint(5, 10)
    #         logger.info(f"{self.camp_loyalty.camp_network.account_index} | Sleeping {random_pause} seconds before checking email...")
    #         await asyncio.sleep(random_pause)

    #         account_info = await self.camp_loyalty.get_user_info()
    #         if account_info is None:
    #             raise Exception("Account info is None")

    #         if account_info["data"][0]["userMetadata"][0]["emailAddress"] is not None:
    #             logger.success(
    #                 f"{self.camp_loyalty.camp_network.account_index} | Successfully set email at Loyalty: {account_info['data'][0]['userMetadata'][0]['emailAddress']}"
    #             )
    #             return True
    #         else:
    #             raise Exception("Failed to set email at Loyalty")
            
    #     except Exception as e:
    #         if "Could not authenticate you" in str(e):
    #             logger.error(
    #                 f"{self.camp_loyalty.camp_network.account_index} | Twitter token is invalid"
    #             )
    #             return False

    #         random_pause = random.randint(
    #             self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
    #                 0
    #             ],
    #             self.camp_loyalty.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[
    #                 1
    #             ],
    #         )   
    #         logger.error(
    #             f"{self.camp_loyalty.camp_network.account_index} | Set Loyalty email error: {e}. Sleeping {random_pause} seconds..."
    #         )
    #         await asyncio.sleep(random_pause)
    #         raise
