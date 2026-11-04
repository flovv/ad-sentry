from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from apps.pro_api.storage import ConnectedAccount, Workspace, tenant_store
from pmax_sentry_core.api import get_account_info

router = APIRouter(prefix="/workspaces", tags=["Workspaces & Accounts"])


class ConnectAccountRequest(BaseModel):
    customer_id: str


@router.get("/current", response_model=Workspace)
def get_current_workspace(
    x_workspace_id: str = Header(default="default_ws"),
) -> Workspace:
    return tenant_store.get_or_create_workspace(x_workspace_id)


@router.post("/accounts/connect", response_model=ConnectedAccount)
def connect_account(
    req: ConnectAccountRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> ConnectedAccount:
    try:
        acc_info = get_account_info(req.customer_id)
        account = ConnectedAccount(
            account_id=f"acc_{acc_info.customer_id}",
            customer_id=acc_info.customer_id,
            descriptive_name=acc_info.descriptive_name,
            currency_code=acc_info.currency_code,
            time_zone=acc_info.time_zone,
            is_active=True,
        )
        tenant_store.connect_account(x_workspace_id, account)
        return account
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/accounts/{customer_id}")
def disconnect_account(
    customer_id: str,
    x_workspace_id: str = Header(default="default_ws"),
) -> dict[str, str]:
    success = tenant_store.disconnect_account(x_workspace_id, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found in workspace")
    return {"status": "DISCONNECTED", "customer_id": customer_id}


@router.delete("/current")
def delete_workspace_data(
    x_workspace_id: str = Header(default="default_ws"),
) -> dict[str, str]:
    tenant_store.delete_workspace(x_workspace_id)
    return {"status": "DELETED", "workspace_id": x_workspace_id}
