import asyncio
import json
import random
from typing import List
from tabulate import tabulate
from loguru import logger

from src.model.database.instance import Database
from src.utils.config import get_config
from src.utils.reader import read_private_keys
from src.utils.proxy_parser import Proxy  # Đã thêm import


async def show_database_menu():
    while True:
        print("\nTùy chọn quản lý Database:\n")
        print("[1] 🗑  Tạo mới/Đặt lại Database")
        print("[2] ➕ Tạo lại nhiệm vụ cho các ví đã hoàn thành")
        print("[3] 📊 Xem nội dung Database")
        print("[4] 🔄 Tạo lại nhiệm vụ cho tất cả ví")
        print("[5] 📝 Thêm ví mới vào Database")
        print("[6] 👋 Thoát")
        print()

        try:
            choice = input("Nhập lựa chọn (1-6): ").strip()

            if choice == "1":
                await reset_database()
            elif choice == "2":
                await regenerate_tasks_for_completed()
            elif choice == "3":
                await show_database_contents()
            elif choice == "4":
                await regenerate_tasks_for_all()
            elif choice == "5":
                await add_new_wallets()
            elif choice == "6":
                print("\nThoát khỏi quản lý database...")
                break
            else:
                logger.error("Lựa chọn không hợp lệ. Vui lòng nhập số từ 1 đến 6.")

        except Exception as e:
            logger.error(f"Lỗi trong quản lý database: {e}")
            await asyncio.sleep(1)


async def reset_database():
    """Tạo mới hoặc đặt lại database hiện tại"""
    print("\n⚠️ CẢNH BÁO: Thao tác này sẽ xóa toàn bộ dữ liệu hiện tại.")
    print("[1] Có")
    print("[2] Không")

    confirmation = input("\nNhập lựa chọn của bạn (1-2): ").strip()

    if confirmation != "1":
        logger.info("Đã hủy thao tác đặt lại database")
        return

    try:
        db = Database()
        await db.clear_database()
        await db.init_db()

        # Tạo nhiệm vụ cho database mới
        config = get_config()
        private_keys = read_private_keys("data/private_keys.txt")

        # Đọc proxy
        try:
            proxy_objects = Proxy.from_file("data/proxies.txt")
            proxies = [proxy.get_default_format() for proxy in proxy_objects]
            if len(proxies) == 0:
                logger.error("Không tìm thấy proxy trong data/proxies.txt")
                return
        except Exception as e:
            logger.error(f"Lỗi khi tải proxy: {e}")
            return

        # Thêm ví với proxy và nhiệm vụ
        for i, private_key in enumerate(private_keys):
            proxy = proxies[i % len(proxies)]

            # Tạo danh sách nhiệm vụ mới cho từng ví
            tasks = generate_tasks_from_config(config)

            if not tasks:
                logger.error(
                    f"Không tạo được nhiệm vụ cho ví {private_key[:4]}...{private_key[-4:]}"
                )
                continue

            await db.add_wallet(
                private_key=private_key,
                proxy=proxy,
                tasks_list=tasks,  # Передаем сгенерированный список задач
            )

        logger.success(
            f"Database đã được đặt lại và khởi tạo với {len(private_keys)} ví!"
        )

    except Exception as e:
        logger.error(f"Lỗi khi đặt lại database: {e}")


