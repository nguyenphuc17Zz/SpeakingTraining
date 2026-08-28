from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import User
from app.domains.users.schemas import UserUpdate
from app.shared.errors.exceptions import NotFoundException


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_default_user(self) -> User:
        """Fetches the primary local user, creating one if this is a fresh setup."""
        result = await self.session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                display_name="Learner (学習者)",
                timezone="Asia/Tokyo",
                locale="ja-JP",
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")
        return user

    async def update_user(self, user_id: str, payload: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(user, key, val)
        await self.session.commit()
        await self.session.refresh(user)
        return user
