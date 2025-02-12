from flask import Blueprint

bp = Blueprint('amc', __name__)

@bp.app_template_filter('expiring_soon')
def expiring_soon_filter(contracts, days=30):
    return [c for c in contracts if c.days_until_expiry() <= days]

from app.amc import routes
