from django.contrib import admin
from .models import User,Tokenaizer,Confirmed
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'confirm', 'password')
    readonly_fields = ('password',)
class ConfirmAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'key', 'user')

class TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token')


admin.site.register(User,UserAdmin)
admin.site.register(Confirmed,ConfirmAdmin)
admin.site.register(Tokenaizer,TokenAdmin)