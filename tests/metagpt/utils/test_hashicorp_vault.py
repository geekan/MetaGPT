#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
import pytest

from metagpt.utils.hashicorp_vault import HashicorpAuth, HashicorpVaultSecrets


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("root_token", "vault_addr", "user_name", "kvs"),
    [
        (
            "hvs.gMkrxXDhVNkeg4H50Vb9tUeg",
            "http://127.0.0.1:8200",
            "a@dafcSSD/a",
            {"user": "a", "pwd": "a", "ip": "a", "port": "a"},
        )
    ],
)
@pytest.mark.skip
async def test_vault_secret(root_token, vault_addr, user_name, kvs, context):
    root_vault = HashicorpVaultSecrets(
        auth=HashicorpAuth(vault_addr=vault_addr, access_token=root_token), user_name=user_name
    )
    user_auth = await root_vault.create_user()
    user_vault = HashicorpVaultSecrets(
        auth=user_auth,
        user_name=user_name,
    )

    await user_vault.upsert_kv(kvs=kvs, app_name="redis-config")
    kvs1 = await user_vault.get_kv(app_name="redis-config")
    assert kvs1 == kvs


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
