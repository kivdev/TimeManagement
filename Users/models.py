from django.db.models import (Model, CharField,
                              TextField, IntegerField,
                              ForeignKey, CASCADE,
                              DateTimeField, BooleanField, DO_NOTHING)



# Create your models here.


class User(Model):
    class Meta:
        db_table = 'user'

    email = CharField(max_length=126)
    password = TextField(max_length=254)
    confirm = BooleanField(default=False,blank=True)
    is_admin = BooleanField(blank=True)
    is_staff = BooleanField(blank=True)

    def __str__(self):
        return str(self.email)


class Confirmed(Model):
    class Meta:
        db_table = 'confirmed'
    timestamp = CharField(max_length=15)
    key = CharField(max_length=126, null=False, blank=False)
    user = CharField(max_length=50)



class Tokenaizer(Model):
    class Meta:
        db_table = 'tokenaizer'

    user = CharField(max_length=50)
    token = TextField(max_length=254, unique=True)
    last_login = DateTimeField(blank=True, auto_now_add=True)

    def __str__(self):
        return '%s  -  %s' % (self.user, self.token)
