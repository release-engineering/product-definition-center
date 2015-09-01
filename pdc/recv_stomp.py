import time
import sys
import logging

import stomp

logger = logging.getLogger('stomp.py')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
logger.addHandler(ch)


class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error %s' % message)

    def on_message(self, headers, message):
        print('received a message %s' % message)

conn = stomp.Connection(
    host_and_ports=[
        ('fuse-fabric-01.host.stage.eng.rdu2.redhat.com', 61617),
        ('fuse-fabric-02.host.stage.eng.rdu2.redhat.com', 61617),
        ('fuse-fabric-03.host.stage.eng.rdu2.redhat.com', 61617),
        ('fuse-fabric-01.host.stage.eng.bos.redhat.com', 61617),
        ('fuse-fabric-02.host.stage.eng.bos.redhat.com', 61617),
    ],
    use_ssl=True,
    ssl_key_file='/home/jiahuang/Projects/PDC/cert/fuse-fabric-scratch.devel.engineering.redhat.com.key',
    ssl_cert_file='/home/jiahuang/Projects/PDC/cert/fuse-fabric-scratch.devel.engineering.redhat.com.crt',
)

conn.set_listener('MyDurableListener', MyListener())
conn.start()
conn.connect(headers={'client-id': 'pdc'})

conn.subscribe(destination='/topic/com.redhat.pdc.*', id=1, ack='auto',
               headers={'activemq.subscriptionName': 'pdc.compose'})

# NOTE: enlarge the number if you want to listen for a longer time.
for i in xrange(30):
    time.sleep(1)
conn.disconnect()
