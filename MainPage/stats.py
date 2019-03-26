import time
from collections import defaultdict
from django.shortcuts import HttpResponse
from .models import Categories, Affairs
from Users.models import Tokenaizer, User
from django.db.models import Sum
from rest_framework.views import APIView
import json


class Stats(APIView):
    def post(self, request):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']
            if token.split(' ')[0] == 'Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    token = ""
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return HttpResponse(json.dumps(response), content_type="application/json")
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return HttpResponse(json.dumps(response), content_type="application/json")
        # Берет id пользователя
        email = Tokenaizer.objects.get(token=token)
        if email:
            email = email.user
            user = User.objects.get(email=email)
            if user:
                try:
                    data = json.loads(request.data['data'])
                    start_date = data['start_date']
                    end_date = data['end_date']
                except KeyError:
                    response['status'] = 'error'
                    response['error'] = "Не переданы обязательные параметры: start_date/end_date"
                    return HttpResponse(json.dumps(response), content_type="application/json")
                if data.get('id', None):
                    response['status'] = 'success'
                    response['data'] = for_histogram(start_date, end_date, data['id'])
                    return HttpResponse(json.dumps(response), content_type="application/json")
                else:
                    try:
                        data['type']
                    except KeyError:
                        response['status'] = 'error'
                        response['error'] = "Не переданы обязательные параметры для круговой диаграмы: type"
                        return HttpResponse(json.dumps(response), content_type="application/json")
                    response['status'] = 'success'
                    kartoshka = get_final_categs_stats(start_date,end_date, email,data['type'])
                    try:
                        response['data'] = kartoshka['categories']
                    except KeyError:
                        response['status'] = 'error'
                        response['error'] = "У вас нет категорий."
                    return HttpResponse(json.dumps(response), content_type="application/json")


def get_final_categs_stats(start_date, end_date, email, type_):
    """ Создает дерево категорий с длительностями """

    parents = defaultdict(list)
    for p in categories_to_tuple(start_date, end_date, email, type_):
        parents[p[2]].append(p)


    def buildtree(t=None, parent_current_id=''):
        parent = parents.get(parent_current_id, None)
        if parent is None:
            return t
        for current_id, name, parent_id, count, color, summAll in parent:
            category = {'name': name, "color": color, "count": count, "summAll": summAll}
            if t is None:
                t = category
            else:
                categories = t.setdefault('categories', [])
                categories.append(category)
            buildtree(category, current_id)
        return t

    data = buildtree()
    return data


def categories_to_tuple(s_start_date, s_end_date, email, type_):
    duration_dict = get_categories_duration(s_start_date, s_end_date, email, type_)
    categories_list = []
    for i in duration_dict:
        current_category = Categories.objects.get(id=i)
        categories_list.append((current_category.id, current_category.name,
                                current_category.categories,
                                duration_dict[current_category.id],
                                current_category.color, 0))
    categories_list.append((0, "Без категории", '', '', '', 0))
    return categories_list


def get_categories_duration(s_start_date, s_end_date, email, type_):
    """ Берет длительность всех категорий пользователя """

    s_categories_list = get_categories_id(email)
    duration_dict = {}
    for category in s_categories_list:
        if type_ == "Avg":
            duration = get_avg(s_start_date, s_end_date, category)
        elif type_ == "Sum":
            duration = get_duration(s_start_date, s_end_date, category)
        duration_dict[category] = duration
    return duration_dict


def get_categories_id(email):
    """ Собирает id категорий по запрошенному пользователю """

    categoricurrent_id = []
    for cat in Categories.objects.filter(user=email):
        categoricurrent_id.append(cat.id)
    return categoricurrent_id


def get_avg(s_start_date, s_end_date, id_category):
    """
    Считает среднее время,
    затраченное на конкретную категорию
    за конкретный промежуток времени
    """

    full_duration = get_duration(s_start_date, s_end_date, id_category)
    days = (s_end_date - s_start_date) / 86400 + 1
    a = full_duration / days
    return a


