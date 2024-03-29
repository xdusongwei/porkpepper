from typing import *
import asyncio
from .error import *
from .result import Result
from .redis_session import RedisSession


class RedisTaskNode:
    def __init__(self, command, fa: Optional[Tuple[Callable, Union[None, Dict]]]):
        self.command: bytes = command
        self.fa = fa
        self.result = None

    @classmethod
    async def readline(cls, reader, session=None):
        line = await reader.readline()
        if line and session:
            session.server.total_net_input_bytes += len(line)
        return line

    @classmethod
    async def readexactly(cls, reader, read_size, session=None):
        line = await reader.readexactly(read_size)
        if line and session:
            session.server.total_net_input_bytes += read_size
        return line

    @classmethod
    def write(cls, writer, binary, session=None):
        writer.write(binary)
        if binary and session:
            session.server.total_net_output_bytes += len(binary)

    @classmethod
    async def create(cls, session: RedisSession, mixin: 'RedisServerBase') -> Result['RedisTaskNode']:
        reader = session.reader
        need_auth_event = session.need_auth_event
        idle_timeout = mixin.IDLE_TIMEOUT
        line = await asyncio.wait_for(cls.readline(reader, session), timeout=idle_timeout)
        if not line:
            return Result(EOFError())
        args_count_result = mixin.get_count(line)
        if args_count_result.is_error:
            return Result(args_count_result.error)
        args_count = args_count_result.unwrap()
        commands = list()
        for _ in range(args_count):
            data = await asyncio.wait_for(cls.readline(reader, session), timeout=idle_timeout)
            binary_size_result = mixin.get_binary_size(data)
            if binary_size_result.is_error:
                return Result(binary_size_result.error)
            binary_size = binary_size_result.unwrap()
            data = await asyncio.wait_for(cls.readexactly(reader, binary_size + 2, session), timeout=idle_timeout)
            commands.append(data[:-2])
        if not commands:
            return Result(RedisProtocolFormatError())
        command = commands[0].upper()
        if command == b'AUTH':
            if len(commands) > 1:
                password = commands[1]
            else:
                password = b''
            fa = (mixin.auth, dict(session=session, password=password), )
            node = RedisTaskNode(command, fa)
            return Result(node)
        if need_auth_event.is_set():
            node = RedisTaskNode(b'AUTH', None)
            node.result = Result(NoPasswordError("NOAUTH Authentication required."))
            return Result(node)
        if command == b'CONFIG':
            if len(commands) != 3:
                return Result(RedisProtocolFormatError())
            fa = (mixin.config, dict(session=session, get_set=commands[1], field=commands[2]))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'INFO':
            fa = (mixin.info, dict(session=session))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'SELECT':
            if len(commands) != 2:
                return Result(RedisProtocolFormatError())
            database_id = int(commands[1])
            fa = (mixin.select, dict(session=session, db=database_id))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'DBSIZE':
            if len(commands) != 1:
                return Result(RedisProtocolFormatError())
            fa = (mixin.dbsize, dict(session=session))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'PING':
            fa = (mixin.ping, dict(session=session))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'SET':
            if len(commands) < 3:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            value = commands[2]
            fa = (mixin.set, dict(session=session, key=key, value=value))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'GETSET':
            if len(commands) < 3:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            value = commands[2]
            fa = (mixin.getset, dict(session=session, key=key, value=value))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'GET':
            if len(commands) != 2:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            fa = (mixin.get, dict(session=session, key=key))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'TYPE':
            if len(commands) != 2:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            fa = (mixin.key_type, dict(session=session, key=key))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'TTL':
            if len(commands) != 2:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            fa = (mixin.ttl, dict(session=session, key=key))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b'SCAN' or command == b'KEYS':
            if len(commands) < 2 or len(commands) % 2:
                return Result(RedisProtocolFormatError())
            pattern = None
            args_pairs = zip(commands[2::2], commands[3::2])
            for arg_name, arg_value in args_pairs:
                if arg_name.upper() == b'MATCH':
                    pattern = f'^{arg_value.decode("utf8").replace("*", ".+")}$'
                elif arg_name.upper() == b'COUNT':
                    pass
            fa = (mixin.scan, dict(session=session, pattern=pattern))
            node = RedisTaskNode(command, fa)
            return Result(node)
        elif command == b"DEL":
            if len(commands) != 2:
                return Result(RedisProtocolFormatError())
            key = commands[1].decode("utf8").strip()
            fa = (mixin.delete, dict(session=session, key=key))
            node = RedisTaskNode(command, fa)
            return Result(node)
        else:
            node = RedisTaskNode(b'NOOP', None)
            node.result = Result(CommandNotFound())
            return Result(node)

    async def write_result(self, session: RedisSession, mixin: 'RedisServerBase') -> Result[bool]:
        writer = session.write
        need_auth_event = session.need_auth_event
        command = self.command
        if command == b'AUTH':
            auth_result = self.result
            if auth_result.is_error:
                if isinstance(auth_result.error, ExceptionWithReplyError):
                    error_reply = auth_result.error.reply
                else:
                    error_reply = "ERR"
                binary_result = mixin.set_err(error_reply)
                need_auth_event.set()
            elif not auth_result.unwrap():
                binary_result = mixin.set_err("ERR invalid password")
                need_auth_event.set()
            else:
                binary_result = mixin.set_ok()
                need_auth_event.clear()
            self.write(writer, binary_result.unwrap(), session)
        elif need_auth_event.is_set():
            binary_result = mixin.set_err("NOAUTH Authentication required.")
            self.write(writer, binary_result.unwrap(), session)
        elif command == b'CONFIG':
            config_result = self.result
            if config_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                binary_lines = config_result.unwrap()
                item_size = len(binary_lines)
                self.write(writer, mixin.set_count(item_size).unwrap(), session)
                for binary in binary_lines:
                    binary_result = mixin.set_binary(binary)
                    self.write(writer, binary_result.unwrap(), session)
        elif command == b'INFO':
            info_result = self.result
            if info_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            binary_result = mixin.set_binary(info_result.unwrap())
            if binary_result.is_error:
                return Result(binary_result.error)
            self.write(writer, binary_result.unwrap(), session)
        elif command == b'SELECT':
            select_result = self.result
            if select_result.is_error:
                self.write(writer, mixin.set_err("ERR invalid DB index").unwrap(), session)
            else:
                self.write(writer, mixin.set_ok().unwrap(), session)
        elif command == b'DBSIZE':
            dbsize_result = self.result
            if dbsize_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                binary_result = mixin.set_integer(dbsize_result.unwrap())
                if binary_result.is_error:
                    return Result(binary_result.error)
                self.write(writer, binary_result.unwrap(), session)
        elif command == b'PING':
            ping_result = self.result
            if ping_result.is_error:
                return Result(ping_result.error)
            binary_result = mixin.set_ok(ping_result.unwrap())
            if binary_result.is_error:
                return Result(binary_result.error)
            self.write(writer, binary_result.unwrap(), session)
        elif command == b'SET':
            set_result = self.result
            if set_result.is_error:
                binary_result = mixin.set_err()
                self.write(writer, binary_result.unwrap(), session)
            else:
                binary_result = mixin.set_ok()
                if binary_result.is_error:
                    return Result(binary_result.error)
                self.write(writer, binary_result.unwrap(), session)
        elif command == b'GETSET':
            getset_result = self.result
            if getset_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                if getset_result.unwrap() is None:
                    binary_result = mixin.set_nil()
                else:
                    binary_result = mixin.set_binary(getset_result.unwrap())
                if binary_result.is_error:
                    return Result(binary_result.error)
                self.write(writer, binary_result.unwrap(), session)
        elif command == b'GET':
            get_result = self.result
            if get_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                if get_result.unwrap() is None:
                    binary_result = mixin.set_nil()
                else:
                    binary_result = mixin.set_binary(get_result.unwrap())
                if binary_result.is_error:
                    return Result(binary_result.error)
                self.write(writer, binary_result.unwrap(), session)
        elif command == b'TYPE':
            key_type_result = self.result
            if key_type_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                binary_result = mixin.set_ok(key_type_result.unwrap())
                if binary_result.is_error:
                    return Result(binary_result.error)
                self.write(writer, binary_result.unwrap(), session)
        elif command == b'TTL':
            ttl_result = self.result
            if ttl_result.is_error:
                return Result(ttl_result.error)
            binary_result = mixin.set_integer(ttl_result.unwrap())
            if binary_result.is_error:
                return Result(binary_result.error)
            self.write(writer, binary_result.unwrap(), session)
        elif command == b'SCAN' or command == b'KEYS':
            scan_result = self.result
            if scan_result.is_error:
                self.write(writer, mixin.set_err().unwrap(), session)
            else:
                keys = scan_result.unwrap()
                count = len(keys)
                if command == b'SCAN':
                    self.write(writer, mixin.set_count(2).unwrap(), session)
                    self.write(writer, mixin.set_binary(0).unwrap(), session)
                self.write(writer, mixin.set_count(count).unwrap(), session)
                for key in keys:
                    self.write(writer, mixin.set_binary(key).unwrap(), session)
                    await writer.drain()
        elif command == b"DEL":
            delete_result = self.result
            if delete_result.is_error:
                return Result(delete_result.error)
            binary_result = mixin.set_integer(delete_result.unwrap())
            if binary_result.is_error:
                return Result(binary_result.error)
            self.write(writer, binary_result.unwrap(), session)
        else:
            binary_result = mixin.set_err("COMMAND NOT EXISTS")
            self.write(writer, binary_result.unwrap(), session)
        await writer.drain()
        return Result(True)


__all__ = ["RedisTaskNode", ]
