"""Comparison example: a single order's state rules, without DB or HTTP."""


class Order:
    ALLOWED_TRANSITIONS = {
        'PENDING': ('APPROVED', 'CANCELLED'),
        'APPROVED': ('SHIPPING',), 'SHIPPING': ('DELIVERED',),
        'DELIVERED': ('COMPLETED',), 'COMPLETED': (), 'CANCELLED': (),
    }

    def __init__(self, order_id=1):
        """Create a pending order with the supplied identifier."""
        self.order_id = order_id
        self._status = 'PENDING'

    @property
    def status(self):
        """Read the current state; no public setter is provided."""
        return self._status

    def _transition_to(self, target):
        """Check before assignment, preserving state when rejected."""
        if target not in self.ALLOWED_TRANSITIONS[self._status]:
            raise ValueError('허용되지 않은 상태 변경입니다.')
        self._status = target

    def approve(self):
        """Approve a pending order."""
        self._transition_to('APPROVED')

    def ship(self):
        """Ship an approved order."""
        self._transition_to('SHIPPING')

    def confirm_delivery(self):
        """Confirm delivery of a shipping order."""
        self._transition_to('DELIVERED')

    def complete(self):
        """Complete a delivered order."""
        self._transition_to('COMPLETED')

    def cancel(self):
        """Cancel a pending order."""
        self._transition_to('CANCELLED')
