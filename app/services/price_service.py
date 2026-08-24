"""Logica de negocio: comparar precos, calcular variacao e decidir se um
alerta deve ser enviado. Nao sabe nada sobre Playwright, Excel ou e-mail --
apenas trabalha com numeros, o que facilita testar (ver tests/).
"""

from dataclasses import dataclass


@dataclass
class PriceCheckResult:
    current_price: float
    previous_price: float | None
    variation_percent: float | None
    should_alert: bool


class PriceService:
    def __init__(self, min_drop_percent: float):
        self.min_drop_percent = min_drop_percent

    def calculate_variation_percent(self, previous_price: float, current_price: float) -> float:
        """Retorna a queda percentual. Positivo = preco caiu; negativo = preco subiu."""
        if previous_price <= 0:
            raise ValueError("Preco anterior deve ser maior que zero.")
        return ((previous_price - current_price) / previous_price) * 100

    def should_alert(self, variation_percent: float) -> bool:
        """So alerta quando a queda for igual ou maior que o minimo configurado.

        Como variation_percent e negativo quando o preco sobe, uma alta nunca
        atinge o limiar (que e positivo) -- portanto nunca dispara alerta.
        """
        return variation_percent >= self.min_drop_percent

    def evaluate(self, current_price: float, previous_price: float | None) -> PriceCheckResult:
        """Junta as duas regras acima. Sem preco anterior (primeira execucao),
        nao ha o que comparar, entao nunca ha alerta.
        """
        if previous_price is None:
            return PriceCheckResult(current_price, None, None, False)

        variation = self.calculate_variation_percent(previous_price, current_price)
        return PriceCheckResult(
            current_price=current_price,
            previous_price=previous_price,
            variation_percent=variation,
            should_alert=self.should_alert(variation),
        )
