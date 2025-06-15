from tabulate import tabulate
from loguru import logger
import pandas as pd
from datetime import datetime
import os

from src.utils.config import Config, WalletInfo


def print_wallets_stats(config: Config, excel_path="data/progress.xlsx"):
    """
    In thống kê tất cả ví dưới dạng bảng và lưu vào file Excel

    Args:
        config: Cấu hình chứa dữ liệu ví
        excel_path: Đường dẫn lưu file Excel (mặc định "data/progress.xlsx")
    """
    try:
        # Sắp xếp các ví theo chỉ số
        sorted_wallets = sorted(config.WALLETS.wallets, key=lambda x: x.account_index)

        # Chuẩn bị dữ liệu cho bảng
        table_data = []
        total_balance = 0
        total_transactions = 0

        for wallet in sorted_wallets:
            # Ẩn khóa riêng (5 ký tự cuối)
            masked_key = "•" * 3 + wallet.private_key[-5:]

            total_balance += wallet.balance
            total_transactions += wallet.transactions

            row = [
                str(wallet.account_index),  # Chỉ số ví không có số 0 đứng đầu
                wallet.address,  # Địa chỉ đầy đủ
                masked_key,
                f"{wallet.balance:.4f} CAMP",
                f"{wallet.transactions:,}",  # Định dạng số có dấu phân cách
            ]
            table_data.append(row)

        # Nếu có dữ liệu - in bảng và thống kê
        if table_data:
            # Tạo tiêu đề cho bảng
            headers = [
                "STT",
                "Địa chỉ ví",
                "Private Key",
                "Số dư (CAMP)",
                "Tổng giao dịch",
            ]

            # Tạo bảng với định dạng đẹp hơn
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="double_grid",  # Đường viền đẹp hơn
                stralign="center",       # Căn giữa chuỗi
                numalign="center",       # Căn giữa số
            )

            # Tính giá trị trung bình
            wallets_count = len(sorted_wallets)
            avg_balance = total_balance / wallets_count
            avg_transactions = total_transactions / wallets_count

            # In bảng và thống kê
            logger.info(
                f"\n{'='*50}\n"
                f"         Thống kê ví ({wallets_count} ví)\n"
                f"{'='*50}\n"
                f"{table}\n"
                f"{'='*50}\n"
                f"{'='*50}"
            )

            logger.info(f"Số dư trung bình: {avg_balance:.4f} CAMP")
            logger.info(f"Số giao dịch trung bình: {avg_transactions:.1f}")
            logger.info(f"Tổng số dư: {total_balance:.4f} CAMP")
            logger.info(f"Tổng số giao dịch: {total_transactions:,}")

            # Xuất ra Excel
            # Tạo DataFrame cho Excel
            df = pd.DataFrame(table_data, columns=headers)

            # Thêm thống kê tổng hợp
            summary_data = [
                ["", "", "", "", ""],
                ["TÓM TẮT", "", "", "", ""],
                [
                    "Tổng",
                    f"{wallets_count} ví",
                    "",
                    f"{total_balance:.4f} CAMP",
                    f"{total_transactions:,}",
                ],
                [
                    "Trung bình",
                    "",
                    "",
                    f"{avg_balance:.4f} CAMP",
                    f"{avg_transactions:.1f}",
                ],
            ]
            summary_df = pd.DataFrame(summary_data, columns=headers)
            df = pd.concat([df, summary_df], ignore_index=True)

            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)

            # Đặt tên file theo định dạng ngày giờ
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"progress_{timestamp}.xlsx"
            file_path = os.path.join(os.path.dirname(excel_path), filename)

            # Lưu vào Excel
            df.to_excel(file_path, index=False)
            logger.info(f"Đã xuất thống kê ra {file_path}")
        else:
            logger.info("\nKhông có thống kê ví nào")

    except Exception as e:
        logger.error(f"Lỗi khi in thống kê: {e}")
