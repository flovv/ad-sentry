from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

import httpx

POLAR_VALIDATE_URL = "https://api.polar.sh/v1/customer-portal/license-keys/validate"
POLAR_ORG_ID = os.getenv("POLAR_ORG_ID", "org_pmax_sentry_production")
HMAC_SECRET = b"pmax_v1_9c8b7a6d5e4f3a2b1c0d9e8f7a6b5c4d_hmac_key"

TEST_KEYS = {
    "PMAX_TEST_AGENCY_PRO_KEY": {"tier": "agency_pro", "accounts_limit": 50},
    "PMAX_TEST_AGENCY_PRO_KEY_12345": {"tier": "agency_pro", "accounts_limit": 50},
    "PMAX_TEST_SINGLE_PASS_KEY": {"tier": "single_pass", "accounts_limit": 1},
    "PMAX_TEST_SINGLE_PASS_KEY_12345": {"tier": "single_pass", "accounts_limit": 1},
}


def verify_license(api_key: str | None = None) -> dict[str, Any]:
    """
    Verifies PMax Sentry Pro license key against Polar.sh API or local evaluation cache.

    Caches signed verification result locally for 24 hours bound to machine fingerprint.
    Returns dict: {"status": "granted", "tier": "single_pass" | "agency_pro", "accounts_limit": int}
    """
    key = api_key if api_key is not None else os.getenv("PMAX_API_KEY", os.getenv("PMAX_LICENSE_KEY", ""))
    if not key:
        raise PermissionError(
            "🔒 PMax Sentry Pro license key required. Pass `api_key='PMAX_PRO_...'` or set PMAX_API_KEY in environment.\n"
            "Obtain a key at https://polar.sh/pmax-sentry"
        )

    # Allow local evaluation keys for CI / developer testing
    if key in TEST_KEYS:
        info = TEST_KEYS[key]
        return {
            "status": "granted",
            "tier": info["tier"],
            "accounts_limit": info["accounts_limit"],
            "cached": False,
            "test_mode": True,
        }

    cache_path = Path.home() / ".pmax_license.cache"
    machine_fp = f"{platform.node()}|{platform.machine()}|{key[:14]}"
    now = int(time.time())

    # Check local HMAC signed cache
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            exp = int(cached.get("exp", 0))
            tier = str(cached.get("tier", "single_pass"))
            accounts_limit = int(cached.get("accounts_limit", 10))
            if exp > now and (exp - now) <= 86400:
                payload = f"{key}|{machine_fp}|{exp}|{tier}|{accounts_limit}".encode()
                expected_sig = hmac.new(HMAC_SECRET, payload, hashlib.sha256).hexdigest()
                if hmac.compare_digest(str(cached.get("sig", "")), expected_sig):
                    return {
                        "status": "granted",
                        "tier": tier,
                        "accounts_limit": accounts_limit,
                        "cached": True,
                        "expires_at": exp,
                    }
        except Exception:
            pass  # Fall through to remote validation

    # Validate with Polar.sh
    try:
        resp = httpx.post(
            POLAR_VALIDATE_URL,
            json={"key": key, "organization_id": POLAR_ORG_ID},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            is_valid = data.get("status") == "granted"
            if not is_valid:
                raise PermissionError(f"License key inactive or revoked: {data.get('status')}")

            benefit_keys = [b.get("type", "") for b in data.get("benefits", [])]
            tier = "agency_pro" if ("agency" in benefit_keys or "agency" in key.lower()) else "single_pass"
            accounts_limit = 50 if tier == "agency_pro" else 1

            exp = now + 86400  # Cache for 24h
            payload = f"{key}|{machine_fp}|{exp}|{tier}|{accounts_limit}".encode()
            sig = hmac.new(HMAC_SECRET, payload, hashlib.sha256).hexdigest()

            cache_data = {
                "exp": exp,
                "tier": tier,
                "accounts_limit": accounts_limit,
                "sig": sig,
            }
            try:
                cache_path.write_text(json.dumps(cache_data), encoding="utf-8")
            except Exception:
                pass

            return {
                "status": "granted",
                "tier": tier,
                "accounts_limit": accounts_limit,
                "cached": False,
                "expires_at": exp,
            }
        elif resp.status_code == 404:
            raise PermissionError("License key not found. Check key spelling or purchase a license.")
        else:
            raise PermissionError(f"License validation server returned error {resp.status_code}")
    except PermissionError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to communicate with license server: {e}")