def get_duration(start_date, end_date, id_category):
    """
    Считает время, затраченное на конкретную категорию
    за конкретный промежуток времени
    """

    affairs = Affairs.objects.filter(category_id=id_category,
                                     end_date__lte=end_date,
                                     start_date__gte=start_date,
                                     status='done').aggregate(Sum('duration'))
    a_end = cut_end(start_date, end_date, id_category)
    a_start = cut_start(start_date, end_date, id_category)
    a_outside = cut_outside(start_date, end_date, id_category)
    duration = 0
    try:
        duration = int(affairs['duration__sum']) + a_end + a_start + a_outside
    except TypeError:
        duration = a_end + a_start + a_outside
    duration = round(duration/3600,10)
    return duration


def find_end(start_date, end_date, id_category):
    """ Ищет дела, заканчивающиеся после запрошенного периода """

    a_without_end = []
    for i in Affairs.objects.filter(category_id=id_category,
                                    end_date__gt=end_date,
                                    start_date__gte=start_date,
                                    start_date__lte=end_date,
                                    status='done'):
        a_without_end.append(i.id)
    return a_without_end


def cut_end(start_date, end_date, id_category):
    """ Обрезает дела, заканчивающиеся после запрошенного периода """

    cat_id = find_end(start_date, end_date, id_category)
    duration = 0
    for i in cat_id:
        current_affair = Affairs.objects.get(id=i)
        start_current_affair = current_affair.start + current_affair.start_date
        duration += (end_date + 86400) - start_current_affair
    return duration


def find_start(start_date, end_date, id_category):
    """ Ищет дела, начинающиеся до запрошенного периода """

    a_without_start = []
    for i in Affairs.objects.filter(category_id=id_category,
                                    start_date__lt=start_date,
                                    end_date__gte=start_date,
                                    end_date__lte=end_date,
                                    status='done'):
        a_without_start.append(i.id)
    return a_without_start


def cut_start(start_date, end_date, id_category):
    """ Обрезает дела, начинающиеся до запрошенного периода """

    cat_id = find_start(start_date, end_date, id_category)
    duration = 0
    for i in cat_id:
        current_affair = Affairs.objects.get(id=i)
        end_current_affair = current_affair.end + current_affair.end_date
        duration += end_current_affair - start_date
    return duration


def find_outside(start_date, end_date, id_category):
    """ Ищет дела, которые поглощают запрошенный период """

    a_outside = []
    for i in Affairs.objects.filter(category_id=id_category,
                                    start_date__lt=start_date,
                                    end_date__gt=end_date,
                                    status='done'):
        a_outside.append(i.id)
    return a_outside


def cut_outside(start_date, end_date, id_category):
    """ Обрезает дела, которые поглощают запрошенный период """

    cat_id = find_outside(start_date, end_date, id_category)
    duration = 0
    for i in cat_id:
        duration += (end_date + 86400) - start_date  # end-start*5 Возможно лучше
    return duration


def for_histogram(s_start_date, s_end_date, cat_id):
    """ Сбор статистики для гистограммы """

    all_categories_id = []
    def find_child_categories(cat_id):
        """ Поиск id всех категорий """

        categories_id = []
        for cat in Categories.objects.filter(categories=cat_id):
            categories_id.append(cat.id)
        if categories_id != []:
            all_categories_id += categories_id
            for cat in categories_id:
                find_child_categories(cat)

    def get_child_duratoin(start_date, end_date, categories_id):
        full_duration = 0
        for cat_id in categories_id:
            full_duration += get_duration(start_date, end_date, cat_id)

        return full_duration

    all_categories_id.append(cat_id)
    list_to_return = []
    if s_end_date - s_start_date == 172800:
        for i in range(3):
            list_to_return.append({"Длительность": get_child_duratoin(s_end_date,
                                                                      s_end_date,
                                                                      all_categories_id),
                                   "date": time.strftime("%d.%m.%Y ", time.gmtime(s_end_date))})
            s_end_date -= 86400
    if s_end_date - s_start_date == 518400:
        for i in range(7):
            list_to_return.append({"Длительность": get_child_duratoin(s_end_date,
                                                                      s_end_date,
                                                                      all_categories_id),
                                   "date": time.strftime("%d.%m.%Y ", time.gmtime(s_end_date))})
            s_end_date -= 86400
    if s_end_date - s_start_date == 2505600:
        for i in range(30):
            list_to_return.append({"Длительность": get_child_duratoin(s_end_date,
                                                                      s_end_date,
                                                                      all_categories_id),
                                   "date": time.strftime("%d.%m.%Y ", time.gmtime(s_end_date))})
            s_end_date -= 86400
    return list_to_return

