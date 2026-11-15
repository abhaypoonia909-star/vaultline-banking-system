import os

os.environ["FLASK_APP_AUTOLOAD"] = "0"
os.environ["AUTO_SEED_ADMIN"] = "0"
os.environ["RATELIMIT_ENABLED"] = "0"

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    application = create_app("testing")
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
