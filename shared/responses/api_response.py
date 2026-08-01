from rest_framework.response import Response


class ApiResponse:

    @staticmethod
    def success(
        data=None,
        message="Success",
        status=200,
    ):
        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
            },
            status=status,
        )

    @staticmethod
    def error(
        message="Something went wrong",
        status=400,
        errors=None,
    ):
        return Response(
            {
                "success": False,
                "message": message,
                "errors": errors,
            },
            status=status,
        )