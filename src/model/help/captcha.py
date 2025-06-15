import asyncio
from loguru import logger
from primp import AsyncClient
import requests
from typing import Optional, Dict
from enum import Enum
import time
import base64


class CaptchaError(Exception):
    """Ngoại lệ cơ bản cho các lỗi captcha"""

    pass


class ErrorCodes(Enum):
    ERROR_WRONG_USER_KEY = "ERROR_WRONG_USER_KEY"
    ERROR_KEY_DOES_NOT_EXIST = "ERROR_KEY_DOES_NOT_EXIST"
    ERROR_ZERO_BALANCE = "ERROR_ZERO_BALANCE"
    ERROR_PAGEURL = "ERROR_PAGEURL"
    IP_BANNED = "IP_BANNED"
    ERROR_PROXY_FORMAT = "ERROR_PROXY_FORMAT"
    ERROR_BAD_PARAMETERS = "ERROR_BAD_PARAMETERS"
    ERROR_BAD_PROXY = "ERROR_BAD_PROXY"
    ERROR_SITEKEY = "ERROR_SITEKEY"
    CAPCHA_NOT_READY = "CAPCHA_NOT_READY"
    ERROR_CAPTCHA_UNSOLVABLE = "ERROR_CAPTCHA_UNSOLVABLE"
    ERROR_WRONG_CAPTCHA_ID = "ERROR_WRONG_CAPTCHA_ID"
    ERROR_EMPTY_ACTION = "ERROR_EMPTY_ACTION"


class Capsolver:
    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        session: AsyncClient = None,
    ):
        self.api_key = api_key
        self.base_url = "https://api.capsolver.com"
        self.proxy = self._format_proxy(proxy) if proxy else None
        self.session = session or AsyncClient(verify=False)

    def _format_proxy(self, proxy: str) -> str:
        if not proxy:
            return None
        if "@" in proxy:
            return proxy
        return proxy

    async def create_task(
        self,
        sitekey: str,
        pageurl: str,
        invisible: bool = False,
    ) -> Optional[str]:
        """Tạo task giải captcha"""
        data = {
            "clientKey": self.api_key,
            "appId": "0F6B2D90-7CA4-49AC-B0D3-D32C70238AD8",
            "task": {
                "type": "ReCaptchaV2Task",
                "websiteURL": pageurl,
                "websiteKey": sitekey,
                "isInvisible": False,
            },
        }

        if self.proxy:
            data["task"]["proxy"] = self.proxy

        try:
            response = await self.session.post(
                f"{self.base_url}/createTask",
                json=data,
                timeout=30,
            )
            result = response.json()

            if "taskId" in result:
                return result["taskId"]

            logger.error(f"Lỗi khi tạo task captcha: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi tạo task captcha: {e}")
            return None

    async def get_task_result(self, task_id: str) -> Optional[str]:
        """Lấy kết quả giải captcha"""
        data = {"clientKey": self.api_key, "taskId": task_id}

        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = await self.session.post(
                    f"{self.base_url}/getTaskResult",
                    json=data,
                    timeout=30,
                )
                result = response.json()

                if result.get("status") == "ready":
                    solution = result.get("solution", {})
                    return solution.get("token") or solution.get("gRecaptchaResponse")
                elif "errorId" in result and result["errorId"] != 0:
                    logger.error(f"Lỗi khi lấy kết quả: {result}")
                    return None

                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Lỗi khi lấy kết quả: {e}")
                return None

        return None

    async def create_recaptcha_v3_task(
        self,
        sitekey: str,
        pageurl: str,
        page_action: str,
        enterprise: bool = False,
        enterprise_payload: Optional[Dict] = None,
        is_session: bool = False,
        api_domain: Optional[str] = None,
    ) -> Optional[str]:
        """Tạo task giải reCAPTCHA v3"""
        task_type = "ReCaptchaV3EnterpriseTask" if enterprise else "ReCaptchaV3Task"
        if not self.proxy:
            task_type += "ProxyLess"

        data = {
            "clientKey": self.api_key,
            "task": {
                "type": task_type,
                "websiteURL": pageurl,
                "websiteKey": sitekey,
                "pageAction": page_action,
            },
        }

        if enterprise_payload:
            data["task"]["enterprisePayload"] = enterprise_payload
        if is_session:
            data["task"]["isSession"] = True
        if api_domain:
            data["task"]["apiDomain"] = api_domain
        if self.proxy:
            data["task"]["proxy"] = self.proxy

        try:
            response = await self.session.post(
                f"{self.base_url}/createTask",
                json=data,
                timeout=30,
            )
            result = response.json()

            if "taskId" in result:
                return result["taskId"]

            logger.error(f"Lỗi khi tạo task reCAPTCHA v3: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi tạo task reCAPTCHA v3: {e}")
            return None

    async def solve_recaptcha(
        self,
        sitekey: str,
        pageurl: str,
        page_action: str = "verify",
        enterprise: bool = False,
        enterprise_payload: Optional[Dict] = None,
        is_session: bool = False,
        api_domain: Optional[str] = None,
    ) -> Optional[str]:
        """Giải reCAPTCHA v3 và trả về token"""
        task_id = await self.create_recaptcha_v3_task(
            sitekey=sitekey,
            pageurl=pageurl,
            page_action=page_action,
            enterprise=enterprise,
            enterprise_payload=enterprise_payload,
            is_session=is_session,
            api_domain=api_domain,
        )
        if not task_id:
            return None

        return await self.get_task_result(task_id)

    async def create_turnstile_task(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
    ) -> Optional[str]:
        """Tạo task giải captcha Turnstile"""
        data = {
            "clientKey": self.api_key,
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": pageurl,
                "websiteKey": sitekey,
            },
        }

        try:
            response = await self.session.post(
                f"{self.base_url}/createTask",
                json=data,
                timeout=30,
            )
            result = response.json()

            if "taskId" in result:
                return result["taskId"]

            logger.error(f"Lỗi khi tạo task Turnstile: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi tạo task Turnstile: {e}")
            return None

    async def solve_turnstile(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
    ) -> Optional[str]:
        """Giải captcha Cloudflare Turnstile và trả về token"""
        task_id = await self.create_turnstile_task(
            sitekey=sitekey,
            pageurl=pageurl,
            action=action,
            cdata=cdata,
        )
        if not task_id:
            return None

        return await self.get_task_result(task_id)


