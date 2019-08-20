from typing import *
import random
import asyncio
from abc import ABC
from enum import Enum


class NodeRole(Enum):
    Leader = 1
    Follower = 2
    Candidate = 3


class Raft(ABC):
    def __init__(self,
                 node: str,
                 election_timeout: float = 1.0,
                 heartbeat_timeout: float = 1.0,
                 vote_timeout: float = 0.15,
                 **kwargs):
        assert isinstance(node, str) and node
        assert isinstance(election_timeout, (float, int, )) and election_timeout > 0
        assert isinstance(heartbeat_timeout, (float, int, )) and heartbeat_timeout > 0
        assert isinstance(vote_timeout, (float, int, )) and vote_timeout > 0
        assert election_timeout > heartbeat_timeout
        self.node: str = node
        self.term: int = 0
        self.role: NodeRole = NodeRole.Follower
        self.election_timeout: float = float(election_timeout)
        self.heartbeat_timeout: float = float(heartbeat_timeout)
        self.vote_timeout: float = float(vote_timeout)
        self.nodes: Set[str] = set()
        self.vote_count: int = 0

        self.follower_task: asyncio.Task = None
        self.vote_task: asyncio.Task = None
        self.heartbeat_task: asyncio.Task = None

        self.term_vote_set = set()

        self.is_start: bool = False

    def __repr__(self):
        return f"<Raft({self.node}): {self.role}>"

    async def start(self):
        self._shutdown_follower_task()
        self._shutdown_vote_task()
        self._shutdown_heartbeat_task()
        self._start_follower_task()
        self.role = NodeRole.Follower
        self.is_start = True

    async def stop(self):
        self._shutdown_follower_task()
        self._shutdown_vote_task()
        self._shutdown_heartbeat_task()
        self.role = NodeRole.Follower
        self.is_start = False

    def _shutdown_follower_task(self):
        task = self.follower_task
        if task:
            task.cancel()
            self.follower_task = None

    def _shutdown_vote_task(self):
        task = self.vote_task
        if task:
            task.cancel()
            self.vote_task = None

    def _shutdown_heartbeat_task(self):
        task = self.heartbeat_task
        if task:
            task.cancel()
            self.heartbeat_task = None

    def _start_follower_task(self):
        self.follower_task = asyncio.ensure_future(self.timeout_timer(self.node_election_timeout()))

    def _start_vote_task(self):
        self.vote_task = asyncio.ensure_future(self.timeout_timer(self.node_vote_timeout()))

    def _start_heartbeat_task(self):
        self.heartbeat_task = asyncio.ensure_future(self.heartbeat_timer(self.heartbeat_timeout))

    async def recv_leader_message(self, term: int):
        if not self.is_start:
            return
        assert isinstance(term, int)
        if term != self.term:
            return
        self._shutdown_follower_task()
        self._shutdown_vote_task()
        self._start_follower_task()

    async def recv_vote_request(self,  node: str, term: int):
        if not self.is_start:
            return
        assert isinstance(term, int)
        if self.node == node:
            return
        if term <= self.term:
            return
        self._shutdown_follower_task()
        self._shutdown_heartbeat_task()
        if term > self.term:
            self.term = term
            self.vote_count = 0
            self._shutdown_vote_task()
            self._start_vote_task()
            try:
                if term not in self.term_vote_set:
                    self.term_vote_set.add(term)
                    await self.send_vote(node, term)
            except Exception as e:
                pass
        self.role = NodeRole.Follower

    async def recv_vote(self, term: int):
        if not self.is_start:
            return
        assert isinstance(term, int)
        if term < self.term:
            return
        if self.role == NodeRole.Leader and term == self.term:
            return
        if term == self.term:
            self.vote_count += 1
        try:
            nodes = await self.get_nodes()
            self.nodes = nodes
        except Exception as e:
            return
        node_count = len(self.nodes)
        if not node_count:
            return
        if self.vote_count > 0.5 * node_count:
            self._shutdown_vote_task()
            self._shutdown_follower_task()
            self._shutdown_heartbeat_task()
            self.role = NodeRole.Leader
            self._start_heartbeat_task()

    async def timeout_timer(self, timeout: float):
        assert isinstance(timeout, (float, int)) and timeout > 0
        timeout = float(timeout)
        await asyncio.sleep(timeout)
        self.term += 1
        self.role = NodeRole.Candidate
        self.vote_count = 1
        await self.broadcast_vote_request()
        self._start_vote_task()

    async def heartbeat_timer(self, timeout: float):
        assert isinstance(timeout, (float, int)) and timeout > 0
        timeout = float(timeout)
        await asyncio.sleep(timeout)
        await self.broadcast_heartbeat()
        self._start_heartbeat_task()

    async def broadcast_vote_request(self):
        try:
            nodes = await self.get_nodes()
            self.nodes = nodes
        except Exception as e:
            return
        for node in self.nodes:
            try:
                await self.send_request_vote(node, self.term)
            except Exception as e:
                pass

    async def broadcast_heartbeat(self):
        try:
            nodes = await self.get_nodes()
            self.nodes = nodes
        except Exception as e:
            return
        for node in self.nodes:
            try:
                await self.send_heartbeat(node, self.term)
            except Exception as e:
                pass

    async def random_vote(self):
        try:
            nodes = await self.get_nodes()
            self.nodes = nodes
        except Exception as e:
            return
        node = random.choice(nodes)
        await self.send_request_vote(node, self.term)

    def node_vote_timeout(self) -> float:
        vote_timeout = self.vote_timeout
        vote_timeout += random.randint(0, 3) * 0.15
        return vote_timeout

    def node_election_timeout(self) -> float:
        election_timeout = self.election_timeout
        election_timeout += random.randint(0, 3) * 0.15
        return election_timeout

    async def get_nodes(self) -> List[str]:
        raise NotImplementedError

    async def send_request_vote(self, node: str, term: int):
        raise NotImplementedError

    async def send_vote(self, node: str, term: int):
        raise NotImplementedError

    async def send_heartbeat(self, node:str, term: int):
        raise NotImplementedError


__all__ = ['NodeRole', 'Raft', ]
