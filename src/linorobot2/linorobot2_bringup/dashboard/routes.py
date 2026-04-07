"""API routes for the robot dashboard."""

from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

# Shared state — set by main.py before uvicorn starts
_node    = None
_map_b64 = None
_map_info = None


class GoRequest(BaseModel):
    waypoints: List[dict]
    loop: bool = False


class InitialPoseRequest(BaseModel):
    x: float
    y: float
    theta: float = 0.0


@router.get('/api/map')
async def api_map():
    if _map_b64 is None:
        return JSONResponse({'ok': False})
    return {'ok': True, 'image': _map_b64, 'info': _map_info}


@router.get('/api/map-live')
async def api_map_live():
    b64, info = _node.get_live_map()
    if b64 is None:
        return JSONResponse({'ok': False})
    return {'ok': True, 'image': b64, 'info': info}


@router.get('/api/pose')
async def api_pose():
    return _node.get_pose()


@router.get('/api/status')
async def api_status():
    return _node.status()


@router.post('/api/go')
async def api_go(req: GoRequest):
    _node.start(req.waypoints, req.loop)
    return {'ok': True}


@router.post('/api/stop')
async def api_stop():
    _node.cancel()
    return {'ok': True}


@router.post('/api/initial-pose')
async def api_initial_pose(req: InitialPoseRequest):
    _node.set_initial_pose(req.x, req.y, req.theta)
    return {'ok': True}
