# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import asyncio
import typing as t
import gzip
import io
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.errors import AnsibleError

try:
    import sliver
except ImportError:
    raise AnsibleError("sliver-py is required for this plugin! pip install sliver-py")


DOCUMENTATION = """
    name: sliver
    author: UFSIT BlueTeam

    short_description: connect via a sliver c2 connection

    options:
      password:
        description: The STS access key to use when connecting via session-manager.
        env:
        - name: ansible_ssh_pass
"""

display = Display()

# created once for every host we provision
class Connection(ConnectionBase):

    transport = 'sliver'
    has_pipelining = False

    sessionID = None
    client = None

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(Connection, self).__init__(*args, **kwargs)

        remote = self._play_context.remote_addr
        display.v(f"Remote Address: {remote}")

        configPath = self.get_option('password') or self._play_context.password
        display.v(f"Path: {configPath}")

        config = sliver.SliverClientConfig.parse_config_file(configPath)
        self.client = sliver.SliverClient(config)
        self.sessionID = asyncio.run(self.getSessionID(remote))


    async def getSessionID(self, remote_addr):
        try:
            await self.client.connect()
        except:
            raise AnsibleError("Could not connect to Sliver Multiplayer Server")
        sessions = await self.client.sessions()

        for session in sessions:
            if (remote_addr == session.RemoteAddress.split(':')[0]):
                display.v(f"Found Sliver Session!")
                return session.ID


        #  No session exists, maybe beacon does?
        beacons = await self.client.beacons()

        for beacon in beacons:
            if (remote_addr == beacon.RemoteAddress.split(':')[0]):
                raise AnsibleError(f"Found a Sliver Beacon for {remote_addr}, create a session with interactive")

        raise AnsibleError(f"Could not find Sliver Session/Beacon: {remote_addr}")



    # _connect() is called multiple times whenever a new task is run
    # we only need the sessionID & clientID for the lifetime of the play
    # these vars are constant throughout the lifetime, so no need to regenerate for every task
    # i.e no connection management
    def _connect(self) -> Connection:
        display.v(f"_connect()")
        return self

    async def asyncExecCommand(self, cmd: str) -> tuple[int, bytes, bytes]:
        try:
            await self.client.connect()
        except:
            raise AnsibleError("Could not connect to Sliver Multiplayer Server")
        interact = await self.client.interact_session(self.sessionID)

        # 1.5 hours to find this command right here
        cmdRes = await interact.execute("/bin/sh", ['-c', cmd], True)

        return cmdRes.Status, cmdRes.Stdout.decode(), cmdRes.Stderr.decode()


    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        display.v("exec_command()")
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        return asyncio.run(self.asyncExecCommand(cmd))

    async def asyncPutFile(self, in_path: str, out_path: str) -> None:
        with open(in_path, 'rb') as f:
            contents = f.read()

        try:
            await self.client.connect()
        except:
            raise AnsibleError("Could not connect to Sliver Multiplayer Server")
        interact = await self.client.interact_session(self.sessionID)

        await interact.upload(out_path, contents)

    def put_file(self, in_path: str, out_path: str) -> None:
        return asyncio.run(self.asyncPutFile(in_path, out_path))

    async def asyncFetchFile(self, in_path: str, out_path: str) -> None:
        try:
            await self.client.connect()
        except:
            raise AnsibleError("Could not connect to Sliver Multiplayer Server")
        interact = await self.client.interact_session(self.sessionID)

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