def generate_tasks_from_config(config) -> List[str]:
    """Tạo danh sách nhiệm vụ từ config theo đúng định dạng như trong start.py"""
    planned_tasks = []

    # Lấy danh sách nhiệm vụ từ config
    for task_name in config.FLOW.TASKS:
        # Import tasks.py để lấy danh sách nhiệm vụ cụ thể
        import tasks

        # Lấy danh sách các nhiệm vụ con cho nhiệm vụ hiện tại
        task_list = getattr(tasks, task_name)

        # Xử lý từng nhiệm vụ con
        for task_item in task_list:
            if isinstance(task_item, list):
                # Nếu là dạng [], chọn ngẫu nhiên một nhiệm vụ
                selected_task = random.choice(task_item)
                planned_tasks.append(selected_task)
            elif isinstance(task_item, tuple):
                # Nếu là dạng (), xáo trộn thứ tự
                shuffled_tasks = list(task_item)
                random.shuffle(shuffled_tasks)
                planned_tasks.extend(shuffled_tasks)
            else:
                # Nhiệm vụ thông thường
                planned_tasks.append(task_item)

    logger.info(f"Chuỗi nhiệm vụ đã tạo: {planned_tasks}")
    return planned_tasks


async def regenerate_tasks_for_completed():
    """Tạo lại nhiệm vụ cho các ví đã hoàn thành"""
    try:
        db = Database()
        config = get_config()

        # Lấy danh sách ví đã hoàn thành
        completed_wallets = await db.get_completed_wallets()

        if not completed_wallets:
            logger.info("Không có ví nào đã hoàn thành")
            return

        print("\n[1] Có")
        print("[2] Không")
        confirmation = input(
            "\nThao tác này sẽ thay thế toàn bộ nhiệm vụ cho các ví đã hoàn thành. Tiếp tục? (1-2): "
        ).strip()

        if confirmation != "1":
            logger.info("Đã hủy thao tác tạo lại nhiệm vụ")
            return

        # Tạo lại nhiệm vụ cho từng ví đã hoàn thành
        for wallet in completed_wallets:
            # Генерируем новый список задач
            new_tasks = generate_tasks_from_config(config)

            # Очищаем старые задачи и добавляем новые
            await db.clear_wallet_tasks(wallet["private_key"])
            await db.add_tasks_to_wallet(wallet["private_key"], new_tasks)

        logger.success(
            f"Đã tạo lại nhiệm vụ cho {len(completed_wallets)} ví đã hoàn thành"
        )

    except Exception as e:
        logger.error(f"Lỗi khi tạo lại nhiệm vụ: {e}")


async def regenerate_tasks_for_all():
    """Tạo lại nhiệm vụ cho tất cả ví"""
    try:
        db = Database()
        config = get_config()

        # Lấy tất cả ví
        completed_wallets = await db.get_completed_wallets()
        uncompleted_wallets = await db.get_uncompleted_wallets()
        all_wallets = completed_wallets + uncompleted_wallets

        if not all_wallets:
            logger.info("Không có ví nào trong database")
            return

        print("\n[1] Có")
        print("[2] Không")
        confirmation = input(
            "\nThao tác này sẽ thay thế toàn bộ nhiệm vụ cho TẤT CẢ ví. Tiếp tục? (1-2): "
        ).strip()

        if confirmation != "1":
            logger.info("Đã hủy thao tác tạo lại nhiệm vụ")
            return

        # Tạo lại nhiệm vụ cho từng ví
        for wallet in all_wallets:
            # Генерируем новый список задач
            new_tasks = generate_tasks_from_config(config)

            # Очищаем старые задачи и добавляем новые
            await db.clear_wallet_tasks(wallet["private_key"])
            await db.add_tasks_to_wallet(wallet["private_key"], new_tasks)

        logger.success(f"Đã tạo lại nhiệm vụ cho tất cả {len(all_wallets)} ví")

    except Exception as e:
        logger.error(f"Lỗi khi tạo lại nhiệm vụ cho tất cả ví: {e}")


