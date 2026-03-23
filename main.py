from dotenv import load_dotenv

load_dotenv()

import uvicorn
from src.config import config

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
