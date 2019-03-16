from django.db.models import *
from Users.models import User
from datetime import datetime


class Icons(Model):
    class Meta:
        db_table = 'icon'
        verbose_name_plural = 'Иконки'

    path = CharField(max_length=150)
    user = CharField(max_length=50)

    def __str__(self):
        return "{}".format(self.path)


class Logs(Model):
    class Meta:
        db_table = 'log'
        verbose_name_plural = "Логи"

    user = CharField(max_length=50)
    datetime = DateTimeField()
    action = TextField()
    ip = CharField(max_length=16)
    browser = TextField()

    # def __str__(self):
    #    return "{} {} {} {}".format(self.user.values('username')[0].get('username'), self.l_datetime, self.l_action,
    #                                                               self.l_browser)


class Categories(Model):
    class Meta:
        verbose_name_plural = "Категории"
        db_table = 'category'

    name = CharField(max_length=50)
    icon = ForeignKey(Icons, on_delete=CASCADE)
    user = CharField(max_length=50)
    categories = IntegerField(default=0,blank=True)#ForeignKey('self',on_delete=SET_NULL)
    color = IntegerField()
    fast_access = BooleanField(default=False)
    fast_access_index = IntegerField(blank=True, null=True)

    def __str__(self):
        return "%s" % self.name

    def id(self):
        return self.id

class Affairs(Model):
    class Meta:
        db_table = 'affair'
        verbose_name = 'Дело'
        verbose_name_plural = 'Дела'

    start_date = IntegerField(blank=True, null=True)
    end_date = IntegerField(blank=True, null=True)
    start = IntegerField(blank=True, null=True)
    end = IntegerField(blank=True, null=True)
    start_timestamp = IntegerField(blank=True, null=True)
    duration = IntegerField(blank=True, null=True)
    category = ForeignKey(Categories, on_delete=CASCADE)
    user = CharField(max_length=50)
    complexity = IntegerField(default=0, null=True)
    text = CharField(max_length=50, blank=True, null=True)
    importance = IntegerField(default=0, null=True)
    status = CharField(max_length=50, default="", null=True,blank=True)
    notifications = BooleanField(default=0, null=True)
    notification_time = IntegerField(blank=True, null=True)
    period = IntegerField(blank=True, null=True)


    def id(self):
        return self.id


class Paterns(Model):
    class Meta:
        db_table = 'patern'
        verbose_name_plural = "Шаблоны"

    icon = IntegerField()
    name = CharField(max_length=50)
    affairs = TextField()
    user = CharField(max_length=50)
    fast_access = BooleanField(default=0,blank=True)
    fast_access_index = IntegerField(blank=True,null=True)
