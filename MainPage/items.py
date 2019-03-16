import json
import re
from datetime import datetime, timedelta, date
from datetime import time as tm

from django.db.models import Q
from django.shortcuts import HttpResponse
from rest_framework.views import APIView

from TimeManagement.settings import DEBUG
from Users.models import Tokenaizer
from Users.views import gen_token, gen_temp_username
from .models import Affairs, Categories
from .serializer import (ItemSerializer, ItemAddSerializer, ItemEditSerializer)
from .views import _response, ADD, EDIT


def check_items_data_edit(data,response):
    response['status'] = 'success'
    response['error'] = ''
    last_week = (datetime.combine(datetime.date(datetime.now()) - timedelta(days=7), tm(0, 0, 0)) - datetime(1970, 1,
                                                                                                             1)).total_seconds()
    sdate_empty = edate_empty = start_empty = end_empty = False
    try:
        if data['start_date'] < last_week:
            response['status'] = 'error'
            response['error'] += 'Нельзя создать дело в прошлом(более чем за неделю).\n'
    except KeyError:
        sdate_empty = True
    try:
        if data['end_date'] < last_week:
            response['status'] = 'error'
            response['error'] += 'Нельзя создать дело закончевшееся в прошлом(более чем за неделю).\n'
    except KeyError:
        edate_empty = True
    try:
        if not (0 <= data['start'] <= 86400):
            response['status'] = 'error'
            response['error'] += 'Параметр start должен иметь значение в диапазоне [0,86400].\n'
    except KeyError:
        start_empty = True
    try:
        if not (0 <= data['end'] <= 86400):
            response['status'] = 'error'
            response['error'] += 'Параметр end должен иметь значение в диапазоне [0,86400].\n'
    except KeyError:
        end_empty = True
    if sdate_empty != edate_empty:
        response['status'] = 'error'
        response['error'] += 'Дело должно иметь старт И конец, или не иметь ни того, ни другого.(дата)\n'
    if start_empty != end_empty:
        response['status'] = 'error'
        response['error'] += 'Дело должно иметь старт И конец, или не иметь ни того, ни другого.(время)\n'
    if sdate_empty == False and edate_empty == False:
        if data['end_date'] < data['start_date']:
            response['status'] = 'error'
            response['error'] += 'Дело не может закончится раньше чем начнется.(дата)\n'
    if start_empty == False and end_empty == False:
        if data['end_date'] < data['start_date']:
            response['status'] = 'error'
            response['error'] += 'Дело не может закончится раньше чем начнется.(время)\n'
    try:
        if len(data['text']) > 50:
            response['status'] = 'error'
            response['error'] += 'Название дела не может быть длиньше 50 символов.\n'
    except:
        pass
    if len(response['error']):
        return response
    else:
        response.pop('error')
        return False

