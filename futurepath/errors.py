from flask import Blueprint, render_template

from . import db


errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(403)
def forbidden(error):
    return render_template("errors/error.html", code=403, title="Access Denied", message="You do not have permission to perform this action."), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    return render_template("errors/error.html", code=404, title="Page Not Found", message="The page or event you requested could not be found."), 404


@errors_bp.app_errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template("errors/error.html", code=500, title="Something Went Wrong", message="FuturePath could not complete that request. Please try again."), 500
