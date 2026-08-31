from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal, List, Dict, Any
from collections import Counter
import logging

from ..core import crud, models, schemas
from ..core.dependencies import get_db, get_team_and_verify_membership

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)

PeriodLiteral = Literal["day", "week", "month"]

@router.get(
    "/teams/{team_id}/compass/",
    response_model=schemas.CompassData,
    summary="获取团队情绪罗盘数据",
)
def get_compass_data(
    period: PeriodLiteral = Query(default="week"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
):
    """根据周期筛选情绪罗盘数据并返回结构化结果。"""
    return crud.get_team_compass_data(db=db, team_id=str(team.id), period=period)


@router.get(
    "/teams/{team_id}/focus-time/",
    response_model=schemas.FocusTimeData,
    summary="获取团队有效专注时长数据",
)
def get_focus_time_data(
    period: PeriodLiteral = Query(default="week"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
):
    """提取团队指定周期内的专注时长统计信息。"""
    return crud.get_team_focus_time_data(db=db, team_id=str(team.id), period=period)


@router.get(
    "/teams/{team_id}/insights/",
    response_model=schemas.AIInsights,
    summary="获取AI洞察墙数据",
)
def get_insights_data(
    period: PeriodLiteral = Query(default="week"),
    team: models.Team = Depends(get_team_and_verify_membership),
    db: Session = Depends(get_db),
):
    return crud.get_team_insights_data(db=db, team_id=str(team.id), period=period)