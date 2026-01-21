from typing import List, Optional

from pydantic import BaseModel


class EnergyData(BaseModel):
    name: str
    img: str
    refreshTimeStamp: int
    cur: int
    total: int


class LivenessData(BaseModel):
    name: str
    img: str
    cur: int
    total: int


class BattlePassData(BaseModel):
    name: str
    cur: int
    total: int


class DailyData(BaseModel):
    gameId: int
    userId: int
    serverId: str
    roleId: str
    roleName: str
    signInTxt: str
    hasSignIn: bool
    energyData: EnergyData
    livenessData: LivenessData
    battlePassData: List[BattlePassData]


class AccountBaseInfo(BaseModel):
    name: str
    id: int
    creatTime: Optional[int] = None
    activeDays: Optional[int] = None
    level: Optional[int] = None
    worldLevel: Optional[int] = None
    roleNum: Optional[int] = None
    bigCount: Optional[int] = None
    smallCount: Optional[int] = None
    achievementCount: Optional[int] = None
    achievementStar: Optional[int] = None
    weeklyInstCount: Optional[int] = None
    weeklyInstCountLimit: Optional[int] = None
    storeEnergy: Optional[int] = None
    storeEnergyLimit: Optional[int] = None
    rougeScore: Optional[int] = None
    rougeScoreLimit: Optional[int] = None
