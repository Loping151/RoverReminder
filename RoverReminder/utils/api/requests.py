import asyncio
import json
from typing import Any, Dict, Optional, Union

import httpx

from gsuid_core.logger import logger

from ..constants import WAVES_GAME_ID
from ..database.models import WavesUser
from .api import BASE_DATA_URL, GAME_DATA_URL, LOGIN_LOG_URL, REFRESH_URL, REQUEST_TOKEN, SERVER_ID, SERVER_ID_NET
from .request_util import KuroApiResp, get_base_header


class WavesApi:
    ssl_verify = True

    def is_net(self, role_id: str) -> bool:
        try:
            return int(role_id) >= 200000000
        except Exception:
            return False

    def get_server_id(self, role_id: str, server_id: Optional[str] = None) -> str:
        if server_id:
            return server_id
        return SERVER_ID_NET if self.is_net(role_id) else SERVER_ID

    async def refresh_bat_token(self, waves_user: WavesUser) -> Optional[WavesUser]:
        success, access_token = await self.get_request_token(
            waves_user.uid,
            waves_user.cookie,
            waves_user.did,
        )
        if not success:
            return None

        waves_user.bat = access_token
        await WavesUser.update_data_by_data(
            select_data={
                "uid": waves_user.uid,
                "game_id": waves_user.game_id,
            },
            update_data={"bat": access_token},
        )
        return waves_user

    async def get_used_headers(
        self,
        cookie: str,
        uid: str,
        need_token: bool = False,
        game_id: Optional[int] = WAVES_GAME_ID,
    ) -> Dict[str, Any]:
        headers: Dict[str, Any] = {"did": "", "b-at": ""}
        if need_token:
            headers["token"] = cookie
        waves_user = await WavesUser.select_data_by_cookie_and_uid(
            cookie=cookie,
            uid=uid,
            game_id=game_id,
        ) or await WavesUser.select_data_by_cookie(cookie=cookie)

        if not waves_user:
            return headers

        headers["did"] = waves_user.did or ""
        headers["b-at"] = waves_user.bat or ""
        return headers

    async def get_self_waves_ck(self, uid: str, user_id: str, bot_id: str) -> Optional[str]:
        waves_user = await WavesUser.select_waves_user(uid, user_id, bot_id, game_id=WAVES_GAME_ID)
        if not waves_user or not waves_user.cookie:
            return ""

        if waves_user.status == "无效":
            return ""

        data = await self.login_log(uid, waves_user.cookie)
        if not data.success:
            await data.mark_cookie_invalid(uid, waves_user.cookie)
            return ""

        data = await self.refresh_data(uid, waves_user.cookie)
        if not data.success:
            if data.is_bat_token_invalid:
                waves_user = await self.refresh_bat_token(waves_user)
                if waves_user:
                    await WavesUser.update_last_used_time(uid, user_id, bot_id, game_id=WAVES_GAME_ID)
                    return waves_user.cookie
            else:
                await data.mark_cookie_invalid(uid, waves_user.cookie)
            return ""

        await WavesUser.update_last_used_time(uid, user_id, bot_id, game_id=WAVES_GAME_ID)
        return waves_user.cookie

    async def get_request_token(
        self,
        role_id: str,
        token: str,
        did: str,
        server_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        header = await get_base_header()
        header.update({"token": token, "did": did, "b-at": ""})
        data = {
            "serverId": self.get_server_id(role_id, server_id),
            "roleId": role_id,
        }
        raw_data = await self._waves_request(REQUEST_TOKEN, "POST", header, data=data)
        if raw_data.success and isinstance(raw_data.data, dict):
            access_token = raw_data.data.get("accessToken", "")
            if access_token:
                return True, access_token
        return False, ""

    async def get_daily_info(self, role_id: str, token: str):
        header = await get_base_header()
        used_headers = await self.get_used_headers(
            cookie=token,
            uid=role_id,
            need_token=True,
            game_id=WAVES_GAME_ID,
        )
        header.update(used_headers)
        data = {
            "type": "2",
            "sizeType": "1",
            "gameId": WAVES_GAME_ID,
            "serverId": self.get_server_id(role_id),
            "roleId": role_id,
        }
        return await self._waves_request(GAME_DATA_URL, "POST", header, data=data)

    async def get_base_info(self, role_id: str, token: str, server_id: Optional[str] = None):
        header = await get_base_header()
        used_headers = await self.get_used_headers(cookie=token, uid=role_id, game_id=WAVES_GAME_ID)
        header.update(used_headers)
        data = {
            "gameId": WAVES_GAME_ID,
            "serverId": self.get_server_id(role_id, server_id),
            "roleId": role_id,
        }
        return await self._waves_request(BASE_DATA_URL, "POST", header, data=data)

    async def refresh_data(self, role_id: str, token: str, server_id: Optional[str] = None):
        header = await get_base_header()
        used_headers = await self.get_used_headers(cookie=token, uid=role_id, game_id=WAVES_GAME_ID)
        header.update(used_headers)
        data = {
            "gameId": WAVES_GAME_ID,
            "serverId": self.get_server_id(role_id, server_id),
            "roleId": role_id,
        }
        return await self._waves_request(REFRESH_URL, "POST", header, data=data)

    async def login_log(self, role_id: str, token: str):
        header = await get_base_header()
        used_headers = await self.get_used_headers(cookie=token, uid=role_id, game_id=WAVES_GAME_ID)
        header.update(
            {
                "token": token,
                "devCode": used_headers.get("did", ""),
            }
        )
        return await self._waves_request(LOGIN_LOG_URL, "POST", header, data={})

    async def _waves_request(
        self,
        url: str,
        method: str = "GET",
        header: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> KuroApiResp[Union[str, Dict[str, Any]]]:
        if header is None:
            header = await get_base_header()

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(verify=self.ssl_verify, timeout=10) as client:
                    resp = await client.request(
                        method,
                        url,
                        headers=header,
                        params=params,
                        json=json_data,
                        data=data,
                    )
                try:
                    raw_data = resp.json()
                except Exception:
                    raw_data = {"code": -999, "data": resp.text}

                if isinstance(raw_data, dict):
                    try:
                        raw_data["data"] = json.loads(raw_data.get("data", ""))
                    except Exception:
                        pass
                logger.debug(
                    f"url:[{url}] params:[{params}] headers:[{header}] data:[{data}] raw_data:{raw_data}"
                )
                return KuroApiResp[Any].model_validate(raw_data)
            except Exception as e:
                logger.exception(f"url:[{url}] attempt {attempt + 1} failed", e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        return KuroApiResp[Any].err("请求服务器失败，已达最大重试次数", code=-999)


waves_api = WavesApi()
