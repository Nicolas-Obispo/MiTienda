import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


EXPECTED_DATABASE_NAME = "mitienda_stage97_test"
ENV_NAME = "FEEDGO_STAGE97_TEST_DATABASE_URL"


def isolated_mysql_test_engine():
    raw_url = os.getenv(ENV_NAME)
    if not raw_url:
        raise unittest.SkipTest(f"{ENV_NAME} no configurada")

    url = make_url(raw_url)
    if not url.drivername.startswith("mysql"):
        raise RuntimeError("ETAPA 97 concurrency tests require MySQL")
    if url.database != EXPECTED_DATABASE_NAME or not url.database.endswith("_test"):
        raise RuntimeError(
            f"Unsafe test database: expected exactly {EXPECTED_DATABASE_NAME!r}"
        )

    engine = create_engine(url, pool_pre_ping=True, isolation_level="READ COMMITTED")
    with engine.connect() as connection:
        current_database = connection.exec_driver_sql("SELECT DATABASE()").scalar_one()
    if current_database != EXPECTED_DATABASE_NAME:
        engine.dispose()
        raise RuntimeError("Connected database does not match the isolated test database")
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)
