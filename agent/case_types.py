"""The four dispute case types supported by this first version.

Scoped deliberately to a fixed set rather than open-ended free text
classification, so the Jev verdict criteria below can be tailored to what
actually matters for each case type (what to weigh for a shipping dispute
is different from what matters for a "not as described" dispute).

All sample disputes here are entirely synthetic — fictional stores,
products, and amounts — safe to publish.
"""

from __future__ import annotations

from typing import TypedDict

from agent.state import CaseType


class CaseTypeInfo(TypedDict):
    label: str
    verdict_instructions: str
    sample_dispute: str


CASE_TYPES: dict[CaseType, CaseTypeInfo] = {
    "item_not_received": {
        "label": "Item not received",
        "verdict_instructions": (
            "This is an 'item not received' dispute: the customer paid but "
            "says the item never arrived. Weigh shipment tracking status, "
            "how long it's been since the promised delivery date, and "
            "whether the seller has acknowledged or resolved the issue."
        ),
        "sample_dispute": (
            "Customer paid $64.50 for a desk lamp from an online storefront "
            "('NovaMart Home Goods'). Order confirmation was received and "
            "payment was captured immediately. The promised delivery window "
            "was 5 days ago. Courier tracking has shown no update beyond "
            "'Label Created' for 9 days. The customer messaged the seller "
            "twice through the platform's support chat; the seller replied "
            "once saying they would 'check with the warehouse' three days "
            "ago and has not followed up since. The listing remains active "
            "and in stock."
        ),
    },
    "item_damaged": {
        "label": "Item damaged",
        "verdict_instructions": (
            "This is an 'item damaged' dispute: the customer received the "
            "item but says it arrived broken or defective. Weigh whether "
            "photo/video evidence was provided, how soon after delivery it "
            "was reported, and whether the damage is consistent with "
            "shipping rather than pre-existing wear."
        ),
        "sample_dispute": (
            "Customer received a ceramic plant pot set ($38.00) from seller "
            "'GreenRoot Supplies'. Two of the three pots arrived cracked; "
            "the customer uploaded photos showing visible shipping-box "
            "damage (crushed corner, no packing material around the pots) "
            "within 2 hours of delivery. The seller's return policy covers "
            "damage reported within 48 hours with photo evidence. The "
            "seller has not responded to the claim after 4 days."
        ),
    },
    "item_not_as_described": {
        "label": "Item not as described",
        "verdict_instructions": (
            "This is an 'item not as described' dispute: the customer says "
            "the item received doesn't match the listing (wrong size, "
            "color, material, counterfeit, or missing features). Weigh how "
            "specific and verifiable the discrepancy is, and whether the "
            "listing itself was ambiguous."
        ),
        "sample_dispute": (
            "Customer ordered a 'genuine leather' messenger bag ($89.99) "
            "from seller 'UrbanCraft Goods'. The listing explicitly stated "
            "'full-grain leather exterior' in the title and description. "
            "The item received has a synthetic (vinyl) exterior per the "
            "care label sewn inside, which the customer photographed and "
            "attached to the claim. The customer requests a refund rather "
            "than an exchange since no genuine-leather version is in stock."
        ),
    },
    "refund_not_received": {
        "label": "Refund not received",
        "verdict_instructions": (
            "This is a 'refund not received' dispute: the seller already "
            "agreed to or processed a refund, but the customer says the "
            "money never arrived. Weigh how long it's been since the "
            "refund was supposedly issued versus typical processing times, "
            "and whether there's confirmation (reference number, "
            "screenshot) that a refund was actually initiated."
        ),
        "sample_dispute": (
            "Customer returned a pair of hiking boots ($72.00) to seller "
            "'TrailWorks Outdoor' and received an email on day 1 confirming "
            "the return was received and 'a refund has been issued.' No "
            "refund reference number was included. It has now been 12 "
            "business days and no refund has appeared on the customer's "
            "statement. The customer contacted the seller once by email "
            "with no reply after 5 days."
        ),
    },
}