async def show_database_contents():
    """Hiển thị nội dung database dưới dạng bảng"""
    try:
        db = Database()

        # Lấy tất cả ví
        completed_wallets = await db.get_completed_wallets()
        uncompleted_wallets = await db.get_uncompleted_wallets()
        all_wallets = completed_wallets + uncompleted_wallets

        if not all_wallets:
            logger.info("Database trống")
            return

        # Chuẩn bị dữ liệu cho bảng
        table_data = []
        for wallet in all_wallets:
            tasks = (
                json.loads(wallet["tasks"])
                if isinstance(wallet["tasks"], str)
                else wallet["tasks"]
            )

            # Danh sách nhiệm vụ đã hoàn thành
            completed_tasks = [
                task["name"] for task in tasks if task["status"] == "completed"
            ]
            # Danh sách nhiệm vụ đang chờ
            pending_tasks = [
                task["name"] for task in tasks if task["status"] == "pending"
            ]

            # Rút gọn private key để hiển thị
            short_key = f"{wallet['private_key'][:6]}...{wallet['private_key'][-4:]}"

            # Rút gọn proxy để hiển thị
            proxy = wallet["proxy"]
            if proxy and len(proxy) > 20:
                proxy = f"{proxy[:17]}..."

            table_data.append(
                [
                    short_key,
                    proxy or "Không có proxy",
                    wallet["status"],
                    f"{len(completed_tasks)}/{len(tasks)}",
                    ", ".join(completed_tasks) or "Không có",
                    ", ".join(pending_tasks) or "Không có",
                ]
            )

        # Tạo bảng
        headers = [
            "Ví",
            "Proxy",
            "Trạng thái",
            "Tiến độ",
            "Nhiệm vụ đã hoàn thành",
            "Nhiệm vụ đang chờ",
        ]
        table = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")

        # Thống kê
        total_wallets = len(all_wallets)
        completed_count = len(completed_wallets)
        print(f"\nThống kê Database:")
        print(f"Tổng số ví: {total_wallets}")
        print(f"Ví đã hoàn thành: {completed_count}")
        print(f"Ví đang chờ: {total_wallets - completed_count}")

        # Hiển thị bảng
        print("\nNội dung Database:")
        print(table)

    except Exception as e:
        logger.error(f"Lỗi khi hiển thị nội dung database: {e}")


async def add_new_wallets():
    """Thêm các ví mới từ file vào database"""
    try:
        db = Database()
        config = get_config()

        # Đọc tất cả private key từ file
        private_keys = read_private_keys("data/private_keys.txt")

        # Đọc proxy
        try:
            proxy_objects = Proxy.from_file("data/proxies.txt")
            proxies = [proxy.get_default_format() for proxy in proxy_objects]
            if len(proxies) == 0:
                logger.error("Không tìm thấy proxy trong data/proxies.txt")
                return
        except Exception as e:
            logger.error(f"Lỗi khi tải proxy: {e}")
            return

        # Lấy các ví đã có trong database
        completed_wallets = await db.get_completed_wallets()
        uncompleted_wallets = await db.get_uncompleted_wallets()
        existing_wallets = {
            w["private_key"] for w in (completed_wallets + uncompleted_wallets)
        }

        # Tìm các ví mới
        new_wallets = [pk for pk in private_keys if pk not in existing_wallets]

        if not new_wallets:
            logger.info("Không có ví mới để thêm vào database")
            return

        print(f"\nTìm thấy {len(new_wallets)} ví mới để thêm vào database")
        print("\n[1] Có")
        print("[2] Không")
        confirmation = input("\nBạn có muốn thêm các ví này không? (1-2): ").strip()

        if confirmation != "1":
            logger.info("Đã hủy thao tác thêm ví mới")
            return

        # Thêm các ví mới
        added_count = 0
        for private_key in new_wallets:
            proxy = proxies[added_count % len(proxies)]
            tasks = generate_tasks_from_config(config)

            if not tasks:
                logger.error(
                    f"Không tạo được nhiệm vụ cho ví {private_key[:4]}...{private_key[-4:]}"
                )
                continue

            await db.add_wallet(
                private_key=private_key,
                proxy=proxy,
                tasks_list=tasks,
            )
            added_count += 1

        logger.success(f"Đã thêm thành công {added_count} ví mới vào database!")

    except Exception as e:
        logger.error(f"Lỗi khi thêm ví mới: {e}")
