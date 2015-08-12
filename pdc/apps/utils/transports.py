#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import socket
from qpid.messaging import transports
from qpid.util import connect
from ssl import (wrap_socket, SSLError, CERT_REQUIRED, CERT_NONE)


class timeout_tls(transports.tls):
    def __init__(self, conn, host, port):
        self.socket = connect(host, port)
        if conn.tcp_nodelay:
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if conn.ssl_trustfile:
            validate = CERT_REQUIRED
        else:
            validate = CERT_NONE

        # set timeout for socket, in case it will hang forever
        self.socket.settimeout(conn.options.get('socket_timeout', 1))

        self.tls = wrap_socket(self.socket, keyfile=conn.ssl_keyfile,
                               certfile=conn.ssl_certfile,
                               ca_certs=conn.ssl_trustfile,
                               cert_reqs=validate)

        if validate == CERT_REQUIRED and not conn.ssl_skip_hostname_check:
            match_found = False
            peer_cert = self.tls.getpeercert()
            if peer_cert:
                peer_names = []
                if 'subjectAltName' in peer_cert:
                    for san in peer_cert['subjectAltName']:
                        if san[0] == 'DNS':
                            peer_names.append(san[1].lower())
                if 'subject' in peer_cert:
                    for sub in peer_cert['subject']:
                        while isinstance(sub, tuple) and isinstance(sub[0], tuple):
                            sub = sub[0]   # why the extra level of indirection???
                        if sub[0] == 'commonName':
                            peer_names.append(sub[1].lower())
                for pattern in peer_names:
                    if transports._match_dns_pattern(host.lower(), pattern):
                        match_found = True
                        break
            if not match_found:
                raise SSLError("Connection hostname '%s' does not match names from peer certificate: %s" % (host, peer_names))

        self.socket.setblocking(0)
        self.state = None
        # See qpid-4872: need to store the parameters last passed to
        # tls.recv_into() and tls.write() in case the calls fail with an
        # SSL_ERROR_WANT_* error and we have to retry the call.
        self.write_retry = None   # buffer passed to last call of tls.write()
        self.read_retry = None    # buffer passed to last call of tls.recv_into()


transports.TRANSPORTS['ssl'] = timeout_tls
transports.TRANSPORTS['tcp+tls'] = timeout_tls
