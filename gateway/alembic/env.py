import asyncio
import sys
import os
from logging.config import fileConfig

# 상위 폴더(gateway)를 sys.path에 추가하여 absolute import가 가능하게 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from core.config import settings
from core.database import Base
from models.users import User
from models.api_key import ApiKey

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
    

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
        
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()
        
async def run_migrations_online():
    connectable = create_async_engine(settings.database_url)
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()
    
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())