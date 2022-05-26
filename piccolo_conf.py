"""
Local development & testing configuration.
Library consumers should use their own.
"""
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "host": "localhost",
        "database": "qbert_test",
        "user": "postgres",
    },
)

APP_REGISTRY = AppRegistry(apps=["qbert.piccolo_app"])
