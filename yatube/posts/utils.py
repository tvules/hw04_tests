from django.core.paginator import Paginator


def _get_page_obj(request, object_list, per_page):
    """Возвращает объект страницы"""
    paginator = Paginator(object_list, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
