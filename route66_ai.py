"""Simple AI driver for Route 66.

The AI uses the public methods on Route66Board so the game rules stay in one
place. It handles emergencies, basic service stops, then moves toward Santa
Monica.
"""

from __future__ import annotations

import math
from typing import Any


class Route66AI:
    CASH_RESERVE = 100
    SAFE_CASH = 150
    RISK_WINDOW = 5

    def __init__(self) -> None:
        self.values: dict[tuple, float] = {}
        self.visits: dict[tuple, int] = {}
        self.targets: dict[str, int] = {}

    def state_key(self, board: Any, car: Any, position: int | None = None) -> tuple:
        pos = car.position if position is None else position
        return (
            car.name,
            min(pos // 5, 13),
            car.fuel < car.fuel_cons,
            car.fuel < 3,
            car.energy <= 0,
            car.energy < 2,
            car.money < 0,
            car.ticket_due,
            car.flat_tire,
            car.tires > 0,
            car.gas_cans > 0,
            pos in board.CITY_STOPS,
            pos in board.RIVER_CROSSINGS,
            tuple(sorted(board.services_at(pos))) or ("road",),
        )

    def remember(self, board: Any, car: Any, reward: float) -> None:
        key = self.state_key(board, car)
        visits = self.visits.get(key, 0) + 1
        old_value = self.values.get(key, 0.0)
        self.visits[key] = visits
        self.values[key] = old_value + (reward - old_value) / visits

    def expected_value(self, board: Any, car: Any, position: int) -> float:
        key = self.state_key(board, car, position)
        learned = self.values.get(key, 0.0)
        progress = position * 0.05
        return learned + progress

    def next_city(self, board: Any, position: int) -> int:
        future_cities = [stop for stop in board.CITY_STOPS if stop > position]
        return min(future_cities) if future_cities else board.CELL_COUNT

    def risk_report(self, board: Any, car: Any) -> dict[str, float]:
        """Estimate survival risk over the next few turns.

        This is intentionally conservative. The AI is trying to reach Santa
        Monica, so cash, fuel, tires, gas cans, and energy are treated as
        survival resources instead of score opportunities.
        """
        turns = self.RISK_WINDOW
        next_city = self.next_city(board, car.position)
        distance_to_city = max(0, next_city - car.position)
        average_step = max(1, min(4, car.max_move))
        turns_to_city = max(1, math.ceil(distance_to_city / average_step))

        fuel_buffer = car.fuel + car.gas_cans * 2
        fuel_needed_5 = car.fuel_cons * turns
        fuel_needed_city = car.fuel_cons * turns_to_city
        energy_needed_5 = turns
        energy_needed_city = turns_to_city

        fuel_short_5 = max(0, fuel_needed_5 - fuel_buffer)
        fuel_short_city = max(0, fuel_needed_city - fuel_buffer)
        energy_short_5 = max(0, energy_needed_5 - car.energy - car.coffee)
        energy_short_city = max(0, energy_needed_city - car.energy - car.coffee)

        ticket_cost = 100 if car.ticket_due else 0
        likely_service_cost = 0
        if fuel_short_5:
            likely_service_cost += 70
        if energy_short_5:
            likely_service_cost += 30
        if car.tires <= 0:
            likely_service_cost += 20

        cash_after_risk = car.money - ticket_cost - likely_service_cost
        money_risk = 0.0
        if car.money < 0:
            money_risk = 1.0
        elif cash_after_risk < 0:
            money_risk = 0.9
        elif car.money < self.CASH_RESERVE:
            money_risk = 0.65
        elif cash_after_risk < self.CASH_RESERVE:
            money_risk = 0.35

        tow_risk = 0.0
        if car.flat_tire:
            tow_risk = 1.0
        elif car.fuel < car.fuel_cons and car.gas_cans <= 0:
            tow_risk = 1.0
        elif fuel_short_5:
            tow_risk = 0.85
        elif fuel_short_city:
            tow_risk = 0.65
        elif car.gas_cans <= 0 and car.fuel <= car.fuel_cons * 2:
            tow_risk = 0.45
        elif car.tires <= 0:
            tow_risk = 0.25

        unsafe_city_factors = 0
        unsafe_city_factors += 1 if fuel_short_city else 0
        unsafe_city_factors += 1 if energy_short_city else 0
        unsafe_city_factors += 1 if car.money < self.CASH_RESERVE else 0
        unsafe_city_factors += 1 if car.tires <= 0 else 0
        unsafe_city_factors += 1 if car.gas_cans <= 0 else 0
        next_city_safe = max(0.05, 1.0 - unsafe_city_factors * 0.18)

        return {
            "money": money_risk,
            "tow": tow_risk,
            "next_city": next_city_safe,
        }

    def survival_priority(self, board: Any, car: Any) -> bool:
        risks = self.risk_report(board, car)
        return (
            car.money < self.CASH_RESERVE
            or risks["money"] >= 0.35
            or risks["tow"] >= 0.45
            or risks["next_city"] < 0.65
        )

    def choose_work_action(self, car: Any) -> str:
        needed = self.SAFE_CASH - car.money
        if needed > 100:
            return "work_three"
        if needed > 50:
            return "work_two"
        return "work_one"

    def can_buy_and_keep_reserve(self, board: Any, car: Any, action: str, reserve: int | None = None) -> bool:
        reserve = self.CASH_RESERVE if reserve is None else reserve
        if not board.service_available(car.position, action):
            return False
        if board.cargo_used(car) >= car.capacity:
            return False
        return car.money - board.price_at(car.position, action) >= reserve

    def should_fill_fuel(self, board: Any, car: Any) -> bool:
        if not board.service_available(car.position, "fill_fuel"):
            return False
        if car.fuel >= car.fuel_tank:
            return False
        risks = self.risk_report(board, car)
        if car.fuel <= car.fuel_cons * 2 or risks["tow"] >= 0.45:
            return True
        return car.money >= self.SAFE_CASH and car.fuel <= car.fuel_tank // 2

    def survival_target(self, board: Any, car: Any) -> int | None:
        risks = self.risk_report(board, car)
        if car.fuel <= car.fuel_cons * 2 or risks["tow"] >= 0.45:
            return board.preferred_service_stop(car.position, "gas")
        if car.energy <= 1:
            return board.preferred_service_stop(car.position, "motel")
        if car.money < self.CASH_RESERVE:
            future_cities = [stop for stop in board.CITY_STOPS if stop > car.position and stop != board.CELL_COUNT]
            return min(future_cities) if future_cities else None
        return None

    def should_sell_collectible(self, board: Any, car: Any) -> bool:
        if not board.service_available(car.position, "sell_collectible"):
            return False
        sale = board.best_collectible_sale(car)
        if sale is None:
            return False
        _, value = sale
        return car.money < self.SAFE_CASH or value >= 80

    def take_turn(self, board: Any) -> bool:
        car = board.current_car()

        if board.turn_done:
            board.next_turn()
            return True

        if board.move_options:
            destination = self.choose_destination(board, car)
            board.finish_move(destination)
            if car.position == self.targets.get(car.name):
                self.targets.pop(car.name, None)
            return True

        if car.position in board.CITY_STOPS and car.position != board.CELL_COUNT and car.money < self.CASH_RESERVE:
            board.use_city_service(self.choose_work_action(car))
            return True

        if car.fuel < car.fuel_cons and board.service_available(car.position, "fill_fuel"):
            board.use_city_service("fill_fuel")
            self.targets.pop(car.name, None)
            return True
        if car.energy <= 0 and board.service_available(car.position, "motel"):
            board.use_city_service("motel")
            self.targets.pop(car.name, None)
            return True

        if self.should_sell_collectible(board, car):
            board.use_city_service("sell_collectible")
            return True

        action = board.emergency_action(car)
        if action == "skip_wait":
            board.roll_for_current_car()
            return True
        if action == "pay_ticket":
            board.pay_ticket_current_car()
            return True
        if action == "tow_mechanic":
            board.tow_to_mechanic_current_car()
            return True
        if action == "gas_can":
            board.use_gas_can_current_car()
            return True
        if action == "tow":
            board.tow_current_car()
            return True
        if action == "coffee":
            board.drink_coffee_current_car()
            return True
        if action == "sleep":
            board.sleep_current_car()
            return True

        if self.should_fill_fuel(board, car):
            board.use_city_service("fill_fuel")
            self.targets.pop(car.name, None)
            return True
        if car.energy <= 1 and board.service_available(car.position, "motel"):
            board.use_city_service("motel")
            self.targets.pop(car.name, None)
            return True
        if car.tires == 0 and self.can_buy_and_keep_reserve(board, car, "tire", reserve=75):
            board.use_city_service("tire")
            return True
        if car.gas_cans == 0 and self.can_buy_and_keep_reserve(board, car, "gas_can", reserve=75):
            board.use_city_service("gas_can")
            return True

        target = self.survival_target(board, car)
        if target is not None:
            self.targets[car.name] = target
        else:
            self.targets.pop(car.name, None)

        board.roll_for_current_car()
        if board.move_options:
            destination = self.choose_destination(board, car)
            board.finish_move(destination)
            if car.position == self.targets.get(car.name):
                self.targets.pop(car.name, None)
        return True

    def choose_destination(self, board: Any, car: Any) -> int:
        forward_options = [pos for pos in board.move_options if pos > car.position]
        moving_options = [pos for pos in board.move_options if pos != car.position]
        choices = forward_options or moving_options or list(board.move_options)
        target = self.targets.get(car.name)
        if target is not None:
            return min(choices, key=lambda pos: (abs(pos - target), -pos))
        if self.survival_priority(board, car):
            cautious = [pos for pos in forward_options if 0 < abs(pos - car.position) <= 4]
            if cautious:
                return max(cautious)
            stay_put = [pos for pos in choices if pos == car.position]
            if stay_put:
                return stay_put[0]
            short_moves = [pos for pos in choices if abs(pos - car.position) <= 4 and pos > car.position]
            if short_moves:
                return max(short_moves)
        return max(choices, key=lambda pos: self.expected_value(board, car, pos))
