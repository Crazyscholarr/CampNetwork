from dataclasses import dataclass
from typing import Protocol
from primp import AsyncClient
from eth_account import Account

from src.model.camp_network.constants import CampNetworkProtocol
from src.model.help.cookies import CookieDatabase
from src.model.onchain.web3_custom import Web3Custom
from src.utils.config import Config


class CampLoyaltyProtocol(Protocol):
    """Protocol class for CampLoyalty type hints to avoid circular imports"""

    camp_network: CampNetworkProtocol
    cookie_db: CookieDatabase
    cf_clearance: str
    login_session_token: str
    login_csrf_token: str
    
    async def get_account_info(self) -> dict | None: ...
    async def get_user_info(self) -> dict | None: ...
