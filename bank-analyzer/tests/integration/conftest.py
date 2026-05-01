import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def use_db(setup_db):
    pass
