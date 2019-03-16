import json
import re
import sys

from rest_framework.views import APIView

from TimeManagement.settings import DEBUG
from Users.models import Tokenaizer, User
from django.db.models import Q
from .models import Categories, Icons, Affairs
from .serializer import (CategoriesSerializer, CategoriesAddSerializer, CategoriesEditSerializer)
from .views import _response, ADD, EDIT

MAX_COLOR_INDEX = 17

def check_categs_data_edit(data, response):
    response['status'] = 'success'
    response['error'] = ''
    try:
        cur_parent = data['categories']
        parent_list = []
        parent_list.append(data['id'])
        while cur_parent!=0 and cur_parent not in parent_list:
            parent_list.append(cur_parent)
            cur_parent = Categories.objects.filter(id=cur_parent).values('categories').get()['categories']
        if cur_parent:
            response['status'] = 'error'
            response['error'] += 'Нельзя создать категорию которая является родителем одного из своих родителей' + '\n'
    except:
        pass
    try:
        if not (2 <= len(data['name'].strip()) < 50):
            response['status'] = 'error'
            response['error'] += 'Имя категории должно быть от 2 до 50 символов.' + '\n'
    except:
        pass
    if len(response['error']):
        return response
    else:
        response.pop('error')
        return False

def check_categs_data(data, response):
    response['status'] = 'success'
    response['error'] = ''
    fast_access_empty = False
    try:
        if not (2 <= len(data['name'].strip()) < 50):
            response['status'] = 'error'
            response['error'] += 'Имя категории должно быть от 2 до 50 символов.' + '\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  name' + '\n'
    try:
        icon = Icons.objects.filter(id=data['icon'])
        if not icon:
            response['status'] = 'error'
            response['error'] += 'Указанной вами иконки нет. Если вы видите ее на сайте, свяжитесь с нами.' + '\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  icon' + '\n'
    try:
        user = User.objects.filter(email=data['user'])
        if not user:
            response['status'] = 'error'
            response['error'] += 'Указанной вами пользователь не зарегистрирован.' + '\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  user' + '\n'
    try:
        parent = Categories.objects.filter(id=data['categories'], user__in=[data['user'],'all'])
        if not parent:
            response['status'] = 'error'
            response['error'] += 'Указанная вами родительская категория отсутствует или не принадлежит вам.' + '\n'
    except:
        pass
    try:
        if not (0 <= data['color'] < MAX_COLOR_INDEX):
            response['status'] = 'error'
            response['error'] += 'Указанной вами цвет не зарегистрирован нами.' + '\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  color' + '\n'
    try:
        if not (data['fast_access'] in ['true', 'false', 0, 1, '0', '1']):
            response['status'] = 'error'
            response['error'] += 'Указанной вами fast_access недоступен.' + '\n'
    except:
        fast_access_empty = True
    try:
        int(data['fast_access_index'])
    except ValueError:
        response['status'] = 'error'
        response['error'] += 'Указанной вами fast_access_index не число.' + '\n'
    except KeyError:
        if not fast_access_empty:
            response['status'] = 'error'
            response['error'] += 'При включенном быстром доступе, обязательно указывать индекс.' + '\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Указанной вами fast_access_index недоступен.' + '\n'
    if len(response['error']):
        return response
    else:
        response.pop('error')
        return False


class Category(APIView):
    def get(self, request, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']  # request.GET['token']#request.data['token']
            if token.split(' ')[0] == 'Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    token = ""
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return _response(response, source, request)
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return _response(response, source, request)
        user = Tokenaizer.objects.filter(token=token)
        if user:
            email = user.values('user').get()['user']
            user = User.objects.filter(email=email)
            if user:
                user = user.values('email').get()['email']
                categories = Categories.objects.filter(Q(id=0) | Q(user__in=[user])) # ~Q(id=0)
            else:
                categories = Categories.objects.filter(user__in=['all'])
        else:
            categories = Categories.objects.filter(user__in=['all'])
        serializer = CategoriesSerializer(categories, many=True)
        response['status'] = 'success'
        response['data'] = serializer.data
        return _response(response, source, request)


class CategoryRemove(APIView):
    def post(self, request, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']  # request.GET['token']#request.data['token']
            if token.split(' ')[0] == 'Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    token = ""
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return _response(response, source, request)
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return _response(response, source, request)
        user = Tokenaizer.objects.filter(token=token)
        if user:
            email = user.values('user').get()['user']
            user = User.objects.filter(email=email)
            if user:
                try:
                    id = json.loads(request.data['data'])['id']
                except:
                    response['status'] = 'error'
                    response['error'] = "Неверно переданы данные. Обратитесь к администратору."
                    return _response(response, source, request)
                category = Categories.objects.filter(id=id, user=email)
                if not category:
                    response['status'] = 'error'
                    response['error'] = "Категория не существует или вам не принадлежит."
                    return _response(response, source, request)

                categs = Categories.objects.filter(categories=id)
                parent = Categories.objects.filter(id=id)[0].categories
                if categs:
                    for i in categs:
                        Categories.objects.filter(id=i.id).update(categories=parent)
                Affairs.objects.filter(category_id=id,user=email).update(category_id=category.values('categories').get()['categories'])
                Categories.objects.filter(id=id, user=email).delete()
                response['status'] = 'success'
                response['error'] = "Указанные категории успешно удалены."
                return _response(response, source, request)

        response['status'] = 'error'
        response['error'] = "Вы не можете удалять категории. Авторизуйтесь."
        return _response(response, source, request)


class CategoryAdd(APIView):
    def post(self, request, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']  # request.GET['token']#request.data['token']
            if token.split(' ')[0] == 'Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    token = ""
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return _response(response, source, request)
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return _response(response, source, request)
        user = Tokenaizer.objects.filter(token=token)
        if user:
            user = user.values('user').get()['user']
            try:
                data = json.loads(request.data['data'])
            except:
                response['status'] = 'error'
                response['error'] = "Ошибка при парсинге входных данных."
                return _response(response, source, request)
            data['user'] = user
            user = User.objects.filter(email=user)
            if user:
                if re.search(ADD, request.META['PATH_INFO']):
                    status = check_categs_data(data, response)
                    if status:
                        return _response(status, source, request)
                    serializer = CategoriesAddSerializer(data=data)
                    if serializer.is_valid(raise_exception=DEBUG):
                        serializer.save()
                        categs_id = Categories.objects.filter(user=data['user']).order_by("-id")[0]
                        response['status'] = 'success'
                        response['id'] = categs_id.id
                        response['data'] = 'Категория успешно добавлена.'
                        return _response(response, source, request)
                elif re.search(EDIT, request.META['PATH_INFO']):
                    try:
                        categs_id = json.loads(request.data['data'])["id"]
                    except:
                        response['status'] = 'error'
                        response['error'] = 'Не удалось обновить категорию. Возможно не переданы обязательные параметры.'
                        return _response(response, source, request)
                    status = check_categs_data_edit(data, response)
                    if status:
                        return _response(status, source, request)
                    if isinstance(categs_id,int):
                        data_ = json.loads(request.data['data'])
                        categ = Categories.objects.get(id=categs_id)
                        if data_.get("categories"):
                            if categs_id==data_.get("categories"):
                                response['status'] = 'error'
                                response['error'] = 'Категория не может быть сама у себя родителем.'
                                return _response(response, source, request)
                        serializer = CategoriesEditSerializer(categ, data=data_,partial=True)
                        if serializer.is_valid(raise_exception=DEBUG):
                            serializer.save()
                            categs_id = Categories.objects.filter(user=data['user']).order_by("-id")[0]
                            response['status'] = 'success'
                            response['id'] = categs_id.id
                            response['data'] = 'Категория успешно обновлена.'
                            return _response(response, source, request)
                        else:
                            response['status'] = 'error'
                            response['error'] = "Не удалось добавить/обновить категорию."
                            return _response(response, source, request)
                    elif isinstance(categs_id,list):
                        for i,id in enumerate(categs_id):
                            try:
                                Categories.objects.filter(~Q(user='all'),id=id).update(fast_access_index=i)
                            except:
                                pass
                        response['status'] = 'success'
                        return _response(response, source, request)

                else:
                    response['status'] = 'error'
                    response['error'] = 'Данный урл не реализован. ' \
                                        'Сообщите нам как вы смогли получить такую ошибку.'
                    return _response(response, source, request)

            else:
                response['status'] = 'error'
                response['error'] = "Не зарегистрированные пользователи не могут добавлять/редактировать категории."
                return _response(response, source, request)
        else:
            response['status'] = 'error'
            response['error'] = "Ваш токен не авторизован."
            return _response(response, source, request)
