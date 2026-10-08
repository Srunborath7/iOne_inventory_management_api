from typing import Generic, TypeVar

RepoType = TypeVar("RepoType")


class BaseService(Generic[RepoType]):
    """Base OOP Service with repository dependency injection."""

    def __init__(self, repository: RepoType):
        self.repository = repository
