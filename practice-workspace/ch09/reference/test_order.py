"""Small comparison tests; the fixed checker covers every state/action pair."""
import unittest
from order import Order


class OrderTests(unittest.TestCase):
    def test_normal_flow(self):
        """Public actions reach each normal state in sequence."""
        order = Order(order_id=1)
        for action, expected in (
            ('approve', 'APPROVED'), ('ship', 'SHIPPING'),
            ('confirm_delivery', 'DELIVERED'), ('complete', 'COMPLETED'),
        ):
            getattr(order, action)()
            self.assertEqual(order.status, expected)

    def test_reapproval_after_delivery(self):
        """Reapproval raises and preserves delivered state."""
        order = Order(order_id=1)
        order.approve()
        order.ship()
        order.confirm_delivery()
        with self.assertRaises(ValueError):
            order.approve()
        self.assertEqual(order.status, 'DELIVERED')

    def test_skip_delivery(self):
        """Delivery confirmation is rejected while pending."""
        order = Order(order_id=1)
        with self.assertRaises(ValueError):
            order.confirm_delivery()
        self.assertEqual(order.status, 'PENDING')

    def test_direct_assignment(self):
        """Public status assignment raises without changing state."""
        order = Order(order_id=1)
        with self.assertRaises(AttributeError):
            order.status = 'APPROVED'
        self.assertEqual(order.status, 'PENDING')

    def test_duplicate_approval(self):
        """Duplicate approval preserves approved state."""
        order = Order(order_id=1)
        order.approve()
        with self.assertRaises(ValueError):
            order.approve()
        self.assertEqual(order.status, 'APPROVED')

    def test_terminal_states(self):
        """Every public action is rejected after cancellation or completion."""
        for preparation, state in (
            (('cancel',), 'CANCELLED'),
            (('approve', 'ship', 'confirm_delivery', 'complete'), 'COMPLETED'),
        ):
            for action in ('approve', 'ship', 'confirm_delivery', 'complete', 'cancel'):
                with self.subTest(state=state, action=action):
                    order = Order(order_id=1)
                    for step in preparation:
                        getattr(order, step)()
                    with self.assertRaises(ValueError):
                        getattr(order, action)()
                    self.assertEqual(order.status, state)


if __name__ == '__main__':
    unittest.main(verbosity=2)
