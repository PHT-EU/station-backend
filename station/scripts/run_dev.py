import pathlib

import uvicorn
from dotenv import find_dotenv, load_dotenv


def main():
    load_dotenv(find_dotenv())
    # set the path to the project root
    project_root = pathlib.Path(__file__).parent.parent
    uvicorn.run(
        "station.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)],
        access_log=True,
    )


if __name__ == "__main__":
    main()
