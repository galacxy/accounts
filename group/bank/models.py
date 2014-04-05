from django.db import models

class user(models.Model):
        lastlogin = models.DateTimeField('Last Login')
        nick = models.CharField(max_length=30)
        password = models.CharField('password', max_length=255)
        name = models.CharField(max_length=50)
        email = models.EmailField(blank=True)
        contact = models.CharField(max_length=13, blank=True)
        balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
        fbUrl = models.URLField(blank=True)
        message = models.TextField(blank=True)
        def __str__(self):
                return self.nick


class transaction(models.Model):
        adder = models.CharField(max_length=30, verbose_name=" Added by")
        date = models.DateTimeField(auto_now=True)
        matterdate = models.DateField(verbose_name="Date", blank=True)
        matter = models.CharField(max_length=60, verbose_name='Occasion')
        matterID = models.CharField(max_length=15, verbose_name='Matter ID')
        flag = models.IntegerField(default=1)

        def __str__(self):  # Python 3: def __str__(self):
            return self.matterID

        class Meta:
            ordering = ["-matterdate"]

class entries(models.Model):
        TID = models.CharField(max_length=30, verbose_name='Transaction ID')
        UID = models.CharField(max_length=15, verbose_name='User ID')
        amt_spent = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
        amt_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
        dateid = models.IntegerField()

        def __str__(self):
            return str(self.TID + ' ' + self.UID)


class BankPayments(models.Model):
    PAYMENT_TYPE = (
        ('CR', 'Credit'),
        ('DB', 'Debit'),
    )
    adder = models.CharField(max_length=30, verbose_name=" Added by")
    UID = models.CharField(max_length=15, verbose_name='User')
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type = models.CharField(max_length=2, verbose_name="Type of Transaction", choices=PAYMENT_TYPE)
    paymentdate = models.DateTimeField(auto_now=True, verbose_name="Payment Date", )
    bankbalance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return str(self.paymentdate + ' ' + self.bankbalance)

    class Meta:
        ordering = ["paymentdate"]

class Messages(models.Model):
    MESSAGE_TYPE = (
        ('BT', 'Bank_Transaction'),
        ('NE', 'New_Event'),
    )
    msgsub = models.CharField(max_length=30)
    msgbody = models.TextField(verbose_name="Message Text")
    msgID = models.CharField(max_length=20, verbose_name="Message Type", choices=MESSAGE_TYPE)
    sender = models.CharField(max_length=30)
    recepient = models.CharField(max_length=30)
    moment = models.DateTimeField(auto_now_add=True, verbose_name="Sent Time");
    flag = models.IntegerField(default=1)
    status = models.SmallIntegerField(default=0)
    replyID = models.IntegerField(verbose_name="Reply for", default=0)
    # Create your models here.