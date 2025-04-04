# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

# this is temporary lol, idrk how to import external libraries w/ ansible plugins
# should be fixed with collections i think?
import sys
sys.path.append("/home/ontu/ansible/.venv/lib/python3.13/site-packages")

import sliver

import functools
import getpass
import os
import pty
import selectors
import shutil
import subprocess
import time
import asyncio
import typing as t
import re

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleConnectionFailure
from ansible.module_utils.six import text_type, binary_type
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


class Connection(ConnectionBase):

    transport = 'sliver'
    has_pipelining = False
    session = None
    client = None
    interact = None

    async def makeConnection(self):
        # CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
        # DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "ansible_127.0.0.1.cfg")
        # config = sliver.SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
        # self.client = sliver.SliverClient(config)
        # # display.vvv('[*] Connected to server ...')
        # await self.client.connect()
        # sessions = await self.client.sessions()
        # # display.vvv('[*] Sessions: %r' % sessions)
        # if len(sessions):
        #     # display.vvv('[*] Interacting with session', sessions[0].ID)
        #     self.interact = await self.client.interact_session(sessions[0].ID)
        #     ls = await self.interact.execute('whoami', [], True)
        #     # display.vvv(ls.Stdout.decode())
        #     self.session = sessions[0]
        pass


    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(Connection, self).__init__(*args, **kwargs)

    def _connect(self) -> Connection:
        # # display.vvv("in connect()")
        # asyncio.run(self.makeConnection())
        return self

    async def asyncExecCommand(self, cmd: str) -> tuple[int, bytes, bytes]:
        # display.vvv("in asyncexec")
        CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
        DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "ansible_127.0.0.1.cfg")
        config = sliver.SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
        self.client = sliver.SliverClient(config)
        # display.vvv('[*] Connected to server ...')
        await self.client.connect()
        sessions = await self.client.sessions()
        # display.vvv('[*] Sessions: %r' % sessions)
        if len(sessions):
            # display.vvv('[*] Interacting with session', sessions[0].ID)
            self.interact = await self.client.interact_session(sessions[0].ID)

            contents = b"#!/bin/sh\n" + cmd.encode() + b"\n"
            # contents = b"#!/bin/sh\nwall \"" + cmd.encode() + b"\"\n" + cmd.encode()
            if b"rm -f -r" in contents:
                return 0, "", ""

            await self.interact.upload('/tmp/troll.sh', contents)
            cmdRes = await self.interact.execute("/tmp/troll.sh", [], True)
            # display.vvv(cmdRes.Stdout.decode())
            self.session = sessions[0]
        # display.vvv("ran exe")
        # display.vvv(cmdRes.Stdout.decode())
        return cmdRes.Status, cmdRes.Stdout.decode(), cmdRes.Stderr.decode()


    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        # display.vvv("in exec_command()")
        display.vvv(f"cmd: {cmd}")

        ret = asyncio.run(self.asyncExecCommand(cmd))
        display.vvv(f"res: {ret}")

        return ret

    async def asyncPutFile(self, in_path: str, out_path: str) -> None:
        # display.vvv("in asyncexec")
        display.vvv(f"uploading to {out_path}")
        display.vvv(f"uploading to {out_path}")
        display.vvv(f"uploading to {out_path}")
        display.vvv(f"uploading to {out_path}")
        CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
        DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "ansible_127.0.0.1.cfg")
        config = sliver.SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
        self.client = sliver.SliverClient(config)
        # display.vvv('[*] Connected to server ...')
        await self.client.connect()
        sessions = await self.client.sessions()
        # display.vvv('[*] Sessions: %r' % sessions)
        if len(sessions):
            # display.vvv('[*] Interacting with session', sessions[0].ID)
            self.interact = await self.client.interact_session(sessions[0].ID)

            with open(in_path, 'rb') as f:
                contents = f.read()
            # contents = contents.encode()
            # contents = b"#!/bin/sh\n" + b"wall HAHA" + b"\n"
            # contents = b"#!/bin/sh\nwall \"" + cmd.encode() + b"\"\n" + cmd.encode()
            # if b"rm -f -r" in contents:
            #     return 0, "", ""

            display.vvv(f"uploading to {out_path}")
            await self.interact.upload(out_path, contents)
            # cmdRes = await self.interact.execute("/tmp/troll.sh", [], True)
            # display.vvv(cmdRes.Stdout.decode())
            self.session = sessions[0]
        # display.vvv("ran exe")
        # display.vvv(cmdRes.Stdout.decode())
        return
        # return cmdRes.Status, cmdRes.Stdout.decode(), cmdRes.Stderr.decode()

    def put_file(self, in_path: str, out_path: str) -> None:
        return asyncio.run(self.asyncPutFile(in_path, out_path))

    async def asyncFetchFile(self, in_path: str, out_path: str) -> None:
        # CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
        # DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "ansible_127.0.0.1.cfg")
        # config = sliver.SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
        # self.client = sliver.SliverClient(config)
        # # display.vvv('[*] Connected to server ...')
        # await self.client.connect()
        # sessions = await self.client.sessions()
        # # display.vvv('[*] Sessions: %r' % sessions)
        # contents = await self.interact.download(in_path)

        # with open(in_path, 'wb') as file:
        #     file.write(contents)\"
        pass


    def fetch_file(self, in_path: str, out_path: str) -> None:
        pass
        # return asyncio.run(self.asyncFetchFile(in_path, out_path))

    def reset(self) -> None:
        pass

    def close(self) -> None:
        pass
