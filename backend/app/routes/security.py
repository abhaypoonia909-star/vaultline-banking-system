from flask import Blueprint, jsonify

from app.extensions import limiter
from app.security.decorators import login_required
from app.security.validators import parse_body
from app.services.security_service import run_simulation, security_overview

bp = Blueprint("security", __name__)


@bp.post("/brute-force-simulation")
@login_required
@limiter.limit("3 per hour")
def simulate(user):
    return jsonify(run_simulation(user, parse_body()))


@bp.get("/logs")
@login_required
def logs(user):
    return jsonify(security_overview(user))