def check_items_data(data, response, type):

    response['status'] = 'success'
    response['error'] = ''
    last_week = (datetime.combine(datetime.date(datetime.now()) - timedelta(days=7), tm(0, 0, 0)) - datetime(1970, 1,
                                                                                                             1)).total_seconds()
    sdate_empty = edate_empty = start_empty = end_empty = user_empty = notif_empty = False
    try:
        if data['start_date'] < last_week:
            response['status'] = 'error'
            response['error'] += 'Нельзя создать дело в прошлом(более чем за неделю).\n'
    except KeyError:
        sdate_empty = True
    try:
        if data['end_date'] < last_week:
            response['status'] = 'error'
            response['error'] += 'Нельзя создать дело закончевшееся в прошлом(более чем за неделю).\n'
    except KeyError:
        edate_empty = True
    try:
        if not (0 <= data['start'] <= 86400):
            response['status'] = 'error'
            response['error'] += 'Параметр start должен иметь значение в диапазоне [0,86400].\n'
    except KeyError:
        start_empty = True
    try:
        if not (0 <= data['end'] <= 86400):
            response['status'] = 'error'
            response['error'] += 'Параметр end должен иметь значение в диапазоне [0,86400].\n'
    except KeyError:
        end_empty = True
    if sdate_empty != edate_empty:
        response['status'] = 'error'
        response['error'] += 'Дело должно иметь старт И конец, или не иметь ни того, ни другого.(дата)\n'
    if start_empty != end_empty:
        response['status'] = 'error'
        response['error'] += 'Дело должно иметь старт И конец, или не иметь ни того, ни другого.(время)\n'
    if sdate_empty == False and edate_empty == False:
        if data['end_date'] < data['start_date']:
            response['status'] = 'error'
            response['error'] += 'Дело не может закончится раньше чем начнется.(дата)\n'
    if start_empty == False and end_empty == False:
        if data['end_date'] < data['start_date']:
            response['status'] = 'error'
            response['error'] += 'Дело не может закончится раньше чем начнется.(время)\n'

    try:
        user = Tokenaizer.objects.filter(user=data['user'])
        if not user:
            response['status'] = 'error'
            response['error'] += 'Указанный юзер не авторизован под текущим токеном.\n'
    except:
        user_empty = True
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр: user\n'
    try:
        if not user_empty:
            category = Categories.objects.filter(id=data['category'], user__in=[data['user'], 'all'])
            if not category:
                response['status'] = 'error'
                response['error'] += 'Переданая категория отсутствует или вам не доступна.\n'
    except:
        response['status'] = 'error'
        response['error'] += 'Не передан обязательный параметр: category\n'
    try:
        if not (data['complexity'] in range(0, 4)):
            response['status'] = 'error'
            response['error'] += 'Переданая сложность не поддерживается. Возможное значение: 0-3\n'
    except:
        pass
    try:
        if not (data['importance'] in range(0, 4)):
            response['status'] = 'error'
            response['error'] += 'Переданая важность не поддерживается. Возможное значение: 0-3\n'
    except:
        pass
    try:
        if len(data['text']) > 50:
            response['status'] = 'error'
            response['error'] += 'Название дела не может быть длиньше 50 символов.\n'
    except:
        pass
    try:
        if data['status'] != "":
            response['status'] = 'error'
            response['error'] += 'При создании дела невозможно указать статус отличный от "".\n'
    except:
        pass
    try:
        if not (data['notifications'] in ['true', 'false', 0, 1, '0', '1']):
            response['status'] = 'error'
            response['error'] += 'Параметр notifications указан не верно, ' \
                                 'он может принимать одно из значений: ["true", "false", 0, 1, "0", "1"]\n'
        if data['notifications']:
            notif_empty = True
    except KeyError:
        notif_empty = True
    if not notif_empty:
        try:
            if data['notification_time'] < 0:
                response['status'] = 'error'
                response['error'] += 'Нельзя создать оповещение в прошлом.\n'
        except:
            response['status'] = 'error'
            response['error'] += 'Не передан обязательный параметр: notification_time\n'
    try:
        if not (isinstance(data['period'], int) and data['period'] > 0):
            response['status'] = 'error'
            response['error'] += 'Параметр period должен быть положительным целым числом\n'
    except KeyError:
        pass
    if len(response['error']):
        return response
    else:
        response.pop('error')
        return False



