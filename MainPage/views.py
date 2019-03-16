import json
import re
import os
from time import sleep
from random import randint
from django.shortcuts import HttpResponse, render,redirect
from rest_framework.views import APIView
from TimeManagement.settings import DEBUG, VERSION, DEV, MEDIA_DIR,PAGE_URL
from Users.models import Tokenaizer, User
from .models import Icons
from django.views import View


EDIT = re.compile('edit', re.IGNORECASE)
ADD = re.compile('add', re.IGNORECASE)


def _response(response, source, request):
    if not source:
        return HttpResponse(json.dumps(response), content_type="application/json")
    else:
        response = {request.data['query_url']: response}
        return response

class Index(View):
    def get(self,request):
        import sys
        while True:
            print(1,file=sys.stderr)
            sleep(2)

class MainPage(APIView):
    def get(self, request):
        if DEBUG:
            return render(request,'debug.html')
        else:
            return redirect(PAGE_URL)
        #return HttpResponse(json.dumps({"data": "Главная страница"}), content_type="application/json")



class Upload(APIView):
    def post(self,request):
        response = {'status': 'success'}
        allow_formats = {'jpg', 'jpeg', 'png'}
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
                return HttpResponse(json.dumps(response), content_type="application/json", status=400)
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return HttpResponse(json.dumps(response), content_type="application/json", status=400)
        user = Tokenaizer.objects.filter(token=token)

        if user:
            email = user.values('user').get()['user']
            user = User.objects.filter(email=email)
            if user:
                USER_DIR = os.path.join(MEDIA_DIR, email.split('@')[0])
                if not os.path.exists(USER_DIR):
                    response['status'] = 'error'
                    response['error'] = 'У вас нет рабочей директории. Свяжитесь с администратором.'
                    return HttpResponse(json.dumps(response), content_type="application/json", status=400)
                try:
                    img = request.data['img']
                except KeyError:
                    response['status'] = 'error'
                    response['error'] = 'Не передано изображение.'
                    return HttpResponse(json.dumps(response), content_type="application/json", status=400)
                except:
                    response['status'] = 'error'
                    response['error'] = 'Что-то пошло не так, сообщите администраторам о возникшей проблеме.'
                    return HttpResponse(json.dumps(response), content_type="application/json", status=400)
                if not (request.data['img'].name.split('.')[-1] in allow_formats):
                    response['status'] = 'error'
                    response['error'] = "Неразрешенный формат изображений. Разрешено только png,jpg,jpeg"
                    return HttpResponse(json.dumps(response), content_type="application/json", status=400)
                if request.data['img'].size>409600:
                    response['status'] = 'error'
                    response['error'] = "Вес указанного вами изображения больше 50КБ."
                    return HttpResponse(json.dumps(response), content_type="application/json", status=400)
                img_name = str(randint(100000,999999999)) + '.'+img.name.split('.')[-1]
                with open(os.path.join(USER_DIR,img_name), 'wb+') as destination:
                    for chunk in img.chunks():
                        destination.write(chunk)
                icon = Icons(path=os.path.join('media\{}\\'.format(email.split('@')[0])) +img_name ,user=email)
                icon.save()
                icon_id = Icons.objects.filter(path=os.path.join('media\{}\\'.format(email.split('@')[0])+img_name)).order_by("-id")
                response['status'] = 'success'
                response['data'] = os.path.join('media\{}\\'.format(email.split('@')[0]), img_name)
                response['id'] = icon_id.values().get()['id']
                return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                response['status'] = 'error'
                response['error'] = "Не зарегистрированные пользователи не могут загружать изображения."
                return HttpResponse(json.dumps(response), content_type="application/json", status=400)
        else:
            response['status'] = 'error'
            response['error'] = "Ваш токен не авторизован."
            return HttpResponse(json.dumps(response), content_type="application/json", status=400)

class Combiner(APIView):
    def post(self):
        pass

class Info(APIView):
    def get(self,request):
        response = {
            'debug': DEBUG,
            'version': VERSION,
            'developer': DEV
         }
        return HttpResponse(json.dumps(response), content_type="application/json")