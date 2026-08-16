"""
payments.py — a small provider abstraction so the donation flow works out
of the box (PAYMENT_PROVIDER=test) and can be pointed at a real gateway
later by filling in the matching keys in .env and implementing the two
TODOs marked below.
"""

import uuid
from abc import ABC, abstractmethod

from app.config import settings


class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout(self, donation) -> dict:
        """Create a payment session for a Donation and return whatever the
        frontend needs to complete checkout (e.g. a redirect URL or order id)."""
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payload: dict) -> bool:
        """Verify a webhook/callback payload from the gateway. Return True
        if the payment succeeded."""
        raise NotImplementedError


class TestPaymentProvider(PaymentProvider):
    """Always-succeeds provider so donations, receipts and the admin
    dashboard can be exercised end-to-end without a real gateway."""

    def create_checkout(self, donation) -> dict:
        return {
            "provider": "test",
            "reference": f"TEST-{uuid.uuid4().hex[:10].upper()}",
            "message": (
                "Test mode: no real payment is taken. Call "
                "POST /api/donations/{donation_id}/confirm-test-payment "
                "to simulate a successful payment."
            ),
        }

    def verify_payment(self, payload: dict) -> bool:
        return True


class RazorpayPaymentProvider(PaymentProvider):
    """Stub — wire this up once you have real Razorpay keys.
    pip install razorpay, then implement using settings.razorpay_key_id /
    settings.razorpay_key_secret."""

    def create_checkout(self, donation) -> dict:
        # TODO: call razorpay.Order.create(...) and return the order id
        # the frontend needs to open Razorpay Checkout.
        raise NotImplementedError("Razorpay integration not yet implemented")

    def verify_payment(self, payload: dict) -> bool:
        # TODO: verify the payment signature using razorpay.utility.verify_payment_signature
        raise NotImplementedError("Razorpay integration not yet implemented")


class InstamojoPaymentProvider(PaymentProvider):
    """Stub — the live kilkaari.org.in site already uses Instamojo, so this
    is the most likely one to finish first. Wire up using
    settings.instamojo_api_key / settings.instamojo_auth_token."""

    def create_checkout(self, donation) -> dict:
        # TODO: POST to https://www.instamojo.com/api/1.1/payment-requests/
        # and return the returned longurl for redirect.
        raise NotImplementedError("Instamojo integration not yet implemented")

    def verify_payment(self, payload: dict) -> bool:
        # TODO: verify the payment_request_id / payment_id sent to your webhook
        raise NotImplementedError("Instamojo integration not yet implemented")


def get_payment_provider() -> PaymentProvider:
    provider = settings.payment_provider.lower()
    if provider == "razorpay":
        return RazorpayPaymentProvider()
    if provider == "instamojo":
        return InstamojoPaymentProvider()
    return TestPaymentProvider()
