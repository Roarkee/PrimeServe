from decimal import Decimal

from ..schema import CatalogValidatedOption


class OrderPricingService:

    @staticmethod
    def calculate_item_subtotal(
        unit_price: Decimal,
        quantity: int,
        options_price: Decimal,
    ) -> Decimal:
        return (unit_price + options_price) * quantity

    @staticmethod
    def calculate_subtotal(
        item_subtotals: list[Decimal],
    ) -> Decimal:
        return sum(item_subtotals, Decimal("0.00"))

    @staticmethod
    def calculate_options_total(
        options: list[CatalogValidatedOption],
    ) -> Decimal:
        return sum(
            (option.additional_price for option in options),
            Decimal("0.00"),
        )

    @staticmethod
    def calculate_discount(
        subtotal: Decimal,
        discount_type: str,
        discount_value: Decimal,
    ) -> Decimal:

        if discount_value < Decimal("0.00"):
            raise ValueError("Discount cannot be negative.")

        if discount_type == "fixed":
            discount = discount_value

        elif discount_type == "percentage":
            if discount_value > Decimal("100.00"):
                raise ValueError(
                    "Percentage discount cannot exceed 100%."
                )

            discount = subtotal * (
                discount_value / Decimal("100")
            )

        else:
            raise ValueError("Invalid discount type.")

        return min(discount, subtotal)

    @staticmethod
    def calculate_tax(
        taxable_amount: Decimal,
        tax_rate: Decimal,
    ) -> Decimal:

        if tax_rate < Decimal("0.00"):
            raise ValueError("Tax rate cannot be negative.")

        return taxable_amount * (
            tax_rate / Decimal("100")
        )

    @staticmethod
    def calculate_total(
        subtotal: Decimal,
        discount: Decimal,
        tax: Decimal,
    ) -> Decimal:
        return subtotal - discount + tax