class TwoCaptcha:
    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        session: AsyncClient = None,
    ):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.proxy = self._format_proxy(proxy) if proxy else None
        self.session = session or AsyncClient(verify=False)

    def _format_proxy(self, proxy: str) -> str:
        if not proxy:
            return None
        if "@" in proxy:
            return proxy
        return proxy

    async def create_turnstile_task(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        data: Optional[str] = None,
        pagedata: Optional[str] = None,
    ) -> Optional[str]:
        """Tạo task giải captcha Turnstile"""
        form_data = {
            "key": self.api_key,
            "method": "turnstile",
            "sitekey": sitekey,
            "pageurl": pageurl,
            "json": "1",
        }

        if action:
            form_data["action"] = action
        if data:
            form_data["data"] = data
        if pagedata:
            form_data["pagedata"] = pagedata
        if self.proxy:
            form_data["proxy"] = self.proxy

        try:
            response = await self.session.post(
                f"{self.base_url}/in.php",
                data=form_data,
                timeout=30,
            )
            result = response.json()

            if result.get("status") == 1:
                return result["request"]

            logger.error(f"Lỗi khi tạo task Turnstile: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi tạo task Turnstile: {e}")
            return None

    async def get_task_result(self, task_id: str) -> Optional[str]:
        """Lấy kết quả giải captcha"""
        params = {
            "key": self.api_key,
            "action": "get",
            "id": task_id,
            "json": "1",
        }

        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = await self.session.get(
                    f"{self.base_url}/res.php",
                    params=params,
                    timeout=30,
                )
                result = response.json()

                if result.get("status") == 1:
                    return result["request"]
                elif result.get("request") == "CAPCHA_NOT_READY":
                    await asyncio.sleep(5)
                    continue

                logger.error(f"Lỗi khi lấy kết quả: {result}")
                return None

            except Exception as e:
                logger.error(f"Lỗi khi lấy kết quả: {e}")
                return None

        return None

    async def solve_turnstile(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        data: Optional[str] = None,
        pagedata: Optional[str] = None,
    ) -> Optional[str]:
        """Giải captcha Cloudflare Turnstile và trả về token"""
        task_id = await self.create_turnstile_task(
            sitekey=sitekey,
            pageurl=pageurl,
            action=action,
            data=data,
            pagedata=pagedata,
        )
        if not task_id:
            return None

        return await self.get_task_result(task_id)


