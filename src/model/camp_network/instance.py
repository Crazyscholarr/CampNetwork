import asyncio
import random
from loguru import logger
from eth_account import Account
import primp
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from src.model.onchain.web3_custom import Web3Custom
from src.utils.decorators import retry_async
from src.utils.config import Config
from src.model.camp_network.faucet import FaucetService


class CampNetwork:
    def __init__(
        self,
        account_index: int,
        session: primp.AsyncClient,
        web3: Web3Custom,
        config: Config,
        wallet: Account,
        discord_token: str,
        twitter_token: str,
        proxy: str,
        private_key: str,
        email: str,
    ):
        self.account_index = account_index
        self.session = session
        self.web3 = web3
        self.config = config
        self.wallet = wallet
        self.discord_token = discord_token
        self.twitter_token = twitter_token
        self.proxy = proxy
        self.private_key = private_key
        self.email = email
    # Удобный метод-прокси для faucet, если нужен
    async def request_faucet(self):
        self.faucet_service = FaucetService(self)
        return await self.faucet_service.request_faucet()

    async def show_account_info(self):
        try:
            account_info = await self.get_account_info()
            account_stats = await self.get_account_stats()
            if account_info and account_stats:
                console = Console()

                # Create a table for account info
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")

                # Add account information
                table.add_row("Address", str(account_info["walletAddress"]))
                table.add_row(
                    "Username", str(account_info["username"] or "Not set")
                )
                table.add_row("Total Points", str(account_stats["totalPoints"]))
                table.add_row("Total Boosters", str(account_stats["totalBoosters"]))
                table.add_row("Final Points", str(account_stats["finalPoints"]))
                table.add_row("Rank", str(account_stats["rank"] or "Not ranked"))
                table.add_row("Total Referrals", str(account_stats["totalReferrals"]))
                table.add_row("Quests Completed", str(account_stats["questsCompleted"]))
                table.add_row("Daily Booster", str(account_stats["dailyBooster"]))
                table.add_row("Streak Count", str(account_stats["streakCount"]))
                table.add_row(
                    "Discord", str(account_info["discordName"] or "Not connected")
                )
                table.add_row(
                    "Twitter", str(account_info["twitterName"] or "Not connected")
                )
                table.add_row(
                    "Telegram", str(account_info["telegramName"] or "Not connected")
                )
                table.add_row(
                    "Referral Code", str(account_info["referralCode"] or "Not set")
                )
                table.add_row("Referral Points", str(account_info["referralPoint"]))

                # Print the table
                console.print(
                    f"\n[bold yellow]Account #{self.account_index} Information:[/bold yellow]"
                )
                console.print(table)
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"{self.account_index} | Show account info error: {e}")
            return False
