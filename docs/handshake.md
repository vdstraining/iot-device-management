# Handshake

Schema

- Required fields:
  - `type`: must be `handshake`
  - `clientId`: string
- Optional fields:
  - `capabilities`: object
  - `token`: string

Config keys (precedence: runtime config > environment variables > defaults)

- `handshake.clientId` (env: `HANDSHAKE_CLIENTID`, default: `client-0001`)
- `handshake.token` (env: `HANDSHAKE_TOKEN`, default: empty)
- `handshake.autoSend` (env: `HANDSHAKE_AUTOSEND`, default: `true`)
- `handshake.applyResponseToState` (env: `HANDSHAKE_APPLYRESPONSE`, default: `false`)

Triggering

- Auto-send: when `handshake.autoSend` is true (default), the client sends the handshake immediately after WebSocket connection.
- Manual send: call `send_handshake(runtime_config=None)` on the `WebSocketManager` instance; provide a runtime_config dict to override any handshake config for that send.

Logging

- Outgoing and incoming handshake messages are logged to the UI log using the existing `AppLogger` API.
- Tokens are redacted in UI logs showing only the first 4 characters followed by `***` when present.

Applying response to state

- If `handshake.applyResponseToState` is true, the parsed server response is stored in `WebSocketManager.connection_state['handshakeResponse']`.
