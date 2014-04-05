from django.contrib import admin
from bank.models import *

class userAdmin(admin.ModelAdmin):
    list_display = ('nick', 'name', 'balance', 'lastlogin',)
    list_filter = ('nick', 'balance', 'lastlogin')
    search_fields = ('nick', 'name')
    ordering = ('-lastlogin',)

class entriesAdmin(admin.ModelAdmin):
    list_display = ('id','TID','UID','amt_spent', 'amt_paid',)
    #list_filter = ('publication_date',)
    #list _filter = ('UID','TID','amt_paid',)
    search_fields = ('UID','TID',)

class transAdmin(admin.ModelAdmin):
    list_display = ('id', 'matterID', 'matter', 'matterdate')
    list_filter = ('date',)
    search_fields = ('matterID', 'date',)

class messageAdmin(admin.ModelAdmin):
    list_display = ('msgID', 'msg',)
    list_filter = ('msgID',)
    search_fields = ('msgID',)

admin.site.register(user, userAdmin)
admin.site.register(transaction, transAdmin)
admin.site.register(entries, entriesAdmin)


# Register your models here.
