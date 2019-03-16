from django.contrib import admin

# Register your models here.

from MainPage.models import Affairs,Categories,Icons,Logs

class AffairsAdmin(admin.ModelAdmin):
    list_display = ('id','start_date','start','end_date','end','user','category','text')
    list_filter = ('user',)

class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('id','name','user','color','icon','categories')
    list_filter = ('user',)

class LogsAdmin(admin.ModelAdmin):
    list_display = ('user','datetime','action','ip','browser')
    read_only = ('user','datetime','action','ip','browser')
    list_filter = ('user',)
admin.site.register(Affairs, AffairsAdmin)
admin.site.register(Categories, CategoriesAdmin)
admin.site.register(Icons)
admin.site.register(Logs,LogsAdmin)
