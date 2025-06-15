from functools import wraps
import asyncio
from typing import TypeVar, Callable, Any, Optional
from loguru import logger
from src.utils.config import get_config

T = TypeVar("T")


# @retry_async(attempts=3, default_value=False)
# async def deploy_contract(self):
#     try:
#         # mã triển khai hợp đồng của bạn
#         return True
#     except Exception as e:
#         # xử lý lỗi của bạn với thời gian tạm dừng
#         await asyncio.sleep(your_pause)
#         raise  # trả quyền kiểm soát về cho decorator để thử lại lần tiếp theo
#
# @retry_async(default_value=False)
# async def some_function():
#     ...

def retry_async(
    attempts: int = None,  # Số lần thử lại (tùy chọn)
    delay: float = 1.0,
    backoff: float = 2.0,
    default_value: Any = None,
):
    """
    Decorator bất đồng bộ để thử lại với backoff lũy tiến.
    Nếu không truyền attempts, sẽ lấy SETTINGS.ATTEMPTS từ config.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Lấy số lần thử lại từ config nếu không truyền vào
            retry_attempts = attempts if attempts is not None else get_config().SETTINGS.ATTEMPTS
            current_delay = delay

            for attempt in range(retry_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < retry_attempts - 1:  # Không tạm dừng ở lần thử cuối cùng
                        logger.warning(
                            f"Lần thử {attempt + 1}/{retry_attempts} thất bại cho hàm {func.__name__}: {str(e)}. "
                            f"Thử lại sau {current_delay:.1f} giây..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Tất cả {retry_attempts} lần thử đều thất bại cho hàm {func.__name__}: {str(e)}"
                        )
                        raise e  # Ném lại exception cuối cùng

            return default_value

        return wrapper

    return decorator