class TwoCaptchaEnterprise:
    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        session: AsyncClient = None,
    ):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.proxy = self._format_proxy(proxy) if proxy else None
        self.session = session or AsyncClient(verify=False)

    def _format_proxy(self, proxy: str) -> str:
        if not proxy:
            return None
        if "@" in proxy:
            return proxy
        return proxy

    async def create_enterprise_task(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> Optional[str]:
        """Tạo task giải reCAPTCHA Enterprise"""
        form_data = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "enterprise": "1",
            "googlekey": sitekey,
            "pageurl": pageurl,
            "json": "1",
        }

        if action:
            form_data["action"] = action
        if min_score:
            form_data["min_score"] = str(min_score)
        if self.proxy:
            form_data["proxy"] = self.proxy

        try:
            response = await self.session.post(
                f"{self.base_url}/in.php",
                data=form_data,
                timeout=30,
            )
            result = response.json()

            if result.get("status") == 1:
                return result["request"]

            logger.error(f"Lỗi khi tạo task Enterprise: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi tạo task Enterprise: {e}")
            return None

    async def get_task_result(self, task_id: str) -> Optional[str]:
        """Lấy kết quả giải captcha"""
        params = {
            "key": self.api_key,
            "action": "get",
            "id": task_id,
            "json": "1",
        }

        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = await self.session.get(
                    f"{self.base_url}/res.php",
                    params=params,
                    timeout=30,
                )
                result = response.json()

                if result.get("status") == 1:
                    return result["request"]
                elif result.get("request") == "CAPCHA_NOT_READY":
                    await asyncio.sleep(5)
                    continue

                logger.error(f"Lỗi khi lấy kết quả: {result}")
                return None

            except Exception as e:
                logger.error(f"Lỗi khi lấy kết quả: {e}")
                return None

        return None

    async def solve_enterprise(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> Optional[str]:
        """Giải reCAPTCHA Enterprise và trả về token"""
        task_id = await self.create_enterprise_task(
            sitekey=sitekey,
            pageurl=pageurl,
            action=action,
            min_score=min_score,
        )
        if not task_id:
            return None

        return await self.get_task_result(task_id)


class NoCaptcha:
    def __init__(
        self,
        user_token: str,
        proxy: Optional[str] = None,
        session: AsyncClient = None,
    ):
        self.user_token = user_token
        self.base_url = "http://api.nocaptcha.io"
        self.proxy = self._format_proxy(proxy) if proxy else None
        self.session = session or AsyncClient(verify=False)

    def _format_proxy(self, proxy: str) -> str:
        if not proxy:
            return None
        if "@" in proxy:
            return proxy
        return proxy

    async def solve_hcaptcha(
        self,
        sitekey: str,
        referer: str,
        rqdata: Optional[str] = None,
        domain: Optional[str] = None,
        region: Optional[str] = None,
        invisible: bool = False,
        need_ekey: bool = False,
    ) -> Optional[Dict]:
        """Giải hCaptcha và trả về dữ liệu giải"""
        data = {
            "sitekey": sitekey,
            "referer": referer,
            "invisible": invisible,
            "need_ekey": need_ekey,
        }

        if rqdata:
            data["rqdata"] = rqdata
        if domain:
            data["domain"] = domain
        if self.proxy:
            data["proxy"] = self.proxy
            if region:
                data["region"] = region

        headers = {
            "User-Token": self.user_token,
            "Content-Type": "application/json",
            "Developer-Id": "SWVtru",
        }

        try:
            response = await self.session.post(
                f"{self.base_url}/api/wanda/hcaptcha/universal",
                json=data,
                headers=headers,
                timeout=30,
            )
            result = response.json()

            if result.get("status") == 1:
                return result.get("data")

            logger.error(f"Lỗi khi giải hCaptcha: {result}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi giải hCaptcha: {e}")
            return None


class Solvium:
    def __init__(
        self,
        api_key: str,
        session: AsyncClient,
        proxy: Optional[str] = None,
    ):
        self.api_key = api_key
        self.proxy = proxy
        self.base_url = "https://captcha.solvium.io/api/v1"
        self.session = session

    def _format_proxy(self, proxy: str) -> str:
        if not proxy:
            return None
        if "@" in proxy:
            return proxy
        return f"http://{proxy}"

    async def create_hcaptcha_task(self, sitekey: str, pageurl: str) -> Optional[str]:
        """Tạo task giải captcha Turnstile"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        url = (
            f"{self.base_url}/task/noname?url={pageurl}&sitekey={sitekey}&ref=starlabs"
        )

        try:
            response = await self.session.get(url, headers=headers, timeout=30)
            result = response.json()

            if result.get("message") == "Task created" and "task_id" in result:
                return result["task_id"]

            if "'Unauthorized'}" in str(result):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None

            logger.error(f"Lỗi khi tạo task Turnstile với Solvium: {result}")
            return None

        except Exception as e:
            if "'Unauthorized'}" in str(e):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None
            logger.error(f"Lỗi khi tạo task Turnstile với Solvium: {e}")
            return None

    async def create_turnstile_task(self, challenge_token: str) -> Optional[str]:
        """Tạo task giải captcha Turnstile"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = await self.session.get(
                f"{self.base_url}/task/vercel/",
                params={"challengeToken": challenge_token},
                headers=headers,
                timeout=30,
            )
            result = response.json()

            if "task_id" in result:
                return result["task_id"]

            if "'Unauthorized'}" in str(result):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None

            logger.error(f"Lỗi khi tạo task Turnstile với Solvium: {result}")
            return None

        except Exception as e:
            if "'Unauthorized'}" in str(e):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None
            logger.error(f"Lỗi khi tạo task Turnstile với Solvium: {e}")
            return None

    async def get_task_result(self, task_id: str) -> Optional[str]:
        """Lấy kết quả giải captcha"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = await self.session.get(
                    f"{self.base_url}/task/status/{task_id}",
                    headers=headers,
                    timeout=30,
                )

                result = response.json()

                # Проверяем статус задачи
                if (
                    result.get("status") == "completed"
                    and result.get("result")
                    and result["result"].get("solution")
                ):
                    solution = result["result"]["solution"]

                    return solution

                elif (
                    result.get("status") == "running"
                    or result.get("status") == "pending"
                ):
                    # Задача еще выполняется, ждем
                    await asyncio.sleep(5)
                    continue
                else:
                    # Ошибка или неизвестный статус
                    logger.error(f"Lỗi khi lấy kết quả với Solvium: {result}")
                    return None

            except Exception as e:
                logger.error(f"Lỗi khi lấy kết quả với Solvium: {e}")
                return None

        logger.error(
            "Đã đạt tối đa số lần kiểm tra mà không nhận được kết quả với Solvium"
        )
        return None

    async def solve_captcha(self, sitekey: str, pageurl: str) -> Optional[str]:
        """Giải captcha Cloudflare Turnstile và trả về token"""
        task_id = await self.create_hcaptcha_task(sitekey, pageurl)
        if not task_id:
            return None

        return await self.get_task_result(task_id)

    async def solve_turnstile(self, challenge_token: str) -> Optional[str]:
        """Giải captcha Cloudflare Turnstile và trả về token"""
        task_id = await self.create_turnstile_task(challenge_token)
        if not task_id:
            return None

        return await self.get_task_result(task_id)

    async def solve_vercel_challenge(
        self, challenge_token: str, site_url: str, session
    ) -> Optional[str]:
        """Giải Vercel challenge và trả về giá trị cookie"""
        # Bước 1: Giải challenge
        solution = await self.solve_turnstile(challenge_token)
        if not solution:
            return None

        return solution

    async def create_cf_clearance_task(
        self, pageurl: str, body_b64: str, proxy: str
    ) -> Optional[str]:
        """Tạo task giải captcha Cloudflare clearance"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        url = f"{self.base_url}/task/cf-clearance"

        json_data = {
            "url": pageurl,
            "body": body_b64,
            "proxy": "http://" + proxy,
        }

        try:
            response = await self.session.post(
                url,
                headers=headers,
                json=json_data,
                timeout=30,
            )
            result = response.json()

            if result.get("message") == "Task created" and "task_id" in result:
                return result["task_id"]

            if "'Unauthorized'}" in str(result):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None

            logger.error(f"Lỗi khi tạo task CF clearance với Solvium: {result}")
            return None

        except Exception as e:
            if "'Unauthorized'}" in str(e):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None
            logger.error(f"Lỗi khi tạo task CF clearance với Solvium: {e}")
            return None

    async def create_recaptcha_v3_task(
        self, sitekey: str, pageurl: str, action: str, enterprise: bool = False
    ) -> Optional[str]:
        """Tạo task giải Recaptcha V3"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        url = f"{self.base_url}/task/"
        params = {
            "url": pageurl,
            "sitekey": sitekey,
            "action": action,
        }

        if enterprise:
            params["enterprise"] = "true"

        try:
            response = await self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
            )
            result = response.json()

            if result.get("message") == "Task created" and "task_id" in result:
                return result["task_id"]

            if "'Unauthorized'}" in str(result):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None

            logger.error(f"Lỗi khi tạo task Recaptcha V3 với Solvium: {result}")
            return None

        except Exception as e:
            if "'Unauthorized'}" in str(e):
                logger.error(f"Bạn cần thiết lập API key trong file config.yaml.")
                return None
            logger.error(f"Lỗi khi tạo task Recaptcha V3 với Solvium: {e}")
            return None

    async def solve_recaptcha_v3(
        self, sitekey: str, pageurl: str, action: str, enterprise: bool = False
    ) -> Optional[str]:
        """Giải reCAPTCHA v3 và trả về token"""
        task_id = await self.create_recaptcha_v3_task(
            sitekey=sitekey,
            pageurl=pageurl,
            action=action,
            enterprise=enterprise,
        )
        if not task_id:
            return None

        return await self.get_task_result(task_id)

    async def solve_cf_clearance(
        self, pageurl: str, body_b64: str, proxy: str
    ) -> Optional[str]:
        """Giải Cloudflare clearance challenge và trả về giá trị cookie cf_clearance"""
        task_id = await self.create_cf_clearance_task(pageurl, body_b64, proxy)
        if not task_id:
            return None

        return await self.get_task_result(task_id)
