import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.example.model import Item
from app.modules.example.schema import ItemCreate


async def create_item(db: AsyncSession, data: ItemCreate) -> Item:
    item = Item(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(Item))
    return list(result.scalars().all())


async def get_item(db: AsyncSession, item_id: uuid.UUID) -> Item | None:
    return await db.get(Item, item_id)


async def delete_item(db: AsyncSession, item_id: uuid.UUID) -> bool:
    item = await db.get(Item, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True
