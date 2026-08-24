"""Run ETAPA 97 concurrency tests against an isolated, resettable MySQL database."""

import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url

from app.core.config import settings
from tests.mysql_stage97_test_support import ENV_NAME, EXPECTED_DATABASE_NAME


def build_isolated_test_url():
    source = make_url(settings.DATABASE_URL)
    if not source.drivername.startswith("mysql"):
        raise RuntimeError("The configured development server is not MySQL")
    return source.set(database=EXPECTED_DATABASE_NAME)


def ensure_test_database(test_url):
    server_url = URL.create(
        drivername=test_url.drivername,
        username=test_url.username,
        password=test_url.password,
        host=test_url.host,
        port=test_url.port,
        query=test_url.query,
    )
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(
                f"CREATE DATABASE IF NOT EXISTS `{EXPECTED_DATABASE_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        engine.dispose()


def main():
    test_url = build_isolated_test_url()
    if test_url.database != EXPECTED_DATABASE_NAME or not test_url.database.endswith("_test"):
        raise RuntimeError("Refusing to run without the isolated ETAPA 97 test database")
    ensure_test_database(test_url)
    os.environ[ENV_NAME] = test_url.render_as_string(hide_password=False)
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_stage97_mysql_concurrency")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
