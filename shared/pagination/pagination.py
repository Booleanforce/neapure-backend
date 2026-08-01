from rest_framework.pagination import PageNumberPagination

from shared.responses.api_response import ApiResponse


class CustomPagination(PageNumberPagination):

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):

        return ApiResponse.success(
            data={
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )