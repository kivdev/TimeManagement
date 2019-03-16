import json
import re
from datetime import datetime
from datetime import time as tm
from time import mktime

from django.db.models import Q
from rest_framework.views import APIView

from TimeManagement.settings import DEBUG
from Users.models import Tokenaizer, User
from .models import Affairs, Paterns,Icons
from .serializer import (ItemSerializer, ItemAddSerializer,
                         PaternsSerializer, PaternsAddSerializer, PaternsEditSerializer)
from .views import _response, ADD, EDIT

def check_patern_data(request, response, query_type):
    data = json.loads(request.data['data'])
    response['status'] = 'success'
    response['error'] = ''
    user_empty = fast_access_empty = False
    try:
        user = Tokenaizer.objects.filter(token=request.data['token']).values('user').get()['user']
        if not (data['user']==user and User.objects.filter(email=user)):
            response['status'] = 'error'
            response['error'] += 'Вы не можете создать шаблон для этого пользователя или он не зарегистрирован.\n'
    except KeyError:
        user_empty = True
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр: user.\n'

    try:
        if not user_empty:
            icon = Icons.objects.filter(id=data['icon'],user__in=['all',user])
            if not icon:
                response['status'] = 'error'
                response['error'] += 'Указанная иконка не существует или не принадлежит вам.\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр: icon.\n'
    try:
        if not (2 <= len(data['name']) < 50):
            response['status'] = 'error'
            response['error'] += 'Имя шаблона должно быть от 2 до 50 символов.\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  name.\n'
    try:
        try:
            if not isinstance(data['affairs'],str):
                response['status'] = 'error'
                response['error'] += 'Список дел должен быть строкой с идентификаторами, разделенными запятыми.\n'
            else:
               for i in data['affairs'].split(','):
                   if int(i)<0:
                       response['status'] = 'error'
                       response['error'] += 'Идентификатор в списке affairs не может быть отрицательным.\n'
                       break
                   affair = Affairs.objects.filter(id=int(i))
                   if not affair:
                       response['status'] = 'error'
                       response['error'] += 'Дело с id = %s не обнаружено или не принадлежит вам.\n' % int(i)
        except ValueError:
            response['status'] = 'error'
            response['error'] += 'Один или несколько идентификаторов не число.\n'
    except KeyError:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр:  affairs.\n'
    try:
        if not (data['fast_access'] in ['true', 'false', 0, 1, '0', '1']):
            response['status'] = 'error'
            response['error'] += 'Указанной вами fast_access недоступен.\n'
    except:
        fast_access_empty = True
    try:
        int(data['fast_access_index'])
    except ValueError:
        response['status'] = 'error'
        response['error'] += 'Указанной вами fast_access_index не число.\n'
    except KeyError:
        if not fast_access_empty:
            response['status'] = 'error'
            response['error'] += 'При включенном быстром доступе, обязательно указывать индекс.\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Указанной вами fast_access_index неопределен.\n'
    if len(response['error']):
        return response
    else:
        response.pop('error')
        return False

class Patern(APIView):
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
            user = user.values('id').get()['id']
        paterns = Paterns.objects.filter(user=user)
        serializer = PaternsSerializer(paterns, many=True)
        response['status'] = 'success'
        response['data'] = serializer.data
        return _response(response, source, request)


class PaternAdd(APIView):
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
        email = Tokenaizer.objects.filter(token=token)
        if email:
            email = email.values('user').get()['user']
        user = User.objects.filter(email=email)
        if user:

            if re.search(ADD, request.META['PATH_INFO']):
                status = check_patern_data(request, response, 'add')
                if status:
                    return _response(status, source, request)
                else:
                    serializer = PaternsAddSerializer(data=json.loads(request.data['data']))
            else:
                try:
                    patern_id = json.loads(request.data['data'])["id"]
                except:
                    response['status'] = 'error'
                    response['error'] = 'Не удалось обновить шаблон. Возможно не переданы обязательные параметры.'
                    return _response(response, source, request)
                patern = Paterns.objects.filter(id=patern_id, user=email)
                if not patern:
                    response['status'] = 'error'
                    response['error'] = 'Указанный вами шаблон не найден или не принадлежит вам.'
                    return _response(response, source, request)
                status = check_patern_data(request, response, 'edit')
                if status:
                    return _response(status,source,request)
                else:
                    serializer = PaternsEditSerializer(patern, data=json.loads(request.data['data']), partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response['status'] = 'success'
                response['data'] = 'Шаблон успешно добавлен/обновлен.'
                return _response(response, source, request)
            else:
                response['status'] = 'error'
                response['error'] = "Не удалось добавить/обновить шаблон."
                return _response(response, source, request)
        else:
            response['status'] = 'error'
            response['error'] = "Не зарегистрированные пользователи не могут добавлять шаблоны."
            return _response(response, source, request)


class PaternPlace(APIView):
    def post(self, request, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']#request.GET['token']#request.data['token']
            if token.split(' ')[0]=='Bearer':
                token = token.split(' ')[1]
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
        user = User.objects.get(email=user)
        if user:
            try:
                patern_id = json.loads(request.data['data'])['id']
                start_date = json.loads(request.data['data'])['start_date']
                start_time = json.loads(request.data['data'])['start_time']
            except:
                response['status'] = 'error'
                response['error'] = "Не переданы обязательные параметры."
                return _response(response, source, request)
            patern = Paterns.objects.get(id=patern_id, user=user.id)
            if patern:
                paterns = patern.affairs[1:-1].split(',')
                affairs = Affairs.objects.filter(~Q(status='deleted'), id__in=paterns).order_by('start_timestamp')
                delta = [affairs.values()[i + 1]['start_timestamp'] - affairs.values()[i]['start_timestamp'] for i in
                         range(len(affairs.values()) - 1)]

                print(delta, start_date, start_time)
                new_affairs = []
                try:
                    start_timestamp = int(start_date) + int(start_time)
                except:
                    response['status'] = 'error'
                    response['error'] = "Не переданы дата и время начала шаблона."
                    return _response(response, source, request)
                for i, affair in enumerate(affairs.values()):
                    affair['start_timestamp'] = start_timestamp
                    end_timestamp = start_timestamp + affair['duration']
                    start_datetime = datetime.fromtimestamp(start_timestamp)
                    affair['start_date'] = int(mktime(datetime.combine(start_datetime.date(), tm(0, 0, 0)).timetuple()))
                    affair['start'] = int(start_timestamp - affair['start_date'])
                    end_datetime = datetime.fromtimestamp(end_timestamp)
                    affair['end_date'] = int(mktime(datetime.combine(end_datetime.date(), tm(0, 0, 0)).timetuple()))
                    affair['end'] = int(end_timestamp - affair['end_date'])
                    affair['category'] = affair['category_id']
                    affair['notifications'] = 1 if affair['notifications'] else 0
                    affair['fast_access'] = 1 if affair['fast_access'] else 0

                    new_affairs.append(affair)
                    if i != len(affairs.values()) - 1:
                        start_timestamp += int(delta[i])
                response['data'] = []
                for i in new_affairs:
                    serializer = ItemAddSerializer(data=i)
                    print(i)
                    if serializer.is_valid(raise_exception=DEBUG):
                        affair = serializer.save()
                        return_serializer = ItemSerializer(Affairs.objects.filter(id=affair.id).get())
                        response['data'].append(return_serializer.data)
                    else:
                        response['status'] = 'error'
                        response['error'] = "Не удалось сохранить дела."
                        return _response(response, source, request)
                response['status'] = 'success'
                return _response(response, source, request)
            else:
                response['status'] = 'error'
                response['error'] = "Указанный шаблон не принадлежит вам."
                return _response(response, source, request)

        else:
            response['status'] = 'error'
            response['error'] = "Не зарегистрированные пользователи не могут добавлять шаблоны."
            return _response(response, source, request)
