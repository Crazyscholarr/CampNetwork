import random
import asyncio
import secrets
from loguru import logger

from src.model.projects.camp_loyalty.other_quests.bleetz import Bleetz
from src.model.projects.camp_loyalty.other_quests.awana import Awana
from src.model.projects.camp_loyalty.other_quests.pictographs import Pictographs
from src.model.projects.camp_loyalty.connect_socials import ConnectLoyaltySocials
from src.model.help import email_parser
from src.model.projects.camp_loyalty.constants import CampLoyaltyProtocol
from src.utils.decorators import retry_async
from src.model.help.twitter import Twitter
from src.model.help.discord import DiscordInviter

# task: campaign name
QUESTS_NAMES = {
    "camp_loyalty_storychain": "StoryChain",
    "camp_loyalty_token_tails": "Token Tails",
    "camp_loyalty_awana": "AWANA",
    "camp_loyalty_pictographs": "Pictographs",
    "camp_loyalty_hitmakr": "Hitmakr",
    "camp_loyalty_panenka": "Panenka",
    "camp_loyalty_scoreplay": "Scoreplay",
    "camp_loyalty_wide_worlds": "Wide Worlds",
    "camp_loyalty_entertainm": "EntertainM",
    "camp_loyalty_rewarded_tv": "RewardedTV",
    "camp_loyalty_sporting_cristal": "Sporting Cristal",
    "camp_loyalty_belgrano": "Belgrano",
    "camp_loyalty_arcoin": "ARCOIN",
    "camp_loyalty_kraft": "Kraft",
    "camp_loyalty_summitx": "SummitX",
    "camp_loyalty_pixudi": "Pixudi",
    "camp_loyalty_clusters": "Clusters",
    "camp_loyalty_jukeblox": "JukeBlox",
    "camp_loyalty_camp_network": "Camp Network",
}


DOABLE_QUESTS = [
    "Mint Pictographs Memory Card",
    "Create your Bleetz GamerID",
    # "Login to AWANA for the First Time"
]


