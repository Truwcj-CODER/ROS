"""
Robot patrol dashboard — FastAPI server.

Usage:
  pip3 install -r requirements.txt
  python3 main.py --map ~/demo_map.yaml --port 5000

Open http://localhost:5000
Requires: slam.launch.py (sim:=true) running first.
"""

import argparse
import os
import threading
from contextlib import asynccontextmanager

import rclpy
from rclpy.executors import MultiThreadedExecutor

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ros_node import NavNode, load_map_file
import routes as _routes
from routes import router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR  = os.path.join(BASE_DIR, 'web')


@asynccontextmanager
async def lifespan(app: FastAPI):
    rclpy.init()
    node = NavNode()
    _routes._node = node
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    t = threading.Thread(target=executor.spin, daemon=True)
    t.start()
    print('[dashboard] ROS2 node started')
    yield
    node.destroy_node()
    rclpy.shutdown()
    print('[dashboard] ROS2 node stopped')


app = FastAPI(title='Robot Dashboard', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=os.path.join(WEB_DIR, 'static')), name='static')
app.include_router(router)


@app.get('/', include_in_schema=False)
async def index():
    return FileResponse(os.path.join(WEB_DIR, 'index.html'))


if __name__ == '__main__':
    import uvicorn

    parser = argparse.ArgumentParser(description='Robot patrol dashboard')
    parser.add_argument('--map',  default='~/demo_map.yaml', help='Path to map YAML')
    parser.add_argument('--port', type=int, default=5000,    help='Port')
    args = parser.parse_args()

    _routes._map_b64, _routes._map_info = load_map_file(args.map)
    if _routes._map_b64 is None:
        print(f'[dashboard] Warning: could not load map from {args.map}')

    print(f'[dashboard] http://localhost:{args.port}')
    uvicorn.run(app, host='0.0.0.0', port=args.port, log_level='warning')
