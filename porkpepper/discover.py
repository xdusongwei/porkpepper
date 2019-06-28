from typing import *
from .result import Result


class Discover:
    async def find_user(self, user) -> Result[object]:
        return Result(NotImplementedError())

    async def register_user_session(self, user, session) -> Result[bool]:
        return Result(NotImplementedError())

    async def unregister_user_session(self, user, session) -> Result[bool]:
        return Result(NotImplementedError())

    async def find_service(self) -> Result[object]:
        return Result(NotImplementedError())

    async def register_service(self) -> Result[bool]:
        return Result(NotImplementedError())

    async def unregister_service(self) -> Result[bool]:
        return Result(NotImplementedError())


__all__ = ["Discover", ]
