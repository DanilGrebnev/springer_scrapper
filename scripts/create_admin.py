#!/usr/bin/env python
"""Create an admin user for the fastapi-admin panel."""
import asyncio
import getpass
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from tortoise import Tortoise
from src.db.config import TORTOISE_CONFIG


async def main() -> None:
    await Tortoise.init(config=TORTOISE_CONFIG)

    from src.admin.models import Admin

    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty")
        return

    password = getpass.getpass("Password: ")
    if not password:
        print("Password cannot be empty")
        return

    existing = await Admin.filter(username=username).first()
    if existing:
        print(f"Admin '{username}' already exists (id={existing.pk})")
        await Tortoise.close_connections()
        return

    admin = await Admin.create(username=username, password=password)
    print(f"Admin '{username}' created (id={admin.pk})")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
