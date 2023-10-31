#!/usr/bin/env python

import pexpect
import sys


class SSH:
    DEFAULT_PROMPT = "rkscli: "
    SHELL_PROMPT = "# "
    LOGIN_PROMPT = "login: "
    PASSWORD_PROMPT = "password : "
    SSH_CMD = "ssh -q -o 'StrictHostKeyChecking=no' -p {port} {host}"

    def __init__(self, host, port=22, username=None, password=None, timeout=30, debug=False) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.debug = debug
        self.current_prompt = None
        self.conn = None
    
    def _connect(self):
        child = pexpect.spawn(self.SSH_CMD.format(host=self.host, port=self.port))
        if self.debug:
            child.logfile = sys.stdout.buffer
        
        child.expect(self.LOGIN_PROMPT)
        child.sendline(self.username)
        child.expect(self.PASSWORD_PROMPT)
        child.sendline(self.password)
        child.expect(self.DEFAULT_PROMPT)
        self.current_prompt = self.DEFAULT_PROMPT
        self.conn = child
    
    def __enter__(self):
        if not self.conn:
            self._connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()

    def rkscli(self, cmd, timeout=30, no_expect=False):
        if self.current_prompt == self.SHELL_PROMPT:
            self.conn.sendline('rkscli')
            self.conn.expect(self.DEFAULT_PROMPT)
            self.current_prompt = self.DEFAULT_PROMPT
        
        self.conn.sendline(cmd)
        if no_expect:
            return ''
        self.conn.expect(self.DEFAULT_PROMPT, timeout=timeout)
        return self.conn.before

    def linuxcli(self, cmd, timeout=30, no_expect=False):
        if self.current_prompt == self.DEFAULT_PROMPT:
            self.conn.sendline('!v54!')
            self.conn.expect(self.SHELL_PROMPT)
            self.current_prompt = self.SHELL_PROMPT

        self.conn.sendline(cmd)
        if no_expect:
            return ''
        self.conn.expect(self.SHELL_PROMPT, timeout=timeout)
        return self.conn.before

    def scp(self, src, dst, password, timeout=30):
        scp_cmd = "scp {src} {dst}".format(src=src, dst=dst)
        self.linuxcli('')
        self.conn.sendline(scp_cmd)
        i = self.conn.expect(['Do you want to continue connecting.*', 'password:'], timeout=timeout)

        if i == 0:
            self.conn.sendline('y')
            self.conn.expect('password:')
            i = 1
        if i == 1:
            self.conn.sendline(password)

        self.conn.expect(self.SHELL_PROMPT, timeout=timeout)
        return True

    def reboot(self):
        self.rkscli('reboot')
        self.rkscli('exit', no_expect=True)

    def factory_reset(self):
        self.rkscli('set factory')
        self.reboot()

    def get_version(self):
        raw = self.rkscli('get version')
        v = raw.decode().split()
        return v[v.index('Version:')+1]
    
    def get_serial(self):
        raw = self.rkscli('get boarddata')
        v = raw.decode().split()
        return v[v.index('Serial#:')+1]