class Items(APIView):
    def get(self, request, sdate=None, edate=None, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']#request.GET['token']#request.data['token']
            if token.split(' ')[0]=='Bearer':
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
        if not sdate and not edate:
            sdate = datetime.now().date() - timedelta(days=7)
            edate = datetime.now().date() + timedelta(days=7)
        else:
            if sdate != '0' and sdate:
                try:
                    sdate_ = sdate.split('.')
                    sdate_.reverse()
                    y, m, d = (int(x) for x in sdate_)
                    sdate = date(y, m, d)
                except:
                    response['status'] = 'error'
                    response['error'] = "%s невозможно преобразовать в дату." % sdate
                    if not source:
                        return HttpResponse(json.dumps(response), content_type="application/json")
                    else:
                        response = {request.data['query_url']: response}
                        return response
            if edate != '0' and edate:
                try:
                    edate_ = edate.split('.')
                    edate_.reverse()
                    y, m, d = (int(x) for x in edate_)
                    edate = date(y, m, d)
                except:
                    response['status'] = 'error'
                    response['error'] = "%s невозможно преобразовать в дату." % edate
                    if not source:
                        return HttpResponse(json.dumps(response), content_type="application/json")
                    else:
                        response = {request.data['query_url']: response}
                        return response
        if sdate == '0':
            sdate = edate - timedelta(days=7)
        if edate == '0':
            edate = sdate + timedelta(days=8)
        sdate = (datetime.combine(sdate, tm(0, 0, 0)) - datetime(1970, 1, 1)).total_seconds()
        edate = (datetime.combine(edate, tm(23, 59, 59)) - datetime(1970, 1, 1)).total_seconds()
        if token:
            user = Tokenaizer.objects.filter(token=token).values('user')
        else:
            response['status'] = 'success'
            response['message'] = 'Токен пустой.'
            response['data'] = []
            return _response(response, source, request)
        if not user:
            response['status'] = 'error'
            response['error'] = "Токен не зарегистрирован. Возможно он устарел."
            return _response(response, source, request)
        else:
            user = user.get()['user']
        affairs = Affairs.objects.filter(~Q(status='deleted'), start_date__gte=sdate, start_date__lte=edate, user=user) |\
                  Affairs.objects.filter(~Q(status='deleted'), start_date__isnull=True,end_date__isnull=True,user=user)
        serializer = ItemSerializer(affairs, many=True)
        response['status'] = 'success'
        response['data'] = serializer.data
        return _response(response, source, request)


class ItemsAdd(APIView):
    def post(self, request, source=None):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']#request.GET['token']#request.data['token']
            if token.split(' ')[0]=='Bearer':
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
        try:
            data = json.loads(request.data['data'])
        except:
            response['status'] = 'error'
            response['error'] = 'Свяжитесь с администратором. Вот. Так вот. Да.'
            return _response(response, source, request)
        if token == '':
            user = gen_temp_username()
            token = gen_token(user)
            t = Tokenaizer(user=user, token=token)
            t.save()
            response['token'] = token
            data['user'] = user
        else:
            user = Tokenaizer.objects.filter(token=token)
            if not user:
                response['status'] = 'error'
                response[
                    'error'] = 'Не удалось добавить задачу. Попробуйте еще раз или обратитесь к администратору.'
                return _response(response, source, request)
            else:
                data['user'] = user.values('user').get()['user']
        if re.search(ADD, request.META['PATH_INFO']):
            status = check_items_data(data, response, 'add')
            if status:
                return _response(status, source, request)
            affair = data
            try:
                affair['start_timestamp'] = affair['start_date'] + affair['start']
                affair['duration'] = (affair['end_date']+affair['end'])-(affair['start_date']+affair['start'])
                if affair['duration'] < 0:
                    response['status'] = 'error'
                    response['error'] = 'Длительность дела не может быть отрицательной.'
                    return _response(response, source, request)
            except KeyError:
                affair['start_timestamp'] = 0
                affair['duration'] = 0
            serializer = ItemAddSerializer(data=affair)
            if serializer.is_valid(raise_exception=DEBUG):
                serializer.save()
                affair_id = Affairs.objects.filter(user=data['user']).order_by("-id")[0]
                response['status'] = 'success'
                response['message'] = 'Задача успешно добавлена'
                response['id'] = affair_id.id
                return _response(response, source, request)
            else:
                response['status'] = 'error'
                response[
                    'error'] = 'Не удалось добавить задачу. Попробуйте еще раз или обратитесь к администратору.'
                return _response(response, source, request)
        elif re.search(EDIT, request.META['PATH_INFO']):
            status = check_items_data_edit(data, response)
            if status:
                return _response(status, source, request)
            try:
                affair_id = json.loads(request.data['data'])["id"]
            except:
                response['status'] = 'error'
                response['error'] = 'Не удалось обновить задачу. Возможно не переданы обязательные параметры.'
                return _response(response, source, request)
            try:
                affair = Affairs.objects.get(id=affair_id)
            except:
                response['status'] = 'error'
                response['error'] = 'Не удалось обновить задачу. Возможно передан не существующий ID.'
                return _response(response, source, request)
            data=json.loads(request.data['data'])
            try:
                data['start_timestamp'] = data['start_date'] + data['start']
                data['duration'] = (data['end_date']+data['end'])-(data['start_date']+data['start'])
            except:
                pass
            serializer = ItemEditSerializer(affair, data=data, partial=True)
            if serializer.is_valid(raise_exception=DEBUG):
                serializer.save()
                response['status'] = 'success'
                response['message'] = 'Задача успешно обновлена'
                return _response(response, source, request)
            else:
                response['status'] = 'error'
                response['error'] = 'Не удалось обновить задачу'
                return _response(response, source, request)
