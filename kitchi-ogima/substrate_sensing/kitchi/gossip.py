"""
Gossip protocol: join, heartbeat, leave, capacity updates.
No coordinator. Every node is a peer.

v1: in-memory message bus (single-process simulation).
v2: swap MessageBus for UDP/ESP-NOW without changing Gossip API.

Wholeness invariant: gossip is meaningful at N=1.
A lone node still emits heartbeats — into the void if nobody
listens, into the pack when someone joins. No mode switch.
"""

from dataclasses import dataclass, field
from collections import defaultdict, deque
from time import monotonic
from typing import Callable, Dict, List, Optional, Set
import threading
import queue


# ------------------------------------------------------------
# Message types — flat, serializable, stdlib-friendly
# ------------------------------------------------------------

@dataclass
class Message:
    kind:     str                    # hello | heartbeat | leave | capacity
    sender:   str
    payload:  dict = field(default_factory=dict)
    ts:       float = field(default_factory=monotonic)


# ------------------------------------------------------------
# MessageBus — abstract transport
# ------------------------------------------------------------
# v1: in-memory pub-sub. Every node subscribes; bus broadcasts.
# v2: replace with UDP multicast or ESP-NOW. Same interface.

class MessageBus:
    """In-memory broadcast bus. Thread-safe."""

    def __init__(self):
        self._subscribers: Dict[str, "queue.Queue[Message]"] = {}
        self._lock = threading.Lock()

    def subscribe(self, node_id: str) -> "queue.Queue[Message]":
        with self._lock:
            q: queue.Queue[Message] = queue.Queue()
            self._subscribers[node_id] = q
            return q

    def unsubscribe(self, node_id: str) -> None:
        with self._lock:
            self._subscribers.pop(node_id, None)

    def broadcast(self, msg: Message) -> None:
        with self._lock:
            targets = list(self._subscribers.items())
        for nid, q in targets:
            if nid != msg.sender:    # don't echo to self
                q.put(msg)


# ------------------------------------------------------------
# Gossip — per-node protocol handler
# ------------------------------------------------------------

@dataclass
class PeerRecord:
    node_id:       str
    last_seen:     float
    capacity:      dict = field(default_factory=dict)
    alive:         bool = True


class Gossip:
    """
    One Gossip per node. Handles outbound heartbeats and
    inbound message processing. Tracks peer liveness.
    """

    def __init__(self,
                 node_id: str,
                 bus: MessageBus,
                 heartbeat_interval: float = 1.0,
                 liveness_timeout:   float = 3.5):
        self.node_id = node_id
        self.bus = bus
        self.heartbeat_interval = heartbeat_interval
        self.liveness_timeout   = liveness_timeout

        self.inbox = bus.subscribe(node_id)
        self.peers: Dict[str, PeerRecord] = {}
        self._on_join:  List[Callable[[str, dict], None]] = []
        self._on_leave: List[Callable[[str], None]] = []
        self._on_capacity: List[Callable[[str, dict], None]] = []

        self._running = False
        self._threads: List[threading.Thread] = []

    # ---- lifecycle ----

    def start(self, capacity: Optional[dict] = None) -> None:
        self._running = True
        # announce arrival
        self.bus.broadcast(Message(
            kind="hello",
            sender=self.node_id,
            payload={"capacity": capacity or {}},
        ))
        # start workers
        t_hb = threading.Thread(target=self._heartbeat_loop,
                                args=(capacity or {},), daemon=True)
        t_rx = threading.Thread(target=self._receive_loop, daemon=True)
        t_lv = threading.Thread(target=self._liveness_loop, daemon=True)
        for t in (t_hb, t_rx, t_lv):
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self.bus.broadcast(Message(kind="leave", sender=self.node_id))
        self.bus.unsubscribe(self.node_id)

    # ---- callbacks (chief layer subscribes here) ----

    def on_join(self,  cb: Callable[[str, dict], None]) -> None:
        self._on_join.append(cb)

    def on_leave(self, cb: Callable[[str], None]) -> None:
        self._on_leave.append(cb)

    def on_capacity_change(self,
                           cb: Callable[[str, dict], None]) -> None:
        self._on_capacity.append(cb)

    # ---- loops ----

    def _heartbeat_loop(self, capacity: dict) -> None:
        import time
        while self._running:
            self.bus.broadcast(Message(
                kind="heartbeat",
                sender=self.node_id,
                payload={"capacity": capacity},
            ))
            time.sleep(self.heartbeat_interval)

    def _receive_loop(self) -> None:
        while self._running:
            try:
                msg = self.inbox.get(timeout=0.5)
            except queue.Empty:
                continue
            self._handle(msg)

    def _liveness_loop(self) -> None:
        import time
        while self._running:
            now = monotonic()
            dead = []
            for nid, rec in list(self.peers.items()):
                if rec.alive and (now - rec.last_seen) > self.liveness_timeout:
                    rec.alive = False
                    dead.append(nid)
            for nid in dead:
                for cb in self._on_leave:
                    cb(nid)
            time.sleep(self.heartbeat_interval / 2)

    # ---- message handling ----

    def _handle(self, msg: Message) -> None:
        if msg.kind == "hello":
            self._upsert_peer(msg, fire_join=True)

        elif msg.kind == "heartbeat":
            existed = msg.sender in self.peers and self.peers[msg.sender].alive
            self._upsert_peer(msg, fire_join=not existed)

        elif msg.kind == "capacity":
            if msg.sender in self.peers:
                self.peers[msg.sender].capacity = msg.payload.get("capacity", {})
                self.peers[msg.sender].last_seen = monotonic()
                for cb in self._on_capacity:
                    cb(msg.sender, self.peers[msg.sender].capacity)

        elif msg.kind == "leave":
            if msg.sender in self.peers and self.peers[msg.sender].alive:
                self.peers[msg.sender].alive = False
                for cb in self._on_leave:
                    cb(msg.sender)

    def _upsert_peer(self, msg: Message, fire_join: bool) -> None:
        cap = msg.payload.get("capacity", {})
        if msg.sender not in self.peers:
            self.peers[msg.sender] = PeerRecord(
                node_id=msg.sender,
                last_seen=monotonic(),
                capacity=cap,
                alive=True,
            )
        else:
            rec = self.peers[msg.sender]
            rec.last_seen = monotonic()
            rec.alive = True
            if cap:
                rec.capacity = cap
        if fire_join:
            for cb in self._on_join:
                cb(msg.sender, cap)

    # ---- helpers ----

    def announce_capacity(self, capacity: dict) -> None:
        self.bus.broadcast(Message(
            kind="capacity",
            sender=self.node_id,
            payload={"capacity": capacity},
        ))

    def alive_peers(self) -> Set[str]:
        return {nid for nid, rec in self.peers.items() if rec.alive}
