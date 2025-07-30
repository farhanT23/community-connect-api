from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from .schema import SearchResultsSchema, SearchTabEnum
from .service import SearchService

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", response_model=SearchResultsSchema)
async def search_content(
    q: str,
    tab: SearchTabEnum = SearchTabEnum.all,
    db: AsyncSession = Depends(get_db)
):
    service = SearchService(db)
    return await service.perform_search(query=q, tab=tab)