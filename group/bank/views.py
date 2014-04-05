from django.shortcuts import render_to_response
from django.shortcuts import render
from django.http import HttpResponseRedirect
from bank.models import *
from recaptcha.client import captcha
from django.contrib.auth.hashers import *
import time
from django.db.models import *

import re
import datetime


def home(request):
    return render_to_response('index.html')


def login_user(request):
    error = ''
    if request.POST:
        username = request.POST.get('username')
        passwrd = request.POST.get('password')
        flag = 0
        if username == '':
            error = "Please enter your username !"
        elif passwrd == '':
            error = "Please enter your password  !"
        else:
            usr = user.objects.filter(nick=username).exists()
            if usr:
                usr = user.objects.get(nick=username)
                pwd = check_password(passwrd, usr.password)
                if pwd:
                    request.session[username] = username
                    request.session['message'] = "Hey, " + username + ".\n You're logged in!"
                    request.session['user'] = username
                    request.session['firstlogin'] = True
                    return HttpResponseRedirect("/user/home/")
            if flag == 0:
                error = "Your username and/or password was incorrect."
        data = dict(today=time.strftime("%d-%m-%Y"), error=error, username=username)
        return render(request, 'user/log_in.html/', data)
    data = dict(today=time.strftime("%d-%m-%Y"), error=error)
    return render(request, 'user/log_in.html/', data)


