

import random
from django.core.mail import send_mail
from django.conf import settings

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    return otp
