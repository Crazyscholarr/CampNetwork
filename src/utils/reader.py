import json
from loguru import logger
from eth_account import Account
from eth_account.hdaccount import generate_mnemonic
from web3.auto import w3


def read_txt_file(file_name: str, file_path: str) -> list:
    with open(file_path, "r") as file:
        items = [line.strip() for line in file]

    logger.success(f"Đã tải thành công {len(items)} {file_name}.")
    return items


def split_list(lst, chunk_size=90):
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def read_abi(path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


class InvalidKeyError(Exception):
    """Exception raised for invalid private keys or mnemonic phrases."""

    pass


def read_private_keys(file_path: str) -> list:
    """
    Đọc private key hoặc cụm từ khôi phục từ file và trả về danh sách private key.
    Nếu một dòng là mnemonic, sẽ chuyển thành private key.

    Args:
        file_path (str): Đường dẫn tới file chứa private key hoặc mnemonic

    Returns:
        list: Danh sách private key dạng hex (có tiền tố '0x')

    Raises:
        InvalidKeyError: Nếu có key hoặc mnemonic không hợp lệ trong file
    """
    private_keys = []

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, 1):
            key = line.strip()
            if not key:
                continue

            try:
                # Kiểm tra nếu là mnemonic (12 hoặc 24 từ)
                words = key.split()
                if len(words) in [12, 24]:
                    Account.enable_unaudited_hdwallet_features()
                    account = Account.from_mnemonic(key)
                    private_key = account.key.hex()
                else:
                    # Xử lý như private key
                    if not key.startswith("0x"):
                        key = "0x" + key
                    # Kiểm tra hợp lệ
                    Account.from_key(key)
                    private_key = key

                private_keys.append(private_key)

            except Exception as e:
                raise InvalidKeyError(
                    f"Khóa riêng hoặc cụm từ khôi phục không hợp lệ ở dòng {line_number}: {key[:10]}... Lỗi: {str(e)}"
                )

    logger.success(f"Đã tải thành công {len(private_keys)} private key.")
    return private_keys
