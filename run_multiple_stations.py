import uvicorn
from dotenv import load_dotenv, find_dotenv
from station.app.db.setup_db import setup_db, reset_db
from station.app.main import app
import threading
import typing
import asyncio


class CustomServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass


async def run_uvicorn():
    cfg = uvicorn.Config(app, loop="none", lifespan="off")
    server = CustomServer(cfg)
    await server.serve()


def join_t(*threads: threading.Thread) -> typing.List[None]:
    return [t.join() for t in threads]


def start_threads(*threads: threading.Thread) -> typing.List[None]:
    return [t.start() for t in threads]


def event_thread(worker: typing.Awaitable, loop, *args, **kwargs) -> threading.Thread:
    def _worker(*args, **kwargs):
        try:
            loop.run_until_complete(worker(*args, **kwargs))
        except Exception as e:
            print(e)
        finally:
            loop.close()

    return threading.Thread(target=_worker, args=args, kwargs=kwargs)


def run_stations(n: int = 3):
    loops = [asyncio.new_event_loop() for i in range(n)]
    for loop in loops:
        asyncio.set_event_loop(loop)

    configs = [
        uvicorn.Config(
            app=app,
            port=8000 + i + 1,
            loop=loops[i],
            limit_max_requests=1,
            reload=True
        )
        for i in range(n)
    ]
    servers = [uvicorn.Server(config=configs[i]) for i in range(n)]
    workers = [event_thread(servers[i].serve, loop=loops[i]) for i in range(n)]
    start_threads(*workers)
    # join_t(*workers)


def naive_run_stations(n: int = 3):
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    for i in range(n):
        uvicorn.run("station.app.main:app", port=8001 + i, host="0.0.0.0", reload=True, log_config=log_config, loop="asyncio")

if __name__ == '__main__':
    run_stations()
    # naive_run_stations()