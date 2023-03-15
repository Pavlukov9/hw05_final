from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, data_list):
    paginator = Paginator(data_list, settings.QUANTITY_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
