from MainPage.models import Categories
from MainPage.serializer import CategoriesAddSerializer
from TimeManagement.settings import DEBUG, MEDIA_DIR
from django.db.models import Q
import os

def default_categs(username):
    def_categs = Categories.objects.filter(~Q(id=0), user='all')
    for i in def_categs:
        i.user = username
        i.__dict__.pop('id')
        i.__dict__['icon'] = i.__dict__['icon_id']
        serializer = CategoriesAddSerializer(data=i.__dict__)
        if serializer.is_valid(raise_exception=DEBUG):
            serializer.save()

def create_dir(username):
    try:
        os.makedirs(os.path.join(MEDIA_DIR,username))
        return False
    except FileExistsError:
        return False
    except:
        return True