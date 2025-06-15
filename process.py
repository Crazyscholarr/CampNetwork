import asyncio
import random
from loguru import logger


import src.utils

from src.utils.proxy_parser import Proxy
import src.model
from src.utils.statistics import print_wallets_stats
from src.utils.logs import ProgressTracker, create_progress_tracker
from src.utils.config_browser import run


async def start():
    async def launch_wrapper(
        index, proxy, private_key, discord_token, twitter_token, email
    ):
        async with semaphore:
            await account_flow(
                index,
                proxy,
                private_key,
                discord_token,
                twitter_token,
                email,
                config,
                progress_tracker,
            )

    # Hiển thị thông báo quan trọng với màu sắc và emoji
    print("\n" + "=" * 80)
    print("🚨 \033[93mTHÔNG BÁO QUAN TRỌNG\033[0m 🚨")
    print("=" * 80)
    print(
        "📚 \033[96mRẤT KHUYẾN NGHỊ đọc hướng dẫn trước khi sử dụng bot!\033[0m"
    )
    print(
        "🔗 \033[96mHướng dẫn: https://github.com/Crazyscholarr/CampNetwork\033[0m"
    )
    print(
        "⚠️ \033[91mVui lòng đọc tài liệu để tránh lỗi và sử dụng đúng cách.\033[0m"
    )
    print("=" * 80 + "\n")

    print("\nCác lựa chọn có sẵn:\n")
    print("[1] 🚀 Bắt đầu chạy nhiệm vụ")
    print("[2] ⚙️ Chỉnh sửa cấu hình")
    print("[3] 💾 Quản lý cơ sở dữ liệu")
    print()

    try:
        choice = input("Nhập lựa chọn (1-3): ").strip()
    except Exception as e:
        logger.error(f"Lỗi nhập liệu: {e}")
        return

    if choice == "4" or not choice:
        raise SystemExit
    elif choice == "2":
        run()
        return
    elif choice == "1":
        pass
    elif choice == "3":
        from src.model.database.db_manager import show_database_menu

        await show_database_menu()
        await start()
    else:
        logger.error(f"Invalid choice: {choice}")
        return

    config = src.utils.get_config()

    # Load proxies using proxy parser
    try:
        proxy_objects = Proxy.from_file("data/proxies.txt")
        proxies = [proxy.get_default_format() for proxy in proxy_objects]
        if len(proxies) == 0:
            logger.error("No proxies found in data/proxies.txt")
            return
    except Exception as e:
        logger.error(f"Failed to load proxies: {e}")
        return

    private_keys = src.utils.read_private_keys("data/private_keys.txt")

    # Read tokens and handle empty files by filling with empty strings
    discord_tokens = src.utils.read_txt_file(
        "discord tokens", "data/discord_tokens.txt"
    )
    twitter_tokens = src.utils.read_txt_file(
        "twitter tokens", "data/twitter_tokens.txt"
    )
    emails = src.utils.read_txt_file("emails", "data/emails.txt")
    # Handle the case when there are more private keys than Twitter tokens
    if len(twitter_tokens) < len(private_keys):
        # Pad with empty strings
        twitter_tokens.extend([""] * (len(private_keys) - len(twitter_tokens)))
    # Handle the case when there are more Twitter tokens than private keys
    elif len(twitter_tokens) > len(private_keys):
        # Store excess Twitter tokens in config
        config.spare_twitter_tokens = twitter_tokens[len(private_keys) :]
        twitter_tokens = twitter_tokens[: len(private_keys)]
        logger.info(
            f"Stored {len(config.spare_twitter_tokens)} excess Twitter tokens in config.spare_twitter_tokens"
        )
    else:
        # Equal number of tokens and private keys
        config.spare_twitter_tokens = []

    # If token files are empty or have fewer tokens than private keys, pad with empty strings
    while len(discord_tokens) < len(private_keys):
        discord_tokens.append("")
    while len(twitter_tokens) < len(private_keys):
        twitter_tokens.append("")
    while len(emails) < len(private_keys):
        emails.append("")

    # Определяем диапазон аккаунтов
    start_index = config.SETTINGS.ACCOUNTS_RANGE[0]
    end_index = config.SETTINGS.ACCOUNTS_RANGE[1]

    # Если оба 0, проверяем EXACT_ACCOUNTS_TO_USE
    if start_index == 0 and end_index == 0:
        if config.SETTINGS.EXACT_ACCOUNTS_TO_USE:
            # Преобразуем номера аккаунтов в индексы (номер - 1)
            selected_indices = [i - 1 for i in config.SETTINGS.EXACT_ACCOUNTS_TO_USE]
            accounts_to_process = [private_keys[i] for i in selected_indices]
            discord_tokens_to_process = [discord_tokens[i] for i in selected_indices]
            twitter_tokens_to_process = [twitter_tokens[i] for i in selected_indices]
            emails_to_process = [emails[i] for i in selected_indices]
            logger.info(
                f"Using specific accounts: {config.SETTINGS.EXACT_ACCOUNTS_TO_USE}"
            )

            # Для совместимости с остальным кодом
            start_index = min(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
            end_index = max(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
        else:
            # Если список пустой, берем все аккаунты как раньше
            accounts_to_process = private_keys
            discord_tokens_to_process = discord_tokens
            twitter_tokens_to_process = twitter_tokens
            emails_to_process = emails
            start_index = 1
            end_index = len(private_keys)
    else:
        # Python slice не включает последний элемент, поэтому +1
        accounts_to_process = private_keys[start_index - 1 : end_index]
        discord_tokens_to_process = discord_tokens[start_index - 1 : end_index]
        twitter_tokens_to_process = twitter_tokens[start_index - 1 : end_index]
        emails_to_process = emails[start_index - 1 : end_index]

    threads = config.SETTINGS.THREADS

    # Подготавливаем прокси для выбранных аккаунтов
    cycled_proxies = [
        proxies[i % len(proxies)] for i in range(len(accounts_to_process))
    ]

    # Создаем список индексов
    indices = list(range(len(accounts_to_process)))

    # Перемешиваем индексы только если включен SHUFFLE_WALLETS
    if config.SETTINGS.SHUFFLE_WALLETS:
        random.shuffle(indices)
        shuffle_status = "random"
    else:
        shuffle_status = "sequential"

    # Создаем строку с порядком аккаунтов
    if config.SETTINGS.EXACT_ACCOUNTS_TO_USE:
        # Создаем список номеров аккаунтов в нужном порядке
        ordered_accounts = [config.SETTINGS.EXACT_ACCOUNTS_TO_USE[i] for i in indices]
        account_order = " ".join(map(str, ordered_accounts))
        logger.info(f"Đang sử dụng các tài khoản cụ thể: {config.SETTINGS.EXACT_ACCOUNTS_TO_USE}")
        logger.info(f"Bắt đầu với các tài khoản cụ thể theo thứ tự {shuffle_status}...")
    else:
        account_order = " ".join(str(start_index + idx) for idx in indices)
        logger.info(
            f"Bắt đầu với các tài khoản từ {start_index} đến {end_index} theo thứ tự {shuffle_status}..."
        )
    logger.info(f"Thứ tự tài khoản: {account_order}")

    semaphore = asyncio.Semaphore(value=threads)
    tasks = []

    # Add before creating tasks
    progress_tracker = await create_progress_tracker(
        total=len(accounts_to_process), description="Accounts completed"
    )

    # Используем индексы для создания задач
    for idx in indices:
        actual_index = (
            config.SETTINGS.EXACT_ACCOUNTS_TO_USE[idx]
            if config.SETTINGS.EXACT_ACCOUNTS_TO_USE
            else start_index + idx
        )
        tasks.append(
            asyncio.create_task(
                launch_wrapper(
                    actual_index,
                    cycled_proxies[idx],
                    accounts_to_process[idx],
                    discord_tokens_to_process[idx],
                    twitter_tokens_to_process[idx],
                    emails_to_process[idx],
                )
            )
        )

    await asyncio.gather(*tasks)

    logger.success("Đã lưu tài khoản và private key vào file.")

    print_wallets_stats(config)

    input("Nhấn Enter để tiếp tục...")


async def account_flow(
    account_index: int,
    proxy: str,
    private_key: str,
    discord_token: str,
    twitter_token: str,
    email: str,
    config: src.utils.config.Config,
    progress_tracker: ProgressTracker,
):
    try:
        instance = src.model.Start(
            account_index,
            proxy,
            private_key,
            config,
            discord_token,
            twitter_token,
            email,
        )

        result = await wrapper(instance.initialize, config)
        if not result:
            raise Exception("Failed to initialize")

        result = await wrapper(instance.flow, config)
        if not result:
            report = True

        # Add progress update
        await progress_tracker.increment(1)

    except Exception as err:
        logger.error(f"{account_index} | Account flow failed: {err}")
        # Update progress even if there's an error
        await progress_tracker.increment(1)


async def wrapper(function, config: src.utils.config.Config, *args, **kwargs):
    attempts = config.SETTINGS.ATTEMPTS
    attempts = 1
    for attempt in range(attempts):
        result = await function(*args, **kwargs)
        if isinstance(result, tuple) and result and isinstance(result[0], bool):
            if result[0]:
                return result
        elif isinstance(result, bool):
            if result:
                return True

        if attempt < attempts - 1:  # Don't sleep after the last attempt
            pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.info(
                f"Sleeping for {pause} seconds before next attempt {attempt+1}/{config.SETTINGS.ATTEMPTS}..."
            )
            await asyncio.sleep(pause)

    return result
