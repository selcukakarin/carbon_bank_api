from rest_framework.pagination import PageNumberPagination


class GeneralPagination(PageNumberPagination):
    page_size = 10
