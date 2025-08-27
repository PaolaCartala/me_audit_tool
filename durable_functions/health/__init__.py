import logging
from http import HTTPStatus

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.debug("Health check endpoint was triggered.")
    return func.HttpResponse(
        "Audit Tool API is up and running.",
        status_code=HTTPStatus.OK
    )