class LoyaltyQuests:
    def __init__(self, camp_loyalty_instance: CampLoyaltyProtocol):
        self.camp_loyalty = camp_loyalty_instance
        self.twitter: Twitter | None = None
        self.discord: DiscordInviter | None = None

    async def complete_quests(self, task: str):
        try:
            if task != "camp_loyalty_complete_quests":
                campaign_name = QUESTS_NAMES[task]
                logger.info(
                    f"{self.camp_loyalty.camp_network.account_index} | Completing quest {campaign_name}..."
                )
            else:
                logger.info(
                    f"{self.camp_loyalty.camp_network.account_index} | Starting campaigns completion..."
                )

            campaigns = await self._get_all_campaigns()

            if not await self._initialize_twitter():
                return False

            for campaign in campaigns:
                if task != "camp_loyalty_complete_quests":
                    if campaign["name"] != campaign_name:
                        continue
                else:
                    logger.info(
                        f"{self.camp_loyalty.camp_network.account_index} | Completing campaign {campaign['name']}..."
                    )

                for quest in campaign["loyaltyGroupItems"]:
                    if (
                        quest["loyaltyRule"]["type"]
                        not in [
                            "drip_x_follow",
                            "link_click",
                        ]
                        and quest["loyaltyRule"]["name"] not in DOABLE_QUESTS
                    ):
                        # logger.warning(
                        #     f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} does not require completion. Skipping..."
                        # )
                        continue

                    await self._complete_quest(quest)
                    random_pause = random.randint(
                        self.camp_loyalty.camp_network.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[
                            0
                        ],
                        self.camp_loyalty.camp_network.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[
                            1
                        ],
                    )
                    logger.info(
                        f"{self.camp_loyalty.camp_network.account_index} | Sleeping {random_pause} seconds before next quest..."
                    )
                    await asyncio.sleep(random_pause)

            return True

        except Exception as e:
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Campaigns error: {e}."
            )
            return False

    async def _complete_quest(self, quest: dict):
        try:
            if quest["loyaltyRule"]["name"] in DOABLE_QUESTS:
                if quest["loyaltyRule"]["name"] == "Mint Pictographs Memory Card":
                    pictographs = Pictographs(self.camp_loyalty.camp_network)
                    await pictographs.mint_nft()
                    return True
                elif (
                    quest["loyaltyRule"]["name"] == "Login to AWANA for the First Time"
                ):
                    awana = Awana(self.camp_loyalty.camp_network)
                    await awana.complete_quest()
                    return True
                elif quest["loyaltyRule"]["name"] == "Create your Bleetz GamerID":
                    bleetz = Bleetz(self.camp_loyalty.camp_network)
                    await bleetz.mint_nft()
                    return True

            is_completed = await self._verify_quest_completion(quest)
            if is_completed == "need_to_complete_quest":
                pass
            elif is_completed:
                return True

            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Completing quest {quest['loyaltyRule']['name']}..."
            )

            if quest["loyaltyRule"]["type"] == "drip_x_follow":
                user_to_follow = quest["loyaltyRule"]["metadata"][
                    "twitterAccountUrl"
                ].split("/")[-1]
                status = await self.twitter.follow(user_to_follow)
                if not status:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Failed to follow user {user_to_follow}."
                    )
                    raise Exception(f"Failed to follow user {user_to_follow}.")

            elif quest["loyaltyRule"]["type"] == "link_click":
                logger.info(
                    f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} is a link click quest. Completing..."
                )

            else:
                # logger.warning(
                #     f"{self.camp_loyalty.camp_network.account_index} | Unknown quest type: {quest['loyaltyRule']['type']}. Can't complete it, skipping..."
                # )
                return False

            status = await self._verify_quest_completion(quest)
            if not status:
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Failed to complete quest {quest['loyaltyRule']['name']}."
                )
                raise Exception(
                    f"Failed to complete quest {quest['loyaltyRule']['name']}."
                )
            else:
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
                f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    @retry_async(default_value=None)
    async def _get_all_campaigns(self):
        try:
            cookies = {
                "__Secure-next-auth.callback-url": "https%3A%2F%2Floyalty.campnetwork.xyz",
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
            }

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
                "sec-ch-ua-platform-version": '"19.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            }

            params = {
                "limit": "1000",
                "websiteId": "32afc5c9-f0fb-4938-9572-775dee0b4a2b",
                "organizationId": "26a1764f-5637-425e-89fa-2f3fb86e758c",
            }

            response = await self.camp_loyalty.camp_network.session.get(
                "https://loyalty.campnetwork.xyz/api/loyalty/rule_groups",
                params=params,
                cookies=cookies,
                headers=headers,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get all campaigns: {response.status_code} | {response.text}"
                )

            return response.json()["data"]

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
                f"{self.camp_loyalty.camp_network.account_index} | Get all campaigns error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise

    async def _initialize_twitter(self):
        """Initialize Twitter instance for campaign completion"""
        try:
            while True:
                self.twitter = Twitter(
                    self.camp_loyalty.camp_network.account_index,
                    self.camp_loyalty.camp_network.twitter_token,
                    self.camp_loyalty.camp_network.proxy,
                    self.camp_loyalty.camp_network.config,
                )
                ok = await self.twitter.initialize()
                if not ok:
                    if (
                        not self.camp_loyalty.camp_network.config.LOYALTY.REPLACE_FAILED_TWITTER_ACCOUNT
                    ):
                        logger.error(
                            f"{self.camp_loyalty.camp_network.account_index} | Failed to initialize twitter instance. Skipping campaigns completion."
                        )
                        return False
                    else:
                        if not await self._replace_twitter_token():
                            return False
                        continue
                break
            return True
        except Exception as e:
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Error initializing Twitter: {e}"
            )
            return False

    async def _replace_twitter_token(self) -> bool:
        """
        Replaces the current Twitter token with a new one from spare tokens.
        Returns True if replacement was successful, False otherwise.
        """
        try:
            async with self.camp_loyalty.camp_network.config.lock:
                if (
                    not self.camp_loyalty.camp_network.config.spare_twitter_tokens
                    or len(self.camp_loyalty.camp_network.config.spare_twitter_tokens)
                    == 0
                ):
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Twitter token is invalid and no spare tokens available. Please check your twitter token!"
                    )
                    return False

                # Get a new token from the spare tokens list
                new_token = (
                    self.camp_loyalty.camp_network.config.spare_twitter_tokens.pop(0)
                )
                old_token = self.camp_loyalty.camp_network.twitter_token
                self.camp_loyalty.camp_network.twitter_token = new_token

                # Update the token in the file
                try:
                    with open("data/twitter_tokens.txt", "r", encoding="utf-8") as f:
                        tokens = f.readlines()

                    # Process tokens to replace old with new and remove duplicates
                    processed_tokens = []
                    replaced = False

                    for token in tokens:
                        stripped_token = token.strip()

                        # Skip if it's a duplicate of the new token
                        if stripped_token == new_token:
                            continue

                        # Replace old token with new token
                        if stripped_token == old_token:
                            if not replaced:
                                processed_tokens.append(f"{new_token}\n")
                                replaced = True
                        else:
                            processed_tokens.append(token)

                    # If we didn't replace anything (old token not found), add new token
                    if not replaced:
                        processed_tokens.append(f"{new_token}\n")

                    with open("data/twitter_tokens.txt", "w", encoding="utf-8") as f:
                        f.writelines(processed_tokens)

                    logger.info(
                        f"{self.camp_loyalty.camp_network.account_index} | Replaced invalid Twitter token with a new one"
                    )

                    connecter = ConnectLoyaltySocials(self.camp_loyalty)
                    # Try to connect the new token
                    if await connecter.connect_twitter():
                        logger.success(
                            f"{self.camp_loyalty.camp_network.account_index} | Successfully connected new Twitter token"
                        )
                        return True
                    else:
                        logger.error(
                            f"{self.camp_loyalty.camp_network.account_index} | Failed to connect new Twitter token, trying another one..."
                        )
                        return False

                except Exception as file_err:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Failed to update token in file: {file_err}"
                    )
                    return False

        except Exception as e:
            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Error replacing Twitter token: {e}"
            )
            return False

    @retry_async(default_value=False)
    async def _verify_quest_completion(self, quest: dict):
        try:
            random_pause = random.randint(
                self.camp_loyalty.camp_network.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[
                    0
                ],
                self.camp_loyalty.camp_network.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[
                    1
                ],
            )
            logger.info(
                f"{self.camp_loyalty.camp_network.account_index} | Waiting for {random_pause} seconds before verifying quest completion..."
            )
            await asyncio.sleep(random_pause)

            cookies = {
                "__Secure-next-auth.callback-url": "https%3A%2F%2Floyalty.campnetwork.xyz",
                "cf_clearance": self.camp_loyalty.cf_clearance,
                "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
            }

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
                "origin": "https://loyalty.campnetwork.xyz",
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

            json_data = {}

            response = await self.camp_loyalty.camp_network.session.post(
                f'https://loyalty.campnetwork.xyz/api/loyalty/rules/{quest["loyaltyRule"]["id"]}/complete',
                cookies=cookies,
                headers=headers,
                json=json_data,
            )

            if "Just a moment" in response.text:
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Cloudflare cookies expired. Need to relogin to loyalty.campnetwork.xyz"
                )
                await self.camp_loyalty.login()
                raise Exception("Trying again...")

            if (
                "You have already been rewarded" in response.text
                or "You have already clicked the link" in response.text
            ):
                logger.success(
                    f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} already completed"
                )
                return True

            if response.status_code != 200:
                raise Exception(
                    f"Failed to verify quest completion: {response.status_code} | {response.text}"
                )

            if response.json()["message"] in [
                "Completion request added to queue",
                "Link click being verified, come back later to check the status",
            ]:

                logger.info(
                    f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} added to queue"
                )
                completed = await self._wait_for_quest_completion(quest)
                if completed == "need_to_complete_quest":
                    return "need_to_complete_quest"
                if completed:
                    logger.success(
                        f"{self.camp_loyalty.camp_network.account_index} | Quest completed: {quest['loyaltyRule']['name']}"
                    )
                    return True
                else:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} not completed"
                    )
                    return False

            else:
                logger.error(
                    f"{self.camp_loyalty.camp_network.account_index} | Failed to verify quest completion: {response.json()['reason']}"
                )
                return False

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
                f"{self.camp_loyalty.camp_network.account_index} | Verify {quest['loyaltyRule']['name']} quest completion error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise e

    @retry_async(default_value=False)
    async def _wait_for_quest_completion(self, quest: dict):
        try:
            counter = 0
            while (
                counter
                < self.camp_loyalty.camp_network.config.LOYALTY.MAX_ATTEMPTS_TO_COMPLETE_QUEST
            ):
                await asyncio.sleep(10)
                logger.info(
                    f"{self.camp_loyalty.camp_network.account_index} | Waiting 10 seconds for quest {quest['loyaltyRule']['name']} to be completed..."
                )

                cookies = {
                    "__Secure-next-auth.callback-url": "https%3A%2F%2Floyalty.campnetwork.xyz",
                    "cf_clearance": self.camp_loyalty.cf_clearance,
                    "__Secure-next-auth.session-token": self.camp_loyalty.login_session_token,
                }

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
                    "websiteId": "32afc5c9-f0fb-4938-9572-775dee0b4a2b",
                    "organizationId": "26a1764f-5637-425e-89fa-2f3fb86e758c",
                    "userId": self.camp_loyalty.user_info["data"][0]["id"],
                }

                response = await self.camp_loyalty.camp_network.session.get(
                    "https://loyalty.campnetwork.xyz/api/loyalty/rules/status",
                    params=params,
                    cookies=cookies,
                    headers=headers,
                )
                if "Just a moment" in response.text:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Cloudflare cookies expired. Need to relogin to loyalty.campnetwork.xyz"
                    )
                    await self.camp_loyalty.login()
                    raise Exception("Trying again...")
                if "try again" in response.text:
                    return "need_to_complete_quest"

                if response.status_code != 200:
                    if "Too many requests" in response.text:
                        logger.error(
                            f"{self.camp_loyalty.camp_network.account_index} | Too many requests. Sleeping 10 seconds..."
                        )
                        await asyncio.sleep(10)
                        continue

                    logger.error(
                        f"Failed to verify quest completion: {response.status_code} | {response.text}"
                    )
                    counter += 1
                    continue

                if response.json()["data"][0]["status"] == "processing":
                    logger.info(
                        f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} is being processed..."
                    )
                    counter += 1
                    continue

                if '"status":"completed"' in response.text:
                    return True

                else:
                    logger.error(
                        f"{self.camp_loyalty.camp_network.account_index} | Failed to verify quest completion: {response.json()['reason']}"
                    )
                    return False

            logger.error(
                f"{self.camp_loyalty.camp_network.account_index} | Quest {quest['loyaltyRule']['name']} not completed after 12 attempts"
            )
            return False

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
                f"{self.camp_loyalty.camp_network.account_index} | Wait for quest completion error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise e
