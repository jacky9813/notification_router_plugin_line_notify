import urllib.parse
import json

import flask
import flasgger
import requests
from notification_router import base_types

bp = flask.Blueprint("line_notify", __name__)


@bp.get("/authorize")
@flasgger.swag_from(
    specs={
        "description": "Register LINE Notify service to a user or group.",
        "parameters": [],
        "responses": {
            "302": {"description": "Redirect to LINE Notify consent screen."},
            "501": {
                "description": "Server has not been properly configured.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            }
        }
    }
)
def authorize() -> flask.Response:
    params = {
        "response_type": "code",
        "client_id": flask.current_app.config.get("LINE_NOTIFY", {}).get("client_id", None),
        "redirect_uri": flask.url_for(".authorize_callback", _external=True, _scheme="https"),
        "scope": "notify",
        "state": "",
        "response_mode": "form_post"
    }

    if params["client_id"] is None:
        return base_types.ErrorResponse(
            "Server has not been properly configured.",
            status=501
        )

    return flask.redirect(
        "https://notify-bot.line.me/oauth/authorize?%s" % 
        (urllib.parse.urlencode(params), )
    )


@bp.get("/callback")
@flasgger.swag_from(
    specs={
        "description": "The callback function for authorize and fetches access token.",
        "parameters": [
            {
                "name": "code",
                "in": "query",
                "description": "The authorization code that the server must"
                "process before giving out access token.",
                "required": "true"
            },
            {
                "name": "state",
                "in": "query",
                "description": "The one time code for preventing replay attack.",
                "required": "true"
            }
        ],
        "responses": {
            "200": {
                "description": "Success with access token being returned.",
                "content": {
                    "text/plain": {}
                }
            },
            "400": {
                "description": "Not able to fetch access token from LINE notify.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            },
            "401": {
                "description": "No authorization code in request.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            },
            "501": {
                "description": "Server has not been properly configured.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            }
        }
    }
)
def authorize_callback() -> flask.Response:
    if flask.request.method == "GET":
        code = flask.request.args.get("code", None)
    else:
        data = urllib.parse.parse_qs(flask.request.get_data(as_text=True))
        code = data.get("code", None)

    if not code:
        return base_types.ErrorResponse(
            "Authorization aborted.",
            status=401
        )

    params = {
        "grant_type": "authorization_code",
        "code": code[0],
        "redirect_uri": flask.url_for(".authorize_callback", _external=True, _scheme="https"),
        "client_id": flask.current_app.config.get("LINE_NOTIFY", {}).get("client_id", None),
        "client_secret": flask.current_app.config.get("LINE_NOTIFY", {}).get("client_secret", None)
    }

    if params["client_id"] is None or params["client_secret"] is None:
        return base_types.ErrorResponse(
            "Server has not been properly configured.",
            status=501
        )

    response = requests.post(
        "https://notify-bot.line.me/oauth/token",
        data=params
    )

    if response.status_code != 200:
        return base_types.ErrorResponse(
            "Failed to request access token.",
            status=400
        )

    try:
        token = response.json()["access_token"]
    except (json.JSONDecodeError, KeyError):
        return base_types.ErrorResponse(
            "Received success response but contains invalid data from LINE Notify serivice.",
            status=502
        )
    
    return flask.Response(
        token,
        status=200,
        content_type="text/plain"
    )

@bp.post("/callback")
@flasgger.swag_from(
    specs={
        "description": "The callback function for authorize and fetches access token.",
        "requestBody": {
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The authorization code provided by LINE Notify API.",
                                "required": "true"
                            },
                            "state": {
                                "type": "string",
                                "description": "The state for preventing replay attack.",
                                "required": "true"
                            }
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "Success with access token being returned.",
                "content": {
                    "text/plain": {}
                }
            },
            "400": {
                "description": "Not able to fetch access token from LINE notify.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            },
            "401": {
                "description": "No authorization code in request.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            },
            "501": {
                "description": "Server has not been properly configured.",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/error"
                        }
                    }
                }
            }
        }
    }
)
def authorize_callback_post() -> flask.Response:
    return authorize_callback()
