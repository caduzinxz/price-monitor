"""Logica de negocio: comparar precos, calcular variacao, detectar menor preco
historico e decidir se um alerta deve ser enviado. Nao sabe nada sobre
Playwright, Supabase ou e-mail -- apenas trabalha com numeros, o que facilita
testar (ver tests/).
"""

from dataclasses import dataclass


@dataclass
class PriceCheckResult:
    current_price: float
    previous_price: float | None
    variation_percent: float | None
    historic_min_price: float | None
    is_historic_low: bool
    should_alert: bool


class PriceService:
    def __init__(self, min_drop_percent: float, alert_on_historic_low: bool = True):
        self.min_drop_percent = min_drop_percent
        self.alert_on_historic_low = alert_on_historic_low

    def calculate_variation_percent(self, previous_price: float, current_price: float) -> float:
        """Retorna a queda percentual. Positivo = preco caiu; negativo = preco subiu."""
        if previous_price <= 0:
            raise ValueError("Preco anterior deve ser maior que zero.")
        return ((previous_price - current_price) / previous_price) * 100

    def reached_drop_threshold(self, variation_percent: float) -> bool:
        """So alerta quando a queda for igual ou maior que o minimo configurado.

        Como variation_percent e negativo quando o preco sobe, uma alta nunca
        atinge o limiar (que e positivo) -- portanto nunca dispara alerta.
        """
        return variation_percent >= self.min_drop_percent

    def is_historic_low(self, current_price: float, historic_min_price: float | None) -> bool:
        """Diz se o preco atual e um novo recorde de menor preco.

        Duas decisoes importantes aqui:

        1. Sem historico (historic_min_price=None) NAO e recorde. Na primeira
           verificacao o preco seria trivialmente "o menor de todos", o que
           geraria um alerta sem significado nenhum.
        2. A comparacao e estritamente MENOR (<), nunca menor-ou-igual (<=).
           Com <=, um preco parado no minimo dispararia um alerta a cada
           verificacao, de hora em hora, para sempre.
        """
        if historic_min_price is None:
            return False
        return current_price < historic_min_price

    def evaluate(
        self,
        current_price: float,
        previous_price: float | None,
        historic_min_price: float | None = None,
    ) -> PriceCheckResult:
        """Junta as regras acima. Sem preco anterior (primeira verificacao),
        nao ha o que comparar, entao nunca ha alerta.
        """
        if previous_price is None:
            return PriceCheckResult(
                current_price=current_price,
                previous_price=None,
                variation_percent=None,
                historic_min_price=historic_min_price,
                is_historic_low=False,
                should_alert=False,
            )

        variation = self.calculate_variation_percent(previous_price, current_price)
        historic_low = self.is_historic_low(current_price, historic_min_price)

        # Um recorde de menor preco e noticia mesmo que a queda desde a ultima
        # verificacao tenha sido pequena -- por isso as duas condicoes sao
        # independentes e qualquer uma delas basta para alertar.
        must_alert = self.reached_drop_threshold(variation) or (
            historic_low and self.alert_on_historic_low
        )

        return PriceCheckResult(
            current_price=current_price,
            previous_price=previous_price,
            variation_percent=variation,
            historic_min_price=historic_min_price,
            is_historic_low=historic_low,
            should_alert=must_alert,
        )
