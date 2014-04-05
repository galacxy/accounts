from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('bank.views',
    url(r'^$', 'home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/$', 'login_user', name='login_user'),
    url(r'^user/home/$', 'home_user', name='home_user'),
    url(r'^user/profile/$', 'profile', name='profile'),
    url(r'^user/inbox/$', 'inbox', name='inbox'),
    url(r'^user/outbox/$', 'outbox', name='outbox'),
    url(r'^user/message/(?P<msgid>\w+)/$', 'view_msg', name='view_msg'),
    url(r'^user/compose/$', 'compose_message', name='compose_message'),
    url(r'^user/addtrans/$', 'addtrans', name='addtrans'),
    url(r'^user/addtransdetails/$', 'addtransdetails', name='addtransdetails'),
    url(r'^users/alltrans/$', 'alltrans', name='alltrans'),
    url(r'^users/occasions/(?P<transid>[\w!@#$%^&*()<>?,./ ]+)/(?P<dateid>[\d-]+)/$', 'showtrans', name='showtrans'),
    url(r'^users/occasions/edit/(?P<transid>[\w!@#$%^&*()<>?,./ ]+)/(?P<dateid>[\d-]+)/$', 'edittrans', name='edittrans'),
    url(r'^user/logout/$', 'logout', name='logout'),
    url(r'^user/(?P<userid>\w+)/$', 'changepassword', name='chpwd'),
    url(r'^user/edit/(?P<userid>\w+)/$', 'editprofile', name='editprofile'),
    url(r'^signup/$', 'newuser', name='newuser'),
)
#url(r'^articles/(?P<year>\d{4})/$', 'news.views.year_archive'),
