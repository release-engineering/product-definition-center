#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings

from .messaging import DummyMessenger, KombuMessenger, FedmsgMessenger, ProtonMessenger, QpidMessenger


# init messenger
if settings.MESSAGE_BUS['MLP'] == 'kombu':
    messenger = KombuMessenger()
elif settings.MESSAGE_BUS['MLP'] == 'fedmsg':
    messenger = FedmsgMessenger()
elif settings.MESSAGE_BUS['MLP'] == 'proton':
    messenger = ProtonMessenger()
elif settings.MESSAGE_BUS['MLP'] == 'qpid':
    messenger = QpidMessenger()
else:
    messenger = DummyMessenger()
