# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

# this is temporary lol, idrk how to import external libraries w/ ansible plugins
# should be fixed with collections i think?
import sys
sys.path.append("/home/ontu/ansible/.venv/lib/python3.13/site-packages")

import sliver

import asyncio
import typing as t
import re
import gzip
import io

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleConnectionFailure
from ansible.module_utils.six import text_type, binary_type
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


# created once for every host we provision
class Connection(ConnectionBase):

    transport = 'sliver'
    has_pipelining = False

    sessionID = None
    client = None

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(Connection, self).__init__(*args, **kwargs)

        config = sliver.SliverClientConfig.parse_config_file(config_path)
        self.client = sliver.SliverClient(config)

    async def setSession(self):
        await self.client.connect()
        sessions = await self.client.sessions()
        self.session = sessions[0]
        self.sessionID = self.session.ID

    # _connect() is called whenever a new task is run
    # we only need the sessionID & clientID for the lifetime of the play
    # these vars are constant throughout the lifetime, so no need to regenerate for every task
    # i.e no connection management
    def _connect(self) -> Connection:
        config_path = self._play_context.config
        display.vvv(f"!!!! CONFIG PATH !!!!")
        display.vvv(f"!!!! CONFIG PATH !!!!")
        display.vvv(f"!!!! CONFIG PATH !!!!")
        display.vvv(f"!!!! CONFIG PATH !!!!")
        display.vvv(f"!!!! CONFIG PATH !!!!")
        display.vvv(f"{config_path}")

        config = sliver.SliverClientConfig.parse_config_file(config_path)
        self.client = sliver.SliverClient(config)
        return self

    async def asyncExecCommand(self, cmd: str) -> tuple[int, bytes, bytes]:
        await self.client.connect()
        interact = await self.client.interact_session(self.session.ID)
        
        match = re.search(r"'(.*?)'", cmd)
        inner = match.group(1)

        cmdRes = await interact.execute("/bin/sh", ['-c', f'{inner}'], True)
        return cmdRes.Status, cmdRes.Stdout.decode(), cmdRes.Stderr.decode()


    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return asyncio.run(self.asyncExecCommand(cmd))

    async def asyncPutFile(self, in_path: str, out_path: str) -> None:
        with open(in_path, 'rb') as f:
            contents = f.read()

        await self.client.connect()
        interact = await self.client.interact_session(self.session.ID)

        await interact.upload(out_path, contents)

    def put_file(self, in_path: str, out_path: str) -> None:
        return asyncio.run(self.asyncPutFile(in_path, out_path))

    async def asyncFetchFile(self, in_path: str, out_path: str) -> None:
        await self.client.connect()
        interact = await self.client.interact_session(self.session.ID)

        contents = await interact.download(in_path)
        with gzip.GzipFile(fileobj=io.BytesIO(contents.Data)) as f:
            decompressed_data = f.read()
            display.vvv(decompressed_data.decode())

        with open(out_path, 'wb') as f:
            f.write(decompressed_data)


    def fetch_file(self, in_path: str, out_path: str) -> None:
        return asyncio.run(self.asyncFetchFile(in_path, out_path))

    # see _connect()
    def reset(self) -> None:
        pass

    # see _connect()
    # we hold no resources
    def close(self) -> None:
        pass
