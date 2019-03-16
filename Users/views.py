import hashlib
import json
import re
import sys

from datetime import datetime

from django.shortcuts import HttpResponse
from rest_framework.views import APIView

from MainPage.mail import send_mail_confirm
from MainPage.models import Affairs,Categories,Icons,Paterns, Logs
from Users.models import User, Tokenaizer
from Users.serializer import UserSerializer, TokenaizerSerializer
from .new_user import default_categs,create_dir
from TimeManagement.settings import HASH_PASSWORD_LVL

UNAUTHUSER = 'unauthuser'
RE_UNAUTHUSER = re.compile(UNAUTHUSER, re.IGNORECASE)


class Login(APIView):
    def post(self, request):
        # Проверка не авторизован ли уже юзер?
        response = {}


        #Проверка присутсвия данных
        try:
            email = request.data['email'].lower()
            password = request.data['password']
            token = request.META['HTTP_AUTHORIZATION']#request.GET['token']#request.data['token']
            if token.split(' ')[0]=='Bearer':
                try:
                    token = token.split(' ')[1]
                except IndexError:
                    token = ""
            else:
                response['status'] = 'error'
                response['error'] = "Указанный вид токена не поддерживается."
                return HttpResponse(json.dumps(response), content_type="application/json")

        except KeyError:
            response["status"] = "error"
            response["error"] = \
                "Обязательные поля email/password/token не были переданы! Обратитесь к администратору: support@timemanage.com"
            return HttpResponse(json.dumps(response), content_type="application/json")
        #Ищем пользователя среди зарегистрированных
        user = User.objects.filter(email=email)
        if not user:
            response["status"] = "error"
            response["error"] = "Пользователь с указанным email не зарегистрирован."
            return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            U_user = user.values('email').get()['email']
            U_password = user.values('password').get()['password']
            #Ищем имя пользователя по токену
            T_user = Tokenaizer.objects.filter(token=token)#.values('user').get()
            #Если токен вообще обнаружен, то сравниваем имена из бд и переданные для авторизации
            if T_user:
                T_user = T_user.values('user').get()['user']
                if T_user==U_user:
                    response["status"] = "error"
                    response["error"] = "Пользователь уже авторизован."
                    return HttpResponse(json.dumps(response), content_type="application/json")
                else:
                    if re.search(RE_UNAUTHUSER,T_user):
                        if _hash_passw(password) == U_password:

                            #########06.01.2018########

                            response['warning'] = ''
                            for i in Affairs.objects.filter(user=T_user):
                                try:
                                    i.category=Categories.objects.get(name=i.category,user=U_user)
                                    i.user=T_user
                                    i.save()
                                except Exception as e:
                                    if not response['warning']:
                                        response['warning'] += 'Возникли проблемы слияния дел в связи с отсутствием у вас стандартных категорий:\n'

                                    if i.start_date:
                                        response['warning'] += datetime.fromtimestamp(i.start_date+i.start).strftime('%d-%m-%Y %H:%M:%S')+' \
                                        - '+datetime.fromtimestamp(i.end_date+i.end).strftime('%d-%m-%Y %H:%M:%S')+' "'+i.text+'" '+i.category.name+'\n'
                                    else:
                                        response['warning'] += 'без начала - без конца "'+i.text+'" '+i.category.name+'\n'
                                    Affairs.objects.get(id=i.id).delete()
                            if not response['warning']:
                                response.pop('warning')
                            #___________________________#
                            Affairs.objects.filter(user=T_user).update(user=U_user)

                            Tokenaizer.objects.filter(token=token).update(user=U_user)
                            response["status"] = "success"
                            response["message"] = "Пользователь успешно авторизован."

                            log = Logs(user=U_user,action="Авторизация: Login:{}".format(email),datetime=datetime.now(),
                                       ip=get_client_ip(request),browser=request.META['HTTP_USER_AGENT'])
                            log.save()
                            return HttpResponse(json.dumps(response), content_type="application/json")
                        else:
                            response["status"] = "error"
                            response["error"] = "Не верный пароль."
                            return HttpResponse(json.dumps(response), content_type="application/json")
                    else:
                        if _hash_passw(password) == U_password:
                            token = gen_token(U_user)
                            user_auth_token = {
                                "user": U_user,
                                "token": token
                            }
                            Tokenaizer.objects.filter(user=U_user).delete()
                            serializer = TokenaizerSerializer(data=user_auth_token)
                            if serializer.is_valid():
                                serializer.save()
                                response["status"] = "success"
                                response["message"] = "Пользователь успешно авторизован"
                                response["token"] = token
                                log = Logs(user=U_user, action="Авторизация: Login:{}".format(email),
                                           datetime=datetime.now(),
                                           ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
                                log.save()
                                return HttpResponse(json.dumps(response), content_type="application/json")
                            else:
                                response["status"] = "error"
                                response["error"] = \
                                    "Не удалось сохранить токен. Обратитесь к администратору: support@timemanage.com или попробуйте еще раз войти"
                                return HttpResponse(json.dumps(response), content_type="application/json")
                        else:
                            response["status"] = "error"
                            response["error"] = "Не верный пароль."
                            return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                if _hash_passw(password) == U_password:
                    token = gen_token(U_user)
                    user_auth_token = {
                        "user": U_user,
                        "token": token
                    }
                    serializer = TokenaizerSerializer(data=user_auth_token)
                    if serializer.is_valid():
                        serializer.save()

                        response["status"] = "success"
                        response["message"] = "Пользователь успешно авторизован"
                        response["token"] = token
                        log = Logs(user=U_user, action="Авторизация: Login:{}".format(email), datetime=datetime.now(),
                                   ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
                        log.save()
                        return HttpResponse(json.dumps(response), content_type="application/json")
                    else:
                        response["status"] = "error"
                        response["error"] = \
                            "Не удалось сохранить токен. " \
                            "Обратитесь к администратору: support@timemanage.com или попробуйте еще раз войти"
                        return HttpResponse(json.dumps(response), content_type="application/json")
                else:
                    response["status"] = "error"
                    response["error"] = "Не верный пароль."
                    return HttpResponse(json.dumps(response), content_type="application/json")


class Logout(APIView):
    def post(self, request):
        # Проверка на приход и существование всех данных
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
                return HttpResponse(json.dumps(response), content_type="application/json")
        except KeyError:
            response["status"] = "error"
            response["error"] = \
                "Обязательное поле token не были переданы! Обратитесь к администратору: support@timemanage.com"
            return HttpResponse(json.dumps(response), content_type="application/json")
        if not token:
            response["status"] = "error"
            response["error"] = \
                "Токен не может быть пустой! Обратитесь к администратору: support@timemanage.com"
            return HttpResponse(json.dumps(response), content_type="application/json")
        T_user = Tokenaizer.objects.filter(token=token)
        if T_user:
            T_user = T_user.values('user').get()['user']
        else:
            response["status"] = "error"
            response["error"] = "Пользователь не авторизован."
            return HttpResponse(json.dumps(response), content_type="application/json")
        Tokenaizer.objects.filter(token=token).delete()
        response['status'] = 'success'
        response['token'] = ''
        log = Logs(user=T_user, action="Деавторизация: Login:{}".format(T_user), datetime=datetime.now(),
                   ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
        log.save()
        return HttpResponse(json.dumps(response), content_type="application/json")



class Register(APIView):
    def post(self, request):
        # Регистрация юзера
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
                return HttpResponse(json.dumps(response), content_type="application/json")
            email = request.data['email'].lower()
            password = request.data['password']
        except KeyError:
            response["status"] = "error"
            response["error"] = "Обязательные поля email/password/token не были переданы!"
            return HttpResponse(json.dumps(response), content_type="application/json")
        email = email.strip()
        try:

            if len(email.split('@')) != 2:
                raise Exception
            if len(email.split('@')[0]) < 2:
                raise Exception
            if re.findall(r'[А-я]+', email.split('@')[0]):
                raise Exception
            if len(email.split('@')[1].split('.')) != 2:
                raise Exception
            if len(email.split('@')[1].split('.')[0])<2:
                raise Exception
        except:
            response["status"] = "error"
            response["error"] = "Что-то это не похоже на почту -_-."
            return HttpResponse(json.dumps(response), content_type="application/json")
        user = User.objects.filter(email=email)
        if user:
            response["status"] = "error"
            response["error"] = "Пользователь с указанной почтой уже зарегистрирован."
            return HttpResponse(json.dumps(response), content_type="application/json")
        if not re.findall(r"^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$", password):
            response["status"] = "error"
            response["error"] = "Пароль должен содержать минимум 8 символов, 1 заглавную и 1 строчную буквы."
            return HttpResponse(json.dumps(response), content_type="application/json")
        user_reg_data = {
            'email': email,
            'password': _hash_passw(password),
            'is_admin': False if not request.data.get('is_admin') else True,
            'is_staff': False if not request.data.get('is_staff') else True
        }

        serializer = UserSerializer(data=user_reg_data)
        if serializer.is_valid():
            serializer.save()
            if create_dir((email.split('@')[0]).lower()):
                response["status"] = "error"
                response["error"] = "Не удалось создать " \
                                    "вашу директорию, " \
                                    "свяжитесь с администратором " \
                                    "для решения проблемы."
            default_categs(email)
            if not token:
                token = gen_token(email)
                user_auth_token = {
                    "user": email,
                    "token": token
                }
                serializer = TokenaizerSerializer(data=user_auth_token)
                if serializer.is_valid():
                    serializer.save()
                    response["status"] = "success"
                    response["message"] = "Пользователь успешно добавлен"
                    response["token"] = token
                    log = Logs(user=email, action="Регистрация: Login:{}".format(email), datetime=datetime.now(),
                               ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
                    log.save()
                    send_mail_confirm(email)
                    return HttpResponse(json.dumps(response), content_type="application/json")
                else:
                    response["status"] = "error"
                    response["error"] = \
                        "Не удалось сохранить токен. Обратитесь к администратору: support@timemanage.com"
                    return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                try:
                    temp_username = Tokenaizer.objects.filter(token=token).values('user').get()['user']
                except:
                    response["status"] = "error"
                    response["error"] = \
                        "Не удалось обнаружить указанный токен. Обратитесь к администратору: support@timemanage.com"
                    return HttpResponse(json.dumps(response), content_type="application/json")
                Tokenaizer.objects.filter(token=token).update(user=email)
                try:
                    for i in Affairs.objects.filter(user=temp_username):
                        i.category=Categories.objects.get(name=i.category,user=email)
                        i.user=email
                        i.save()
                except Exception as e:
                    print(e)
                response["status"] = "success"
                response["message"] = "Пользователь успешно добавлен"
                log = Logs(user=email, action="Регистрация: Login:{}".format(email), datetime=datetime.now(),
                           ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
                log.save()
                send_mail_confirm(email)
                return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            response["status"] = "error"
            response["error"] = \
                "Не удалось добавить пользователя. Обратитесь к администратору: support@timemanage.com"
            return HttpResponse(json.dumps(response), content_type="application/json")

class Change(APIView):
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
            email =email.values('user').get()['user']
            user = User.objects.filter(email=email)
            if user:
                user = True
            else:
                response['status'] = 'error'
                response['error'] = "Пользователь с указанным токеном не зарегистрирован."
                return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            response['status'] = 'error'
            response['error'] = "Ваш токен не авторизован."
            return HttpResponse(json.dumps(response), content_type="application/json")
        if request.data.get('email') and user:
            new_email = request.data['email']
            try:
                if len(new_email.split('@')) != 2:
                    raise Exception
                if len(new_email.split('@')[0]) < 2:
                    raise Exception
                if re.findall(r'[А-я]+', new_email.split('@')[0]):
                    raise Exception
                if len(new_email.split('@')[1].split('.')) != 2:
                    raise Exception
                if len(new_email.split('@')[1].split('.')[0]) < 2:
                    raise Exception
                if len(new_email.split('@')[1].split('.')[1]) < 2:
                    raise Exception
            except:
                response["status"] = "error"
                response["error"] = "Что-то это не похоже на почту -_-."
                return HttpResponse(json.dumps(response), content_type="application/json")
            if User.objects.filter(email=new_email):
                response['status'] = 'error'
                response['error'] = "Указанная почта занята."
                return HttpResponse(json.dumps(response), content_type="application/json")

            User.objects.filter(email=email).update(email=new_email,confirm=False)
            Tokenaizer.objects.filter(token=token).update(user=new_email)
            Affairs.objects.filter(user=email).update(user=new_email)
            Categories.objects.filter(user=email).update(user=new_email)
            Paterns.objects.filter(user=email).update(user=new_email)
            Icons.objects.filter(user=email).update(user=new_email)
            response['status'] = 'success'
            response['error'] = "Почта успешно изменена."
            log = Logs(user=new_email, action="Изменение почты: Old:{} New:{}".format(email,new_email), datetime=datetime.now(),
                       ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
            log.save()
            return HttpResponse(json.dumps(response), content_type="application/json")
        if request.data.get('oldPassword') and request.data.get('password') and user:
            if not re.findall(r"^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$", request.data.get('password')):
                response["status"] = "error"
                response["error"] = "Пароль должен содержать минимум 8 символов, 1 заглавную и 1 строчную буквы."
                return HttpResponse(json.dumps(response), content_type="application/json")
            oldPassword = _hash_passw(request.data.get('oldPassword'))
            user = User.objects.filter(email=email, password=oldPassword)
            if user:
                email = user.values('email').get()['email']
                user.update(password=_hash_passw(request.data.get('password')))
                response['status'] = 'success'
                response['error'] = "Пароль успешно изменен."
                log = Logs(user=email,
                           action="Изменение пароля",
                           datetime=datetime.now(),
                           ip=get_client_ip(request), browser=request.META['HTTP_USER_AGENT'])
                log.save()
                return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                response['status'] = 'error'
                response['error'] = "Указанный старый пароль неверен."
                return HttpResponse(json.dumps(response), content_type="application/json")
        response['status'] = 'error'
        response['error'] = "Не переданы обязательные для изменения данных."
        return HttpResponse(json.dumps(response), content_type="application/json",status=412)



class Me(APIView):
    def get(self,request):
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
                return HttpResponse(json.dumps(response), content_type="application/json")
        except KeyError:
            response['status'] = 'error'
            response['error'] = "Не передан обязательный параметр token"
            return HttpResponse(json.dumps(response), content_type="application/json")
        if token:
            user = Tokenaizer.objects.filter(token=token)
            if user:
                user = user.values('user').get()['user']
                response["status"] = "success"
                response["data"] = user
                response["token"] = token
                try:
                    user = User.objects.get(email=user)
                except:
                    user=''
                if user:
                    response['registered'] = True
                    if user.confirm:
                        response['confirmed'] = True
                    else:
                        response['confirmed'] = False
                        response['message'] = "Подтвердите свою почту и обновите страницу для доступа к" \
                                              " расширенному функционалу."
                else:
                    response['registered'] = False
            else:
                response["status"] = "error"
                response["error"] = "Переданный токен не зарегистрирован."
        else:
            response["status"] = "error"
            response["error"] = "У вас нет токена, создайте дело, чтобы узнать свое имя."
        return HttpResponse(json.dumps(response), content_type="application/json")



def gen_temp_username():
    # UnAuthUser
    username = Tokenaizer.objects.filter(user__contains=UNAUTHUSER).order_by('-user')
    if username:
        print(username[0].user.split(UNAUTHUSER)[1])
        username = UNAUTHUSER + str(int(username[0].user.split(UNAUTHUSER)[1]) + 1)
    else:
        username = UNAUTHUSER + str(0)
    return username


def gen_token(username):
    hash_cur_date = hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest()
    unhash = username + ' ' + str(hash_cur_date)
    return hashlib.sha256(unhash.encode('utf-8')).hexdigest()


def _hash_passw(hash_password):
    hash_password = hashlib.sha256(hash_password.encode('utf-8'))
    for i in range(HASH_PASSWORD_LVL):
        hash_password = hashlib.sha256(hash_password.hexdigest().encode('utf-8'))
    return hash_password.hexdigest()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip