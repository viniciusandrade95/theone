from modules.crm.repo.crm_repo import CrmRepo
from modules.crm.repo.in_memory import InMemoryCrmRepo
from modules.crm.repo.sql import SqlCrmRepo

__all__ = ["CrmRepo", "InMemoryCrmRepo", "SqlCrmRepo"]
