from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import DashboardOverview

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def overview(current_user: User = Depends(get_current_user)):
    return DashboardOverview(full_name=current_user.full_name, project_title=settings.PROJECT_TITLE)
