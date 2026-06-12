import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.example.schema import ItemCreate, ItemResponse
from app.modules.example.service import create_item, delete_item, get_item, get_items

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=201)
async def create(data: ItemCreate, db: AsyncSession = Depends(get_db)):
    return await create_item(db, data)


@router.get("/", response_model=list[ItemResponse])
async def list_all(db: AsyncSession = Depends(get_db)):
    return await get_items(db)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_one(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    item = await get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def remove(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    deleted = await delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
