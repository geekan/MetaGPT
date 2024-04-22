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
    role_id: Optional[str] = None  # At least one of `role_id` and `secret_id`, or `access_token` must be valid
    secret_id: Optional[str] = None  # At least one of `role_id` and `secret_id`, or `access_token` must be valid
    access_token: Optional[str] = None  # At least one of `role_id` and `secret_id`, or `access_token` must be valid

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

    def __init__(self, **data):
        super().__init__(**data)
        self.uid = self.format_user_name(self.user_name)

    async def create_user(self) -> HashicorpAuth:
        """Admin tool, create user.

        Returns:
            The `HashicorpAuth` object containing `role_id` and `secret_id`.
        """
        await self._create_kv_secret_engine()
        await self._create_policy()
        await self._create_approle()
        role_id = await self._get_role_id()
        secret_id = await self._get_secret_id()
        return HashicorpAuth(vault_addr=self.auth.vault_addr, role_id=role_id, secret_id=secret_id)

    @staticmethod
    def format_user_name(user_name):
        """Formats a user name by hashing it with SHA256 and returning a shortened version.

        Args:
            user_name (str): The user name to be formatted.

        Returns:
            str: A formatted user name with the first 8 characters of the SHA256 hash prepended by 'u'.
        """
        hashed = sha256(user_name.encode()).hexdigest()
        return f"u{hashed[:8]}"

    async def _create_kv_secret_engine(self, exists_ok: bool = True):
        url = f"{self.auth.vault_addr}/v1/sys/mounts/{self.uid}"
        headers = {"X-Vault-Token": await self.auth.get_token()}
        payload = {"type": "kv", "options": {"version": "2"}}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    return
                data = await response.text()
        result = HashicorpResult.model_validate_json(data)
        exists_errors = [f"path is already in use at {self.uid}/"]
        if exists_ok and exists_errors == result.errors:
            return
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

    async def upsert_kv(self, kvs: Dict[str, str], app_name: str = "") -> int:
        """Creates or updates a secret in HashiCorp Vault's Key-Value (KV) secret engine v2.

        See More: https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#create-update-secret

        Args:
            kvs (Dict[str, str]): A dictionary containing key-value pairs representing the secret data
                to be created or updated. The keys represent the paths of the secret to update, and the
                values represent the corresponding secret values.
            app_name (str, optional): The path to the KV mount containing the secret to read, such as secret.
                This is specified as part of the URL.

        Returns:
            int: A int indicating the version of the kvs.
        """
        app_name = app_name or "global"
        url = f"{self.auth.vault_addr}/v1/{self.uid}/data/{app_name}"
        headers = {"X-Vault-Token": await self.auth.get_token(), "Content-Type": "application/json"}
        data = {"data": kvs}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                rsp = await response.text()

        class Version(BaseModel):
            version: int

        class Data(HashicorpResult):
            data: Optional[Version] = None

        v = Data.model_validate_json(rsp)
        if v.errors:
            raise ValueError(v.errors)
        return v.data.version

    async def get_kv(self, app_name: str = "") -> Optional[Dict[str, str]]:
        """Reads a secret version from HashiCorp Vault's Key-Value (KV) secret engine v2.

        Retrieves the secret data from the specified KV mount path.
        See more: https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-secret-version

        Args:
            app_name (str): The path to the KV mount containing the secret to read, such as secret.
                This is specified as part of the URL.

        Returns:
            Optional[Dict[str, str]]: A dictionary containing the secret data if found.
                Returns None if the secret is not found.
        """
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
        """Deletes the latest version of a secret from HashiCorp Vault's Key-Value (KV) secret engine v2.

        See More: https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#delete-latest-version-of-secret

        Args:
            app_name (str, optional): The path to the KV mount containing the secret to delete, such as secret.
                This is specified as part of the URL.

        Returns:
            None
        """
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

    field_validator("vault_addr", mode="before")
