# WebSocket Connection Management and Sequence Recovery

## 1. Connection State Machine

WebSocket connections for Bybit and AsterDEX cycle through defined lifecycle states:

```
[DISCONNECTED] ----> (connect) ----> [CONNECTING]
      ^                                     |
      |                                (connected)
      |                                     v
      |                              [CONNECTED]
      |                                     |
  (failure)                            (disconnect)
      |                                     v
  [FAILED] <---- (max retries) <---- [RECONNECTING]
```

- `DISCONNECTED`: Initial state or clean shutdown.
- `CONNECTING`: Establishing underlying TCP/TLS socket.
- `CONNECTED`: Connection active, subscriptions registered and acknowledged.
- `RECONNECTING`: Connection dropped, attempting reconnection with exponential backoff.
- `FAILED`: Maximum reconnection attempts exceeded, requiring operator intervention.

## 2. Exponential Backoff and Jitter

To prevent thundering herd conditions during exchange outages, reconnect delays use exponential backoff:

$$\text{delay} = \min\left(\text{max\_backoff}, \text{initial\_backoff} \times 2^{\text{attempt} - 1}\right) + \text{jitter}$$

- Initial backoff: 1.0 second.
- Maximum backoff: 60.0 seconds.
- Jitter: Uniform random float between 0.1 and 0.5 seconds.
- Maximum attempts: 10 attempts before failing.

## 3. Order Book Sequence Gap Resynchronization

When streaming L2 order book deltas:
1. Every delta frame contains sequence numbers (`u` for Bybit; `pu`, `u` for AsterDEX).
2. If `delta.prev_update_id != local_ob.last_update_id`:
   - A sequence gap is detected (dropped network packet or stream desynchronization).
   - Local order book status immediately transitions to `RESYNCING`.
   - An audit record is logged into `market_data_audit`.
   - A critical alert (`TOPIC_MARKET_FEED_ALERT`, P0) is published to the EventBus.
   - An asynchronous task triggers a REST order book snapshot.
   - Upon receiving the fresh snapshot, `apply_snapshot` resets the book levels, clears the gap condition, and restores status to `SYNCHRONIZED`.
