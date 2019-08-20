import asyncio
import pytest
import random
from porkpepper import *


class NoRandom(Raft):
    def node_election_timeout(self) -> float:
        election_timeout = self.election_timeout
        return election_timeout

    def node_vote_timeout(self) -> float:
        vote_timeout = self.vote_timeout
        return vote_timeout


@pytest.mark.asyncio
async def test_follower_timeout():
    node = NoRandom("noname", 0.01, 0.003)
    await node.start()
    assert node.role == NodeRole.Follower
    await asyncio.sleep(0.02)
    assert node.role == NodeRole.Candidate
    await node.stop()
    assert node.follower_task is None
    assert node.role == NodeRole.Follower


@pytest.mark.asyncio
async def test_follower_recv_ping_once():
    node = NoRandom("noname", 0.01, 0.003)
    await node.start()
    assert node.role == NodeRole.Follower
    await asyncio.sleep(0.005)
    await node.recv_leader_message(0)
    await asyncio.sleep(0.006)
    assert node.role == NodeRole.Follower
    await node.stop()


class BasicLeaderElection(Raft):
    ALL_NODE = dict()

    async def get_nodes(self):
        return list(self.ALL_NODE.keys())

    async def send_request_vote(self, node: str, term: int):
        node = self.ALL_NODE[node]
        await node.recv_vote_request(self.node, term)

    async def send_vote(self, node: str, term: int):
        node = self.ALL_NODE[node]
        await node.recv_vote(term)

    async def send_heartbeat(self, node:str, term: int):
        node = self.ALL_NODE[node]
        await node.recv_leader_message(term)

    def node_election_timeout(self) -> float:
        election_timeout = self.election_timeout
        if self.node == "a":
            election_timeout += 0.0
        if self.node == "b":
            election_timeout += 0.005
        if self.node == "c":
            election_timeout += 0.010
        return election_timeout

    def node_vote_timeout(self) -> float:
        vote_timeout = self.vote_timeout
        if self.node == "a":
            vote_timeout += 0.0
        if self.node == "b":
            vote_timeout += 0.005
        if self.node == "c":
            vote_timeout += 0.010
        return vote_timeout


@pytest.mark.asyncio
async def test_election_basic():
    a = BasicLeaderElection("a", 0.1, 0.03, 0.1)
    b = BasicLeaderElection("b", 0.1, 0.03, 0.1)
    c = BasicLeaderElection("c", 0.1, 0.03, 0.1)
    BasicLeaderElection.ALL_NODE["a"] = a
    BasicLeaderElection.ALL_NODE["b"] = b
    BasicLeaderElection.ALL_NODE["c"] = c
    await a.start()
    await b.start()
    await c.start()
    await asyncio.sleep(0.105)
    assert a.role == NodeRole.Leader or b.role == NodeRole.Leader or c.role == NodeRole.Leader
    await asyncio.sleep(0.105)
    assert a.role == NodeRole.Leader or b.role == NodeRole.Leader or c.role == NodeRole.Leader
    assert a.term == 1
    await a.stop()
    await b.stop()
    await c.stop()

@pytest.mark.asyncio
async def test_leader_stop():
    a = BasicLeaderElection("a", 0.1, 0.03, 0.1)
    b = BasicLeaderElection("b", 0.1, 0.03, 0.1)
    c = BasicLeaderElection("c", 0.1, 0.03, 0.1)
    BasicLeaderElection.ALL_NODE["a"] = a
    BasicLeaderElection.ALL_NODE["b"] = b
    BasicLeaderElection.ALL_NODE["c"] = c
    await a.start()
    await b.start()
    await c.start()
    await asyncio.sleep(0.105)
    assert a.role == NodeRole.Leader or b.role == NodeRole.Leader or c.role == NodeRole.Leader
    if a.role == NodeRole.Leader:
        await a.stop()
    if b.role == NodeRole.Leader:
        await b.stop()
    if c.role == NodeRole.Leader:
        await c.stop()
    await asyncio.sleep(0.105)
    assert a.role == NodeRole.Leader or b.role == NodeRole.Leader or c.role == NodeRole.Leader
    if a.role == NodeRole.Leader:
        assert a.term == 2
    if b.role == NodeRole.Leader:
        assert b.term == 2
    if c.role == NodeRole.Leader:
        assert c.term == 2
    if a.role == NodeRole.Leader:
        await a.stop()
    if b.role == NodeRole.Leader:
        await b.stop()
    if c.role == NodeRole.Leader:
        await c.stop()
    await asyncio.sleep(0.116)
    assert a.role != NodeRole.Leader and b.role != NodeRole.Leader and c.role != NodeRole.Leader
    assert a.role == NodeRole.Candidate or b.role == NodeRole.Candidate or c.role == NodeRole.Candidate
    await a.stop()
    await b.stop()
    await c.stop()