def home_user(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        person = user.objects.get(nick=request.session['user'])
        if request.session['firstlogin']:
            request.session['logintime'] = datetime.datetime.now().isoformat()
            request.session['firstlogin'] = False
        message = request.session['message']
        request.session['message'] = ''
        entry = entries.objects.all().filter(UID=person.nick).order_by('-id')
        bankpyt = BankPayments.objects.all().filter(UID=person.nick).order_by('-paymentdate')
        paid = spent = payment = 0
        dues = recovery = 0
        paid_values = entries.objects.all().filter(UID=person.nick).aggregate(total=Sum('amt_paid'))
        spent_values = entries.objects.all().filter(UID=person.nick).aggregate(total=Sum('amt_spent'))
        if paid_values['total']:
            paid = paid_values['total']
        if spent_values['total']:
            spent = spent_values['total']
        for pyt in bankpyt:
            if pyt.type == 'CR':
                payment += pyt.paid
            elif pyt.type == 'DB':
                payment -= pyt.paid
        sum = paid - payment - spent
        if sum > 0:
            recovery = sum
        else:
            dues = -sum
        count = Messages.objects.filter(recepient=person.nick, status=0).count()
        tran = transaction.objects.filter(id__in=(entries.objects.filter(UID=person.nick).values('dateid'))).order_by('-matterdate')
        occrows = zip(entry, tran)
        money = dict(paid=paid, spent=spent, dues=dues, recovery=recovery, payment=1 * payment)
        data = dict(money=money, today=time.strftime("%d/%m/%Y"), occrows=occrows, bankrows=bankpyt, user=person, message=message, msg_count=count)
        return render_to_response('user/index.html', data)

def profile(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        person = user.objects.get(nick=request.session['user'])
        today = time.strftime("%d/%m/%Y")
        message = request.session['message']
        count = Messages.objects.filter(recepient=person.nick, status=0).count()
        return render_to_response('user/profile.html', dict(person=person, today=today, message=message, msg_count=count))

def check_unique_trans(occasion, date):
    return transaction.objects.filter(matterID=occasion, matterdate=date).exists()

def addtrans(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        users = []
        state = error = ''
        data = {}
        request.session['message'] = error
        if 'user' in request.session:
            data = {'adder': request.session['user']}
            users = user.objects.all()
            if request.POST:
                members = request.POST.getlist('member')
                occasionid = request.POST.get('occid')
                occasion = request.POST.get('occ')
                date = request.POST.get('datepicker')
                response = captcha.submit(
                    request.POST.get('recaptcha_challenge_field'),
                    request.POST.get('recaptcha_response_field'),
                    ['6Le-v-4SAAAAAIyExFArNcVjif6TM5-0ZLz9v6KN'],
                    request.META['REMOTE_ADDR'], )
                if date and date[4] != '-':
                    mon = date[0:2]
                    day = date[3:5]
                    yr = date[6:10]
                    date = yr + '-' + mon + '-' + day
                data['occasionid'] = occasionid
                data['occasion'] = occasion
                data['date'] = date
                expense = paid = []
                for i in range(1, len(members) + 1):
                    expense.append('')
                    paid.append('')
                data['values'] = zip(members, expense, paid)
                if date == '':
                    error = '*Please fill in date'
                elif occasionid == '':
                    error = '*Please fill in occasion'
                elif check_unique_trans(occasionid, date):
                    error = '*Occasion already exists on this date. Choose a different one'
                elif len(occasion) < 10:
                    error = '*Provide at least 10 characters in the description'
                elif not members:
                    error = '*Please select atleast one member'
                #elif not response.is_valid:
                    #error = 'Enter the captcha value correctly'
                else:
                    newtran = transaction.objects.create(adder=data['adder'], matterID=occasionid.title(), matter=occasion, matterdate=date)
                    newtran.save()
                    request.session['data'] = data
                    return HttpResponseRedirect("/user/addtransdetails")
                state = ''
        else:
            state = "*You are not authorised to view this page."
        count = Messages.objects.filter(recepient=data['adder'], status=0).count()
        values = dict(users=users, state=state, data=data, error=error, today=time.strftime("%d-%m-%Y"), msg_count=count)
        return render(request, 'user/newaddtrans.html', values)


def is_number(s):
    try:
        int(s)
        val1 = True
    except ValueError:
        val1 = False
    try:
        float(s)
        val2 = True
    except ValueError:
        val2 = False
    return val1 or val2

def cleanup():
    entry = entries.objects.values_list('TID', flat=True).distint()
    trans = transaction.objects.values_list('id', flat=True)
    for tr in trans:
        if tr not in entry:
            transaction.objects.filter(id=tr).delete()

def addtransdetails(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        state = error = ''
        data = {}
        if 'data' in request.session:
            data = request.session['data']
            occasionid = data['occasionid']
            if 'values' not in data:
                state = 'Entries not fulfilled on previous page'
            elif request.POST:
                values = data['values']
                expense = request.POST.getlist('expense')
                paid = request.POST.getlist('paid')
                members = zip(*values)[0]
                values = zip(members, expense, paid)
                data['values'] = values
                total_expense = 0
                total_paid = 0
                for nk, ex, pd in values:
                    if not ex:
                        error = "*Please fill in Expenditure values completely"
                    elif not pd:
                        error = "*Please fill in Paid values completely"
                    else:
                        if not is_number(ex):
                            error = "*Expense values should consist of numbers only"
                        elif not is_number(pd):
                            error = "*Paid values should consist of numbers only"
                        else:
                            total_expense += float(ex)
                            total_paid += float(pd)
                if not error:
                    if total_expense != 0 and total_paid != 0 and (total_expense != total_paid):
                        error = "*Total Expense amount and Total Paid amount do not match"
                        data['total_paid'] = total_paid
                        data['total_expense'] = total_expense
                    else:
                        date = data['date']
                        tid = transaction.objects.get(matterID=occasionid, matterdate=date)
                        for nk, ex, pd in values:
                            uid = user.objects.get(nick=nk)
                            newentry = entries.objects.create(TID=tid.matterID, UID=uid.nick, amt_spent=ex, amt_paid=pd, dateid=tid.id)
                            newentry.save()
                            msub = data['occasionid'] + ' Billing'
                            mbody = 'You paid Rs. ' + pd + ' and spent Rs. ' + ex + ' at ' + data['occasionid']
                            newmessage = Messages.objects.create(msgbody=mbody, msgsub=msub, recepient=uid.nick,
                                                                 sender=request.session['user'])
                            newmessage.save()
                            usr = user.objects.get(nick=nk)
                            bal = float(usr.balance) + float(pd) - float(ex)
                            user.objects.filter(nick=nk).update(balance=bal)
                        del request.session['data']
                        request.session['message'] = 'Data saved successfully!'
                        request.session.modified = True
                        return HttpResponseRedirect("/user/home/")
        else:
            state = "You are not allowed to view this page"
        count = Messages.objects.filter(recepient=data['adder'], status=0).count()
        return render(request, 'user/newaddtransdetails.html', dict(today=time.strftime("%d-%m-%Y"), data=data, state=state, error=error, msg_count=count))

def alltrans(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    elif 'user' in request.session:
        request.session['message'] = ''
        item = ''
        if request.POST:
            item = request.POST.get('editbox_search')
            trans = transaction.objects.filter(matterID__icontains=item, flag=1).order_by('-date')
        else:
            trans = transaction.objects.filter(flag=1).order_by('-date')
        total = []
        for tr in trans:
            val = entries.objects.values_list('amt_spent', flat=True).filter(TID=tr.matterID, dateid=tr.id)
            amt = 0
            for v in val:
                amt += float(v)
            total.append(amt)
        transactions = zip(trans, total)
        count = Messages.objects.filter(recepient=request.session['user'], status=0).count()
        data = dict(today=time.strftime("%d-%m-%Y"), user=request.session['user'], transactions=transactions, search_item=item, msg_count=count)
        return render(request, 'newalltrans.html', data)


def signingoff(request):
    try:
        if 'user' in request.session:
            person = request.session['user']
            user.objects.filter(nick=person).update(lastlogin=request.session['logintime'])
            del request.session['user']
        request.session.flush()
    except KeyError:
        request.session['message'] = 'There is some error signing off'
    return

def logout(request):
    signingoff(request)
    request.session['message'] = 'You have been logged out'
    return render_to_response('user/log_out.html', {'message': request.session['message']})

def showtrans(request, transid, dateid):
    trans = transaction.objects.get(matterID=transid, id=dateid)
    entry = entries.objects.filter(TID=transid, dateid=dateid)
    count = Messages.objects.filter(recepient=request.session['user'], status=0).count()
    data = dict(trans=trans, entry=entry, user=request.session['user'], today=time.strftime("%d-%m-%Y"), msg_count=count)
    return render_to_response('newshowtrans.html', data)


def edittrans(request, transid, dateid):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    elif 'user' in request.session:
        state = error = ''
        transdate = transaction.objects.get(matterID=transid, id=dateid).matterdate
        entry = entries.objects.all().filter(TID=transid, dateid=dateid)
        balance = []
        bk_pyt = []
        typo = []
        for en in entry:
            balance.append(user.objects.get(nick=en.UID).balance)
            bk_pyt.append(0)
        values = zip(entry, bk_pyt, balance)
        if request.POST:
            bk_pyt = request.POST.getlist('bk_pyt')
            typo = request.POST.getlist('typo')
            values = zip(entry, bk_pyt, balance)
            for usr, pd, tp in values:
                if not pd:
                    error = " Please fill in values completely"
                elif not is_number(pd):
                    error = " Values should consist of numbers only"
            if not error:
                nonzero = 0
                total = 0
                for usr, pd, tp in values:
                    total += 1
                    if float(pd) != 0:
                        nonzero += 1
                        if BankPayments.objects.filter(UID=usr.UID).exists():
                            bankentry = BankPayments.objects.filter(UID=usr.UID).order_by('-paymentdate')[:1]
                            bal = float(bankentry[0].bankbalance) + (float(pd) if tp == 'CR' else -float(pd))
                        else:
                            bal = 0                                                                   # make field as auto_now_add
                        newpayment = BankPayments.objects.create(UID=usr.UID, paid=float(pd), type=tp, paymentdate=datetime.datetime.now(), adder=request.session['user'], bankbalance=bal)
                        newpayment.save()
                        type_of_payment = 'debit'
                        if tp == 'CR':
                            type_of_payment = 'credit'
                            pd = -float(pd)
                        bal = float(user.objects.get(nick=usr.UID).balance) + float(pd)
                        user.objects.filter(nick=usr.UID).update(balance=bal)
                        msub = 'Bank transaction'
                        mbody = 'An amount of Rs. ' + str(pd) + ' has been ' + type_of_payment + 'ed to your account'+ '. \n'
                        if bal == 0:
                            mbody += 'Enjoy zero balance. :)\n'
                        else:
                            mbody += 'Your clear balance is ' + str(bal) + '. \n'
                            if bal < 0:
                                mbody = 'An amount of Rs. ' + str(pd)[1:] + ' has been ' + type_of_payment + 'ed to your account' + '. \n'
                                mbody += 'Please pay Rs ' + str(bal)[1:] + ' as early as possible'
                            else:
                                mbody += 'You are entitled to recieve Rs. ' + str(bal) + ' from bank. Be with us.'
                        newmessage = Messages.objects.create(msgbody=mbody, msgsub=msub, recepient=usr.UID, sender=request.session['user'])
                        newmessage.save()
                        #bankentry = BankPayments.objects.all().order_by('-paymentdate')[1:2]
                request.session['message'] = str(nonzero) + ' out of ' + str(total) + ' payment(s) saved'
                return HttpResponseRedirect("/user/home/")
        count = Messages.objects.filter(recepient=request.session['user'], status=0).count()
        event = dict(occasion=transid, date=transdate, today=time.strftime("%d-%m-%Y"), msg_count=count)
        forward_values = dict(adder=request.session['user'], state=state, event=event, values=values, error=error)
        return render(request, 'user/newedittrans.html', forward_values)

def changepassword(request, userid):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        error = ''
        usr = user.objects.get(nick=userid)
        data = dict(nick=usr.nick, today=time.strftime("%d-%m-%Y"), error=error)
        if request.POST:
            old = request.POST.get('oldpassword')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            if not old:
                error = "Enter your old password first "
            elif not password:
                error = "Enter your new password"
            elif not password2:
                error = "Confirm new password "
            elif len(password) <= 8:
                error = "Password should have atleast 8 characters"
            elif check_password(old, usr.password):
                error = "Incorrect Old Password"
            elif password != password2:
                error = "You did not confirmed your password correctly"
            else:
                pwd = make_password(password)
                user.objects.filter(nick=usr.nick).update(password=pwd)
                request.session['message'] = "Password changed successfully"
                return HttpResponseRedirect('/user/profile')
            data = dict(nick=usr.nick, today=time.strftime("%d-%m-%Y"), error=error, oldp=old)
        return render(request, 'user/chpwd.html', data)

def newuser(request):
    if request.POST:
        nick = request.POST.get('nick')
        name = request.POST.get('name')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        response = captcha.submit(
            request.POST.get('recaptcha_challenge_field'),
            request.POST.get('recaptcha_response_field'),
            ['6Le-v-4SAAAAAIyExFArNcVjif6TM5-0ZLz9v6KN'],
            request.META['REMOTE_ADDR'], )
        if not nick:
            error = "Choose your username "
        elif not name:
            error = "Enter your name"
        elif user.objects.filter(nick=nick).exists():
            error = 'Username already exists!.'
        elif not password:
            error = "Enter your password "
        elif len(password) < 8:
            error = "Password should have atleast 8 characters"
        elif password != password2:
            error = "Confirm your password correctly"
        elif not response.is_valid:
            error = 'Enter the captcha value correctly'
        else:
            pwd = make_password(password)
            user.objects.create(lastlogin=datetime.datetime.now(), nick=nick, name=str(name).title(), password=pwd)
            request.session['message'] = "Account created. Login below"
            return HttpResponseRedirect('/users')
        data = dict(today=time.strftime("%d-%m-%Y"), error=error, nick=nick, name=name)
        return render(request, 'newuser.html', data)
    data = dict(today=time.strftime("%d-%m-%Y"))
    return render(request, 'newuser.html', data)

def editprofile(request, userid):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        error = ''
        request.session['message'] = ''
        usr = user.objects.get(nick=userid)
        person = dict(nick=usr.nick, name=usr.name.title(), contact=usr.contact, email=usr.email)
        data = dict(person, today=time.strftime("%d-%m-%Y"), error=error)
        if request.POST:
            name = request.POST.get('name')
            email = request.POST.get('email')
            contact = request.POST.get('contact')
            password = request.POST.get('password')
            person.clear()
            data.clear()
            exp = '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
            if not name:
                error = 'Name cannot be empty'
            elif email and not re.match(exp, email):
                error = "Enter a valid email "
            elif contact and not is_number(contact):
                error = "Contact should contain digits only"
            elif contact and not re.match('^[789]', contact):  # contact[0] != 9 or contact[0] != 8 or contact[0] != 7):
                    error = "Enter a valid contact"
            elif contact and len(contact) != 10:
                    error = "A valid contact consists of 10 digits"
            elif name != usr.name or email != usr.email or contact != usr.contact:
                if not password:
                    error = "Enter your password"
                elif not check_password(password, usr.password):
                    error = "Incorrect Password"
                else:
                    user.objects.filter(nick=usr.nick).update(name=str(name).title(), email=email, contact='+91' + contact)
                    request.session['message'] = "Changes saved successfully"
                    return HttpResponseRedirect('/user/profile')
            else:
                request.session['message'] = 'No changes committed'
                return HttpResponseRedirect('/user/profile')
            person = dict(nick=usr.nick, name=name.title(), contact=contact, email=email)
            count = Messages.objects.filter(recepient=request.session['user'], status=0).count()
            data = dict(person, today=time.strftime("%d-%m-%Y"), error=error, msg_count=count)
        return render(request, 'user/editprofile.html', data)

def inbox(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        usr = user.objects.get(nick=request.session['user'])
        message = request.session['message']
        request.session['message'] = ''
        msgs = Messages.objects.filter(recepient=usr.nick).order_by('-moment')
        count = len(msgs.filter(status=0))
        data = dict(user=usr, messages=msgs, today=time.strftime("%d-%m-%Y"), msg_count=count, message=message)
        return render(request, 'user/messages.html', data)

def outbox(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        usr = user.objects.get(nick=request.session['user'])
        message = request.session['message']
        request.session['message'] = ''
        msgs = Messages.objects.filter(sender=usr.nick).order_by('-moment')
        count = Messages.objects.filter(recepient=usr.nick, status=0).count()
        data = dict(user=usr, messages=msgs, today=time.strftime("%d-%m-%Y"), msg_count=count, message=message)
        return render(request, 'user/outbox.html', data)


def compose_message(request):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        recepients = user.objects.values_list('nick', flat=True)
        usr = request.session['user']
        count = Messages.objects.filter(recepient=usr, status=0).count()
        if request.POST:
            recp = request.POST.get('recp')
            msub = request.POST.get('msgsub')
            mbody = request.POST.get('msgbody')
            if not msub:
                msub = mbody[:20] + '...'
            Messages.objects.create(msgbody=mbody, msgsub=msub, msgID='TP', sender=usr, recepient=recp)
            request.session['message'] = 'Message succssfully sent.'
            return HttpResponseRedirect('/user/inbox/')
    data = dict(rec=recepients, user=usr, recepients=recepients, today=time.strftime("%d-%m-%Y"), msg_count=count)
    return render(request, 'user/newmessage.html', data)


def view_msg(request, msgid):
    if 'user' not in request.session:
        request.session['message'] = 'You have already logged out'
        return HttpResponseRedirect('/user/logout/')
    else:
        usr = user.objects.get(nick=request.session['user'])
        msgs = Messages.objects.get(id=msgid)
        Messages.objects.filter(id=msgid).update(status=1)
        count = Messages.objects.filter(recepient=request.session['user'], status=0).count()
        data = dict(user=usr, message=msgs, today=time.strftime("%d-%m-%Y"), msg_count=count)
        return render(request, 'user/view_message.html', data)

# Create your views here.
#<a href="/signup/">New User</a>&nbsp;&nbsp;<a href="#">Forgot your password?</a>