import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from request_models import CreateUserRequest


class UserService:
    async def create_user(self, session: AsyncSession, request: CreateUserRequest) -> User:
        user = User(
            id=str(uuid.uuid4()),
            auth_user_id=request.user.auth_user_id,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_user_by_auth_user_id(self, session: AsyncSession, auth_user_id: str) -> User:
        async with session:
            statement = select(User).where(User.auth_user_id == auth_user_id)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError(f"Invalid auth_user_id: {auth_user_id}")
            return user

