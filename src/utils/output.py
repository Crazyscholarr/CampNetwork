import os
from rich.console import Console
from rich.text import Text
from tabulate import tabulate
from rich.table import Table
from rich import box


def show_logo():
    """Отображает стильный логотип STARLABS"""
    
    os.system("cls" if os.name == "nt" else "clear")

    console = Console()
    logo_text = """

 ▄████▄   ██▀███   ▄▄▄      ▒███████▒▓██   ██▓  ██████  ▄████▄   ██░ ██  ▒█████   ██▓    ▄▄▄       ██▀███  
▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▒ ▒ ▒ ▄▀░ ▒██  ██▒▒██    ▒ ▒██▀ ▀█  ▓██░ ██▒▒██▒  ██▒▓██▒   ▒████▄    ▓██ ▒ ██▒
▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ░ ▒ ▄▀▒░   ▒██ ██░░ ▓██▄   ▒▓█    ▄ ▒██▀▀██░▒██░  ██▒▒██░   ▒██  ▀█▄  ▓██ ░▄█ ▒
▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██   ▄▀▒   ░  ░ ▐██▓░  ▒   ██▒▒▓▓▄ ▄██▒░▓█ ░██ ▒██   ██░▒██░   ░██▄▄▄▄██ ▒██▀▀█▄  
▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒███████▒  ░ ██▒▓░▒██████▒▒▒ ▓███▀ ░░▓█▒░██▓░ ████▓▒░░██████▒▓█   ▓██▒░██▓ ▒██▒
░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▒▒ ▓░▒░▒   ██▒▒▒ ▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░ ▒ ░░▒░▒░ ▒░▒░▒░ ░ ▒░▓  ░▒▒   ▓▒█░░ ▒▓ ░▒▓░
  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░░░▒ ▒ ░ ▒ ▓██ ░▒░ ░ ░▒  ░ ░  ░  ▒    ▒ ░▒░ ░  ░ ▒ ▒░ ░ ░ ▒  ░ ▒   ▒▒ ░  ░▒ ░ ▒░
░          ░░   ░   ░   ▒   ░ ░ ░ ░ ░ ▒ ▒ ░░  ░  ░  ░  ░         ░  ░░ ░░ ░ ░ ▒    ░ ░    ░   ▒     ░░   ░ 
░ ░         ░           ░  ░  ░ ░     ░ ░           ░  ░ ░       ░  ░  ░    ░ ░      ░  ░     ░  ░   ░     
░                           ░         ░ ░              ░                                                   
"""

    
    gradient_logo = Text(logo_text)
    gradient_logo.stylize("bold bright_cyan")

    
    console.print(gradient_logo)
    print()


def show_dev_info():
    """Displays development and version information"""
    console = Console()

    
    table = Table(
        show_header=False,
        box=box.DOUBLE,
        border_style="bright_cyan",
        pad_edge=False,
        width=85,
        highlight=True,
    )

    
    table.add_column("Content", style="bright_cyan", justify="center")

    
    table.add_row("✨  CampNetwork Bot ✨")
    table.add_row("─" * 43)
    table.add_row("")
    table.add_row("⚡ GitHub: [link]https://github.com/Crazyscholarr[/link]")
    table.add_row("👤 Nhà phát triển: [link]https://web.telegram.org/k/#@Crzscholar[/link]")
    table.add_row("💬 Nhóm chat: [link]https://web.telegram.org/k/#@dgpubchat[/link]")
    table.add_row("")
    print("   ", end="")
    print()
    console.print(table)
    print()
