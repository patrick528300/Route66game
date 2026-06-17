"""Simple AI driver for Route 66.

The AI uses the public methods on Route66Board so the game rules stay in one
place. It handles emergencies, basic service stops, then moves toward Santa
Monica.
"""

from __future__ import annotations

from typing import Any


class Route66AI:
    def take_turn(self, board: Any) -> bool:
        car = board.current_car()

        if board.turn_done:
            board.next_turn()
            return True

        if board.move_options:
            board.finish_move(max(board.move_options))
            return True

        if car.money < 0 and car.position in board.CITY_STOPS and car.position != board.CELL_COUNT:
            if car.money <= -100:
                board.use_city_service("work_three")
            elif car.money <= -40:
                board.use_city_service("work_two")
            else:
                board.use_city_service("work_one")
            return True

        action = board.emergency_action(car)
        if action == "skip_wait":
            board.roll_for_current_car()
            return True
        if action == "pay_ticket":
            board.pay_ticket_current_car()
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

        if car.fuel <= car.fuel_tank // 2 and board.service_available(car.position, "fill_fuel"):
            board.use_city_service("fill_fuel")
            return True
        if car.name != "RV" and car.energy < 2 and board.service_available(car.position, "motel"):
            board.use_city_service("motel")
            return True
        if car.tires == 0 and board.cargo_used(car) < car.capacity and board.service_available(car.position, "tire"):
            board.use_city_service("tire")
            return True

        board.roll_for_current_car()
        return True
