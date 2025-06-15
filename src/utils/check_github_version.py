import aiohttp
import os
import json
from datetime import datetime
from typing import Tuple, Optional, List, Dict
from rich.console import Console
from rich.table import Table
from rich import box
import re

console = Console()


class VersionInfo:
    def __init__(self, VERSION: str, UPDATE_DATE: str, CHANGES: List[str]):
        self.version = VERSION
        self.update_date = UPDATE_DATE
        self.changes = CHANGES


async def fetch_versions_json(
    repo_owner: str, repo_name: str, proxy: Optional[str] = None
) -> List[VersionInfo]:
    """
    Lấy thông tin các phiên bản từ repository GitHub
    """
    url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/main/camp_network.json"
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7,zh-TW;q=0.6,zh;q=0.5,uk;q=0.4",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "referer": f"https://github.com/{repo_owner}/{repo_name}/blob/main/camp_network.json",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }

    proxy_url = None
    if proxy:
        proxy_url = f"http://{proxy}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy_url) as response:
                if response.status == 200:
                    data = await response.text()

                    # Làm sạch chuỗi JSON nhưng giữ lại dấu cách trong giá trị
                    data = re.sub(
                        r'"([^"]*)"', lambda m: m.group(0).replace(" ", "§"), data
                    )

                    data = data.replace(" ", "").replace("\n", "").replace("\t", "")
                    data = data.replace(",]", "]").replace(",}", "}")
                    while ",," in data:
                        data = data.replace(",,", ",")

                    data = data.replace("§", " ")

                    json_data = json.loads(data)
                    return [VersionInfo(**version) for version in json_data]
                else:
                    print("❌ Không thể lấy thông tin phiên bản từ GitHub")
                    if response.status == 403:
                        print("ℹ️ Giới hạn truy cập API GitHub hoặc bị từ chối")
                    elif response.status == 404:
                        print("ℹ️ Không tìm thấy file phiên bản")
                    print("\n💡 Bạn có thể thử dùng proxy bằng cách thêm vào main.py:")
                    print("   await check_version(VERSION, proxy='user:pass@ip:port')")
                    return []
    except aiohttp.ClientError as e:
        print(f"❌ Lỗi mạng khi lấy thông tin phiên bản: {e}")
        print("\n💡 Bạn có thể thử dùng proxy bằng cách thêm vào main.py:")
        print("   await check_version(VERSION, proxy='user:pass@ip:port')")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi khi phân tích dữ liệu phiên bản: {e}")
        print("ℹ️ Định dạng file phiên bản có thể không đúng")
        return []
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return []


def format_version_changes(versions: List[VersionInfo]) -> None:
    """
    Định dạng và hiển thị bảng thay đổi phiên bản ra màn hình
    """
    if not versions:
        return

    try:
        table = Table(
            show_header=True,
            box=box.DOUBLE,
            border_style="bright_cyan",
            pad_edge=False,
            width=85,
            highlight=True,
        )

        table.add_column("Phiên bản", style="cyan", justify="center")
        table.add_column("Ngày cập nhật", style="magenta", justify="center")
        table.add_column("Thay đổi", style="green")

        for i, version in enumerate(versions):
            changes_str = "\n".join(f"• {change}" for change in version.changes)
            table.add_row(
                f"✨ {version.version}", f"📅 {version.update_date}", changes_str
            )
            # Thêm dòng phân cách sau mỗi phiên bản trừ phiên bản cuối
            if i < len(versions) - 1:
                table.add_row("─" * 12, "─" * 21, "─" * 40, style="dim")

        print("📋 Các bản cập nhật có sẵn:")
        console.print(table)
        print()
    except Exception as e:
        print(f"❌ Lỗi khi hiển thị thông tin phiên bản: {e}")


async def check_version(
    current_version: str,
    repo_owner: str = "0xStarLabs",
    repo_name: str = "VersionsControl",
    proxy: Optional[str] = None,
) -> bool:
    """
    Kiểm tra phiên bản hiện tại đã mới nhất chưa
    """
    try:
        print("🔍 Đang kiểm tra cập nhật...")

        versions = await fetch_versions_json(repo_owner, repo_name, proxy)
        if not versions:
            return True

        # Sắp xếp các phiên bản theo số phiên bản
        versions.sort(key=lambda x: [int(n) for n in x.version.split(".")])
        latest_version = versions[-1]

        current_version_parts = [int(n) for n in current_version.split(".")]
        latest_version_parts = [int(n) for n in latest_version.version.split(".")]

        if current_version_parts < latest_version_parts:
            print(f"⚠️ Có phiên bản mới: {latest_version.version}")
            format_version_changes(versions)
            return False

        print(f"✅ Bạn đang sử dụng phiên bản mới nhất ({current_version})")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra phiên bản: {e}")
        return True  # Trả về True để chương trình tiếp tục chạy
