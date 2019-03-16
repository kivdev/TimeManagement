import hashlib
import json
import time

from django.core.mail import send_mail
from django.shortcuts import redirect, render, HttpResponse
from rest_framework.views import APIView

from TimeManagement.settings import PAGE_URL, EMAIL_HOST_USER
from Users.models import Confirmed, User, Tokenaizer

KEY_LVL = 1542


class SendAgain(APIView):
    def post(self,request):
        response = {}
        try:
            token = request.META['HTTP_AUTHORIZATION']  # request.GET['token']#request.data['token']
            if token.split(' ')[0] == 'Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    response['status'] = 'error'
                    response['error'] = "Токен не может быть пустым."
                    return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return HttpResponse(json.dumps(response), content_type="application/json")
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return HttpResponse(json.dumps(response), content_type="application/json")
        email = Tokenaizer.objects.filter(token=token)
        if email:
            email = email.values('user').get()['user']
            user = User.objects.filter(email=email)
            if user:
                try:
                    send_mail_confirm(email)
                    response['status'] = 'success'
                    response['message'] = "Сообщение отправлено."
                    return HttpResponse(json.dumps(response), content_type="application/json")
                except:
                    response['status'] = 'error'
                    response['error'] = "Не удалось отправить сообщение."
                    return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                response['status'] = 'error'
                response['error'] = "Незарегистрированные пользователи не могут подтвердить почту."
                return HttpResponse(json.dumps(response), content_type="application/json")

class ConfirmMail(APIView):
    def get(self,request,key):
        user = Confirmed.objects.get(key=key)
        print(key,user)
        if user:
            User.objects.filter(email=user.user).update(confirm=True)
            return redirect(PAGE_URL)
        else:
            return render(request,'bad_key.html',context={"page_url":PAGE_URL})


def send_mail_confirm(email):
    timestmp = str(time.time())
    key = create_key(timestmp)
    Confirmed(timestamp=timestmp, user=email, key=key).save()
    confirm_url = 'https://kivdev.pythonanywhere.com' + '/confirm/' + key
    message = "Добро пожаловать на сайт. Для подтверждения учетной записи перейдите по ссылке ниже.\n{}".format(
        confirm_url)
    #print(message)
    try:
        send_mail(
            'Подтверждение учетной записи',
            message,
            EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
    except:
        pass


def create_key(timestmp):
    key = hashlib.sha256(timestmp.encode('utf-8'))
    for i in range(KEY_LVL):
        key = hashlib.sha256(key.hexdigest().encode('utf-8'))
    return key.hexdigest()

