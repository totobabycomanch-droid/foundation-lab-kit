"""Check the public Order interface against fixed business expectations."""
import argparse
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PATHS = {
    'PENDING': (), 'APPROVED': ('approve',),
    'SHIPPING': ('approve', 'ship'),
    'DELIVERED': ('approve', 'ship', 'confirm_delivery'),
    'COMPLETED': ('approve', 'ship', 'confirm_delivery', 'complete'),
    'CANCELLED': ('cancel',),
}
ACTIONS = ('approve', 'ship', 'confirm_delivery', 'complete', 'cancel')
# Expectations come from the manuscript, never from the implementation table.
ALLOWED = {
    ('PENDING', 'approve'): 'APPROVED',
    ('PENDING', 'cancel'): 'CANCELLED',
    ('APPROVED', 'ship'): 'SHIPPING',
    ('SHIPPING', 'confirm_delivery'): 'DELIVERED',
    ('DELIVERED', 'complete'): 'COMPLETED',
}


class OrderRules(unittest.TestCase):
    def prepared(self, state):
        """Prepare each state through public actions on a fresh order."""
        order = self.order_type(order_id=1)
        self.assertEqual(order.status, 'PENDING')
        for action in PATHS[state]:
            getattr(order, action)()
        self.assertEqual(order.status, state)
        return order

    def test_initial_state(self):
        """A new order starts pending."""
        self.assertEqual(self.order_type(order_id=1).status, 'PENDING')

    def test_status_returns_plain_string(self):
        """Every public state is a plain str, including terminal states."""
        for state in PATHS:
            with self.subTest(state=state):
                order = self.prepared(state)
                self.assertIs(type(order.status), str)

    def test_status_print_output(self):
        """Printing each public state emits only its name and a newline."""
        for state in PATHS:
            with self.subTest(state=state):
                order = self.prepared(state)
                output = io.StringIO()
                with redirect_stdout(output):
                    print(order.status)
                self.assertEqual(output.getvalue(), state + '\n')

    def test_status_assignment(self):
        """Direct public assignment is rejected in every state."""
        for state in PATHS:
            with self.subTest(state=state):
                order = self.prepared(state)
                with self.assertRaises(AttributeError):
                    order.status = 'APPROVED'
                self.assertEqual(order.status, state)

    def test_separate_orders(self):
        """Changing one order preserves another order's state."""
        first = self.order_type(order_id=1)
        second = self.order_type(order_id=2)
        first.approve()
        self.assertEqual(first.status, 'APPROVED')
        self.assertEqual(second.status, 'PENDING')
        second.cancel()
        self.assertEqual(first.status, 'APPROVED')
        self.assertEqual(second.status, 'CANCELLED')


def case(state, action):
    def check(self):
        order = self.prepared(state)
        expected = ALLOWED.get((state, action))
        if expected is None:
            with self.assertRaises(ValueError):
                getattr(order, action)()
            self.assertEqual(order.status, state)
        else:
            getattr(order, action)()
            self.assertEqual(order.status, expected)
    check.__doc__ = f'{state} / {action}: check outcome and final state.'
    return check


for state in PATHS:
    for action in ACTIONS:
        setattr(OrderRules, f'test_{state}_{action}', case(state, action))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(__file__).resolve().parents[1] / 'erp-mini/domain/order.py'
    parser.add_argument('--order-file', type=Path, default=default)
    args = parser.parse_args()
    if not args.order_file.is_file():
        print('NOT RUN: generate erp-mini/domain/order.py first.')
        sys.exit(1)
    spec = importlib.util.spec_from_file_location('chapter9_checked_order', args.order_file.resolve())
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    OrderRules.order_type = staticmethod(module.Order)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OrderRules)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('PASS: fixed order rules' if result.wasSuccessful() else 'FAIL: fixed order rules')
    sys.exit(0 if result.wasSuccessful() else 1)
