from web3 import Web3
import random
import asyncio
from loguru import logger
from faker import Faker

from src.model.help.cookies import CookieDatabase
from src.model.camp_network.constants import CampNetworkProtocol
from src.utils.decorators import retry_async
from src.utils.constants import EXPLORER_URL_CAMP_NETWORK


class Bleetz:
    def __init__(self, instance: CampNetworkProtocol):
        self.camp_network = instance
        self.contract_address = "0x0b0A5B8e848b27a05D5cf45CAab72BC82dF48546"

    @retry_async(default_value=False)
    async def mint_nft(self) -> bool:
        try:
            # Check if wallet already has a BleetzGamerID NFT
            contract = self.camp_network.web3.web3.eth.contract(
                address=self.camp_network.web3.web3.to_checksum_address(
                    self.contract_address
                ),
                abi=[
                    {
                        "inputs": [
                            {
                                "internalType": "address",
                                "name": "owner",
                                "type": "address",
                            }
                        ],
                        "name": "balanceOf",
                        "outputs": [
                            {"internalType": "uint256", "name": "", "type": "uint256"}
                        ],
                        "stateMutability": "view",
                        "type": "function",
                    }
                ],
            )
            nft_balance = await contract.functions.balanceOf(
                self.camp_network.wallet.address
            ).call()

            if nft_balance > 0:
                logger.info(
                    f"{self.camp_network.account_index} | Already has BleetzGamerID"
                )
                return True

            logger.info(f"{self.camp_network.account_index} | Minting BleetzGamerID...")

            balance = await self.camp_network.web3.web3.eth.get_balance(
                self.camp_network.wallet.address
            )
            if balance < Web3.to_wei(0.000001, "ether"):
                logger.error(
                    f"{self.camp_network.account_index} | Insufficient balance. Need at least 0.000001 ETH to mint BleetzGamerID."
                )
                return False

            # Base payload with method ID 0xae873a3f for mintGamerID()
            payload = "0xae873a3f"

            chain_id = await self.camp_network.web3.web3.eth.chain_id

            # Prepare transaction with 0 ETH value
            transaction = {
                "from": self.camp_network.wallet.address,
                "to": self.camp_network.web3.web3.to_checksum_address(
                    self.contract_address
                ),
                "value": Web3.to_wei(0, "ether"),
                "nonce": await self.camp_network.web3.web3.eth.get_transaction_count(
                    self.camp_network.wallet.address
                ),
                "chainId": chain_id,
                "data": payload,
            }

            # Get dynamic gas parameters
            gas_params = await self.camp_network.web3.get_gas_params()
            transaction.update(gas_params)

            # Estimate gas
            gas_limit = await self.camp_network.web3.estimate_gas(transaction)
            transaction["gas"] = gas_limit

            # Execute transaction
            tx_hash = await self.camp_network.web3.execute_transaction(
                transaction,
                self.camp_network.wallet,
                chain_id,
                EXPLORER_URL_CAMP_NETWORK,
            )

            if tx_hash:
                logger.success(
                    f"{self.camp_network.account_index} | Successfully minted BleetzGamerID"
                )

            return True

        except Exception as e:
            random_pause = random.randint(
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.camp_network.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.camp_network.account_index} | BleetzGamerID mint error: {e}. Sleeping {random_pause} seconds..."
            )
            await asyncio.sleep(random_pause)
            raise
