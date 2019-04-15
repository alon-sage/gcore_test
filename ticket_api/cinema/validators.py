from decimal import Decimal

from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator
from rest_framework.compat import MaxValueValidator

NotBlank = MinLengthValidator(1)
NonNegativeInt = MinValueValidator(0)
PositiveInt = MinValueValidator(1)
NonNegativeDecimal = MinValueValidator(Decimal('0'))


class DynamicMaxValueValidator(MaxValueValidator):
    def __init__(self, limit_calculator, *args, **kwargs):
        super(DynamicMaxValueValidator, self).__init__(self._limit_value)
        self.limit_calculator = limit_calculator
        self.context = None

    def _limit_value(self):
        return self.limit_calculator(self.context)

    def set_context(self, field):
        self.context = field.parent.context
