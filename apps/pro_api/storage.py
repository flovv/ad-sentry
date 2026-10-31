from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field

from services.data_ingestion.models import BusinessOutcomeDataset
from services.decision_contracts.models import DecisionContract
from services.incrementality.models import ExperimentPlan, ExperimentResultAnalysis


class ConnectedAccount(BaseModel):
    account_id: str
    customer_id: str
    descriptive_name: str
    currency_code: str
    time_zone: str
    connected_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    is_active: bool = True


class Workspace(BaseModel):
    workspace_id: str
    name: str
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    accounts: dict[str, ConnectedAccount] = Field(default_factory=dict)
    datasets: dict[str, BusinessOutcomeDataset] = Field(default_factory=dict)
    experiment_plans: dict[str, ExperimentPlan] = Field(default_factory=dict)
    experiment_analyses: dict[str, ExperimentResultAnalysis] = Field(default_factory=dict)
    decision_contracts: dict[str, DecisionContract] = Field(default_factory=dict)


class TenantIsolatedStore:
    """
    In-memory isolated storage per workspace/tenant.
    Provides complete data deletion and account disconnect facilities.
    """

    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}

    def get_or_create_workspace(self, workspace_id: str, name: str = "Default Workspace") -> Workspace:
        if workspace_id not in self._workspaces:
            self._workspaces[workspace_id] = Workspace(workspace_id=workspace_id, name=name)
        return self._workspaces[workspace_id]

    def connect_account(self, workspace_id: str, account: ConnectedAccount) -> None:
        ws = self.get_or_create_workspace(workspace_id)
        ws.accounts[account.customer_id] = account

    def disconnect_account(self, workspace_id: str, customer_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if ws and customer_id in ws.accounts:
            del ws.accounts[customer_id]
            # Clean up datasets belonging to customer
            ds_to_del = [did for did, ds in ws.datasets.items() if ds.customer_id == customer_id]
            for did in ds_to_del:
                del ws.datasets[did]
            return True
        return False

    def delete_workspace(self, workspace_id: str) -> bool:
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            return True
        return False

    def store_dataset(self, workspace_id: str, dataset: BusinessOutcomeDataset) -> None:
        ws = self.get_or_create_workspace(workspace_id)
        ws.datasets[dataset.dataset_id] = dataset

    def get_dataset(self, workspace_id: str, dataset_id: str) -> Optional[BusinessOutcomeDataset]:
        ws = self._workspaces.get(workspace_id)
        return ws.datasets.get(dataset_id) if ws else None

    def store_contract(self, workspace_id: str, contract: DecisionContract) -> None:
        ws = self.get_or_create_workspace(workspace_id)
        ws.decision_contracts[contract.contract_id] = contract

    def get_contract(self, workspace_id: str, contract_id: str) -> Optional[DecisionContract]:
        ws = self._workspaces.get(workspace_id)
        return ws.decision_contracts.get(contract_id) if ws else None


# Global tenant store instance
tenant_store = TenantIsolatedStore()
