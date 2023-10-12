import flask
import requests
from notification_router import base_types


class LineNotifyDestination(base_types.NotificationDestination):
    """
    Sends notification to LINE via LINE notify service.
    """
    def notify(self, source: base_types.NotificationSource) -> flask.Response:
        authorization = source.authorization
        
        token = authorization.token or authorization.parameters.get("password")

        response = requests.post(
            "https://notify-api.line.me/api/notify",
            headers={
                "Authorization": f"Bearer {token}"
            },
            data={
                "message": source.to_text()
            }
        )

        return flask.Response(
            response.content,
            status=response.status_code,
            headers={
                k: v
                for k, v in response.headers.items()
                if k.lower() == "content-type" or k.startswith("x-")
            }
        )
