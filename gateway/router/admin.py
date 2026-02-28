from fastapi import APIRouter, Depends
from redis.asyncio import Redis
import httpx
from core.dependencies import get_ollama, get_redis
from core.security import get_current_admin_user
from models.users import User
from service.log_service import get_usage_summary

router = APIRouter()


@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_admin_user),
    client: httpx.AsyncClient = Depends(get_ollama)
):
    response = await client.get("/api/tags")
    return response.json()


@router.get("/usage")
async def get_usage(current_user: User = Depends(get_current_admin_user), redis: Redis = Depends(get_redis)):
    return await get_usage_summary(redis, current_user.id)