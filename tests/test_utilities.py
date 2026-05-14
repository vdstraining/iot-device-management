import unittest

from utilities import build_handshake_payload, validate_handshake_payload


class TestUtilities(unittest.TestCase):
    def test_build_handshake_payload_splits_capabilities(self):
        payload = build_handshake_payload(
            client_id='client-123',
            token='secret',
            capabilities='ping, subscribe,echo',
            session_id='session-abc',
        )

        self.assertEqual(payload['action'], 'handshake')
        self.assertEqual(payload['clientId'], 'client-123')
        self.assertEqual(payload['auth']['token'], 'secret')
        self.assertEqual(payload['metadata']['sessionId'], 'session-abc')
        self.assertEqual(payload['capabilities'], ['ping', 'subscribe', 'echo'])

    def test_validate_handshake_payload_returns_true_for_valid_payload(self):
        payload = {
            'action': 'handshake',
            'clientId': 'client-123',
            'capabilities': ['ping'],
            'metadata': {'sessionId': 'session-abc'},
            'auth': {'token': 'secret'},
        }
        self.assertTrue(validate_handshake_payload(payload))

    def test_validate_handshake_payload_rejects_missing_fields(self):
        self.assertFalse(validate_handshake_payload({}))
        self.assertFalse(validate_handshake_payload({'action': 'handshake'}))
        self.assertFalse(validate_handshake_payload({'action': 'handshake', 'clientId': 'client-123', 'auth': {}}))
        self.assertFalse(validate_handshake_payload({'action': 'handshake', 'clientId': 'client-123', 'auth': {'token': 'secret'}, 'capabilities': 'ping'}))


if __name__ == '__main__':
    unittest.main()
