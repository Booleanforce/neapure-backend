from rest_framework.views import exception_handler

from shared.responses.api_response import ApiResponse


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is None:
        return None

    return ApiResponse.error(
        message="Request Failed",
        errors=response.data,
        status_code=response.status_code,
    )