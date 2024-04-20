#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from hashlib import sha256
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel, constr, field_validator


class HashicorpResult(BaseModel):
    errors: Optional[List[str]] = None


class HashicorpAuth(BaseModel):
    vault_addr: str
    role_id: str
    secret_id: str
    access_token: Optional[str] = None

    async def get_token(self) -> str:
        if self.access_token:
            return self.access_token

        url = f"{self.vault_addr}/v1/auth/approle/login"
        payload = {"role_id": self.role_id, "secret_id": self.secret_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.text()

        class Auth(BaseModel):
            client_token: str

        class Data(HashicorpResult):
            auth: Optional[Auth] = None

        v = Data.model_validate_json(data)
        if v.errors:
            raise ValueError(v.errors)
        self.access_token = v.auth.client_token
        return self.access_token

    @field_validator("vault_addr", mode="before")
    @classmethod
    def check_vault_addr(cls, vault_addr: str) -> str:
        vault_addr = vault_addr or os.environ["VAULT_ADDR"]
        return vault_addr.rstrip("/")


class HashicorpVaultSecrets(BaseModel):
    auth: HashicorpAuth
    user_name: constr(min_length=1)
    uid: Optional[str] = None

    async def create_user(self) -> HashicorpAuth:
        """Admin tool, create user.

        Returns:

        """
        self.uid = self.format_user_name(self.user_name)
        await self._create_kv_secret_engine()
        await self._create_policy()
        await self._create_approle()
        role_id = await self._get_role_id()
        secret_id = await self._get_secret_id()
        return HashicorpAuth(vault_addr=self.auth.vault_addr, role_id=role_id, secret_id=secret_id)

    @staticmethod
    def format_user_name(user_name):
        hashed = sha256(user_name.encode()).hexdigest()
        return f"u{hashed[:8]}"

    async def _create_kv_secret_engine(self):
        url = f"{self.auth.vault_addr}/v1/sys/mounts/{self.uid}"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        payload = {"type": "kv", "options": {"version": "2"}}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    return
                data = await response.text()
                result = HashicorpResult.model_validate_json(data)
                raise ValueError(result.errors)

    async def _create_policy(self):
        url = f"{self.auth.vault_addr}/v1/sys/policies/acl/{self.uid}-secret-policy"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        path = f'path "{self.uid}/data/*"'
        acl = '{ capabilities = ["create", "read", "update", "delete", "list"] }'
        payload = {"policy": f"{path} {acl}"}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    return
                data = await response.text()
                result = HashicorpResult.model_validate_json(data)
                raise ValueError(result.errors)

    async def _create_approle(self):
        url = f"{self.auth.vault_addr}/v1/auth/approle/role/role-{self.uid}"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        payload = {"policies": [f"{self.uid}-secret-policy"]}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    return
                data = await response.text()
                result = HashicorpResult.model_validate_json(data)
                raise ValueError(result.errors)

    async def _get_role_id(self) -> str:
        url = f"{self.auth.vault_addr}/v1/auth/approle/role/role-{self.uid}/role-id"
        headers = {"X-Vault-Token": await self.auth.get_token()}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.text()

        class RoleID(BaseModel):
            role_id: str

        class Data(HashicorpResult):
            data: Optional[RoleID] = None

        v = Data.model_validate_json(data)
        if v.errors:
            raise ValueError(v.errors)
        return v.data.role_id

    async def _get_secret_id(self) -> str:
        url = f"{self.auth.vault_addr}/v1/auth/approle/role/role-{self.uid}/secret-id"
        headers = {"X-Vault-Token": await self.auth.get_token()}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.text()

        class SecretID(BaseModel):
            secret_id: str

        class Data(HashicorpResult):
            data: Optional[SecretID] = None

        v = Data.model_validate_json(data)
        if v.errors:
            raise ValueError(v.errors)
        return v.data.secret_id

    async def upsert_kv(self, kvs: Dict[str, str], app_name: str = "") -> str:
        app_name = app_name or "global"
        url = f"{self.auth.vault_addr}/v1/{self.uid}/data/{app_name}"
        headers = {"X-Vault-Token": await self.auth.get_token(), "Content-Type": "application/json"}
        data = {"data": kvs}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                rsp = await response.text()

        class Version(BaseModel):
            version: str

        class Data(HashicorpResult):
            data: Optional[Version] = None

        v = Data.model_validate_json(rsp)
        if v.errors:
            raise ValueError(v.errors)
        return v.data.version

    async def get_kv(self, app_name: str = "") -> Optional[Dict[str, str]]:
        app_name = app_name or "global"
        url = f"{self.auth.vault_addr}/v1/{self.uid}/data/{app_name}"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                rsp = await response.text()

        class KV(BaseModel):
            data: Optional[Dict[str, str]] = None

        class Data(HashicorpResult):
            data: Optional[KV] = None

        v = Data.model_validate_json(rsp)
        if v.errors:
            raise ValueError(v.errors)
        return v.data.data

    async def delete_kv(self, app_name: str = ""):
        app_name = app_name or "global"
        url = f"{self.auth.vault_addr}/v1/{self.uid}/data/{app_name}"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status == 204:
                    return
                rsp = await response.text()
        v = HashicorpResult.model_validate_json(rsp)
        raise ValueError(v.errors)
