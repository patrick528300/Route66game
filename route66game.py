"""A minimal Route 66 board with city stops and a service panel."""

from __future__ import annotations

import sys
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from route66_ai import Route66AI


SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
CELL_COUNT = 66
PANEL_W = 330
INFO_H = 104
GRID_COLS = 11
GRID_ROWS = 6
ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "route66_history.txt"

BG = (18, 20, 24)
BOARD = (238, 233, 220)
ROAD = (212, 77, 52)
CELL = (255, 250, 236)
CITY_CELL = (247, 190, 70)
DEST_CELL = (74, 161, 106)
GAS_CELL = (244, 220, 91)
MECHANIC_CELL = (125, 150, 178)
MOTEL_CELL = (151, 121, 188)
RIVER_CELL = (89, 166, 205)
CELL_EDGE = (40, 43, 48)
TEXT = (29, 32, 36)
MUTED = (96, 101, 108)
PANEL = (246, 244, 236)
PANEL_EDGE = (197, 190, 176)
WHITE = (255, 255, 255)
WINDOW = (188, 220, 230)
HIGHLIGHT = (80, 170, 110)
BUTTON = (48, 98, 160)
BUTTON_DISABLED = (132, 139, 146)
BUTTON_ALT = (74, 161, 106)
ERROR = (184, 64, 64)
OVERLAY = (0, 0, 0, 150)
TICKET_COST = 100


@dataclass
class Vehicle:
    name: str
    speed: int
    max_move: int
    color: tuple[int, int, int]
    position: int = 1
    money: int = 300
    energy: int = 3
    fuel: int = 0
    fuel_tank: int = 0
    fuel_cons: int = 1
    capacity: int = 0
    tires: int = 0
    arms: int = 0
    gas_cans: int = 0
    coffee: int = 0
    collectibles: int = 0
    collectible_origins: list[int] = field(default_factory=list)
    ticket_due: bool = False
    skip_turns: int = 0
    skip_reason: str = ""

CITY_STOPS = {
    1: "Chicago",
    8: "St Louis",
    18: "Oklahoma City",
    25: "Amarillo",
    35: "Santa Fe",
    45: "Flagstaff",
    55: "Barstow",
    62: "Pasadena",
    66: "Santa Monica",
}

CITY_CODES = {
    1: "CHI",
    8: "STL",
    18: "OKC",
    25: "AMA",
    35: "SFE",
    45: "FLG",
    55: "BAR",
    62: "PAS",
    66: "SM",
}

RIVER_CROSSINGS = {
    7: "East St Louis - Mississippi River Crossing",
    53: "Needles - Colorado River Crossing",
}

STATE_RANGES = [
    (1, 7, "Illinois"),
    (8, 17, "Missouri"),
    (18, 24, "Oklahoma"),
    (25, 34, "Texas"),
    (35, 44, "New Mexico"),
    (45, 53, "Arizona"),
    (54, 66, "California"),
]

SERVICE_COSTS = {
    "fill_fuel": 5,
    "motel": 30,
    "tow": 70,
    "tire": 20,
    "gas_can": 15,
    "coffee": 10,
    "arm": 40,
    "collectible": 50,
    "capacity": 50,
    "fuel_tank": 50,
    "speed": 100,
}

SERVICE_POINT_COUNTS = {
    "gas": 10,
    "mechanic": 5,
    "motel": 6,
}

SERVICE_POINT_LABELS = {
    "gas": "Gas Station",
    "mechanic": "Mechanic",
    "motel": "Motel",
}

SERVICE_POINT_CODES = {
    "gas": "G",
    "mechanic": "R",
    "motel": "M",
}

SERVICE_POINT_COLORS = {
    "gas": GAS_CELL,
    "mechanic": MECHANIC_CELL,
    "motel": MOTEL_CELL,
}


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=center))


def draw_text_left(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    surface.blit(font.render(text, True, color), pos)


class Route66Board:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Route 66")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.small = pygame.font.SysFont("Arial", 15)
        self.panel_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.title = pygame.font.SysFont("Arial", 28, bold=True)
        self.game_state = "select"
        self.human_vehicle: int | None = None
        self.ai = Route66AI()
        self.ai_next_action_at = 0
        self.CITY_STOPS = CITY_STOPS
        self.RIVER_CROSSINGS = RIVER_CROSSINGS
        self.CELL_COUNT = CELL_COUNT
        self.setup_new_game()

    def setup_new_game(self) -> None:
        self.game_state = "select"
        self.human_vehicle = None
        self.ai = Route66AI()
        self.ai_next_action_at = 0
        self.vehicles = [
            Vehicle("Sedan", speed=1, max_move=6, fuel_tank=5, fuel=5, fuel_cons=1, tires=1, gas_cans=1, color=(48, 98, 160)),
            Vehicle("RV", speed=1, max_move=5, fuel_tank=20, fuel=20, fuel_cons=4, capacity=4, tires=1, gas_cans=1, color=(128, 92, 166)),
            Vehicle("Pickup", speed=1, max_move=6, fuel_tank=15, fuel=15, fuel_cons=3, capacity=5, tires=1, gas_cans=1, color=(203, 112, 48)),
            Vehicle("Sports Car", speed=2, max_move=10, fuel_tank=5, fuel=5, fuel_cons=2, capacity=2, tires=1, gas_cans=1, color=(194, 54, 70)),
        ]
        self.vehicles[0].capacity = 3
        self.current_vehicle = 0
        self.round_number = 1
        self.die_roll: int | None = None
        self.move_range = 0
        self.move_options: set[int] = set()
        self.turn_done = False
        self.message = "Reach a city to use services."
        self.service_buttons: list[tuple[pygame.Rect, str]] = []
        self.emergency_button: tuple[pygame.Rect, str] | None = None
        self.history_button: pygame.Rect | None = None
        self.new_game_button: pygame.Rect | None = None
        self.turn_service_used = False
        self.transactions: list[str] = []
        self.show_history = False
        self.popup_title: str | None = None
        self.popup_lines: list[str] = []
        self.winner: str | None = None
        self.service_points = self.generate_service_points()
        self.price_modifiers = self.generate_price_modifiers()
        self.add_transaction("Choose a human vehicle.")

    def generate_service_points(self) -> dict[int, str]:
        rng = random.Random(66)
        unavailable = set(CITY_STOPS) | set(RIVER_CROSSINGS)
        available = [index for index in range(2, CELL_COUNT) if index not in unavailable]
        rng.shuffle(available)
        service_points: dict[int, str] = {}
        cursor = 0
        for kind, count in SERVICE_POINT_COUNTS.items():
            for position in available[cursor:cursor + count]:
                service_points[position] = kind
            cursor += count
        return service_points

    def generate_price_modifiers(self) -> dict[int, float]:
        rng = random.Random(660)
        priced_stops = set(CITY_STOPS) | set(self.service_points)
        priced_stops.discard(CELL_COUNT)
        return {position: rng.uniform(0.85, 1.15) for position in priced_stops}

    def price_at(self, position: int, action: str) -> int:
        if action == "fill_fuel":
            return self.fuel_price_at(position)
        if action == "gas_can":
            return self.fuel_price_at(position) * 2 + 5
        base = SERVICE_COSTS[action]
        modifier = self.price_modifiers.get(position, 1.0)
        return max(1, round(base * modifier))

    def fuel_price_at(self, position: int) -> int:
        modifier = self.price_modifiers.get(position, 1.0)
        if 18 <= position <= 35:
            low, high = 2, 3
        elif 45 <= position <= 57:
            low, high = 4, 5
        elif position > 57:
            low, high = 5, 6
        else:
            low, high = 3, 4
        return high if modifier >= 1.0 else low

    def board_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        margin = 42
        return pygame.Rect(margin, margin, width - PANEL_W - margin * 3, height - INFO_H - margin * 3)

    def vehicle_info_rect(self) -> pygame.Rect:
        board = self.board_rect()
        return pygame.Rect(board.x, board.bottom + 18, board.width, INFO_H)

    def panel_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        margin = 42
        return pygame.Rect(width - PANEL_W - margin, margin, PANEL_W, height - margin * 2)

    def cell_size(self, rect: pygame.Rect) -> int:
        gap = 24
        return max(
            24,
            min(
                (rect.width - gap * GRID_COLS) // GRID_COLS,
                (rect.height - gap * (GRID_ROWS - 1)) // GRID_ROWS,
                58,
            ),
        )

    def cell_centers(self) -> list[tuple[int, int]]:
        rect = self.board_rect()
        size = self.cell_size(rect)
        x_gap = (rect.width - size * GRID_COLS) / GRID_COLS
        y_gap = (rect.height - size * GRID_ROWS) / (GRID_ROWS - 1)
        centers: list[tuple[int, int]] = []

        for row in range(GRID_ROWS):
            row_centers: list[tuple[int, int]] = []
            row_offset = x_gap / 2 if row % 2 else 0
            for col in range(GRID_COLS):
                x = round(rect.x + x_gap / 2 + row_offset + size / 2 + col * (size + x_gap))
                y = round(rect.y + size / 2 + row * (size + y_gap))
                row_centers.append((x, y))
            if row % 2 == 1:
                row_centers.reverse()
            centers.extend(row_centers)

        return centers[:CELL_COUNT]

    def cell_at(self, pos: tuple[int, int]) -> int | None:
        board = self.board_rect()
        size = self.cell_size(board)
        hit_size = max(size + 8, 20)
        for index, center in enumerate(self.cell_centers(), start=1):
            rect = pygame.Rect(0, 0, hit_size, hit_size)
            rect.center = center
            if rect.collidepoint(pos):
                return index
        return None

    def move_player(self, delta: int) -> None:
        vehicle = self.vehicles[self.current_vehicle]
        vehicle.position = max(1, min(CELL_COUNT, vehicle.position + delta))

    def go_button_rect(self) -> pygame.Rect:
        panel = self.panel_rect()
        return pygame.Rect(panel.right - 116, panel.bottom - 58, 86, 38)

    def emergency_button_rect(self) -> pygame.Rect:
        panel = self.panel_rect()
        return pygame.Rect(panel.x + 18, panel.bottom - 58, 96, 38)

    def history_button_rect(self) -> pygame.Rect:
        panel = self.panel_rect()
        return pygame.Rect(panel.x + 132, panel.bottom - 58, 86, 38)

    def new_game_button_rect(self) -> pygame.Rect:
        panel = self.panel_rect()
        return pygame.Rect(panel.x + 18, panel.bottom - 104, panel.width - 36, 34)

    def popup_ok_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        return pygame.Rect(width // 2 - 44, height // 2 + 104, 88, 36)

    def selection_card_rects(self) -> list[pygame.Rect]:
        width, height = self.screen.get_size()
        card_w = min(250, (width - 140) // 4)
        card_h = 250
        gap = 22
        total_w = card_w * 4 + gap * 3
        start_x = (width - total_w) // 2
        y = max(170, height // 2 - card_h // 2 + 30)
        return [pygame.Rect(start_x + idx * (card_w + gap), y, card_w, card_h) for idx in range(4)]

    def select_vehicle(self, index: int) -> None:
        self.human_vehicle = index
        self.game_state = "play"
        self.transactions.clear()
        self.add_transaction(f"Human chose {self.vehicles[index].name}. Other cars are AI.")
        self.message = f"You are driving the {self.vehicles[index].name}."

    def is_human_turn(self) -> bool:
        return self.human_vehicle == self.current_vehicle

    def is_ai_car(self, car: Vehicle) -> bool:
        if self.human_vehicle is None:
            return False
        return any(vehicle is car and index != self.human_vehicle for index, vehicle in enumerate(self.vehicles))

    def reward_ai_state(self, car: Vehicle, reward: float, reason: str) -> None:
        if not self.is_ai_car(car):
            return
        self.ai.remember(self, car, reward)
        self.add_transaction(f"AI value {reward:+.0f} for {car.name}: {reason}.")

    def rankings(self) -> list[tuple[int, Vehicle]]:
        return sorted(enumerate(self.vehicles), key=lambda item: (-item[1].position, item[0]))

    def rank_for_car(self, target: Vehicle) -> int:
        for rank, (_, car) in enumerate(self.rankings(), start=1):
            if car is target:
                return rank
        return len(self.vehicles)

    def current_car(self) -> Vehicle:
        return self.vehicles[self.current_vehicle]

    def add_transaction(self, text: str) -> None:
        self.transactions.append(f"R{self.round_number} {text}")

    def open_popup(self, title: str, lines: list[str]) -> None:
        self.popup_title = title
        self.popup_lines = lines

    def close_popup(self) -> None:
        self.popup_title = None
        self.popup_lines = []

    def movement_block_reason(self, car: Vehicle) -> str | None:
        if car.skip_turns > 0:
            reason = car.skip_reason or "Waiting"
            return f"{reason}. Skip this turn."
        if car.money <= 0 and car.position in CITY_STOPS and car.position != CELL_COUNT:
            return "Debt in big city. Work until money is above $0."
        if car.ticket_due:
            return "Ticket unpaid. Pay $100 before moving."
        if car.fuel < car.fuel_cons:
            return "Fuel is empty. Tow to nearest city service."
        if car.name != "RV" and car.energy <= 0:
            return "Energy is empty. Sleep before moving."
        return None

    def emergency_action(self, car: Vehicle) -> str | None:
        if car.skip_turns > 0:
            return "skip_wait"
        if car.ticket_due:
            return "pay_ticket"
        if car.fuel < car.fuel_cons and car.gas_cans > 0:
            return "gas_can"
        if car.fuel < car.fuel_cons:
            return "tow"
        if car.name != "RV" and car.energy <= 0 and car.coffee > 0:
            return "coffee"
        if car.name != "RV" and car.energy <= 0:
            return "sleep"
        return None

    def roll_for_current_car(self) -> None:
        if self.turn_done:
            self.next_turn()
            return
        car = self.current_car()
        if car.skip_turns > 0:
            reason = car.skip_reason or "waiting"
            car.skip_turns -= 1
            self.turn_done = True
            if car.skip_turns == 0:
                car.skip_reason = ""
            self.message = f"{car.name} is {reason}. Turn skipped."
            self.add_transaction(f"{car.name} skipped a turn: {reason}.")
            return
        blocked = self.movement_block_reason(car)
        if blocked:
            self.message = blocked
            return
        self.die_roll = random.randint(1, 6)
        self.move_range = min(self.die_roll * car.speed, car.max_move)
        self.add_transaction(f"{car.name} rolled {self.die_roll}; move range is {self.move_range}.")
        if car.position in RIVER_CROSSINGS and self.die_roll % 2 == 0:
            river = RIVER_CROSSINGS[car.position]
            self.move_range = 0
            self.turn_done = True
            self.message = f"{car.name} must wait at {river}; even roll freezes fuel and energy."
            self.add_transaction(f"{car.name} rolled even at {river}; stayed with fuel and energy frozen.")
            self.open_popup("River Crossing", [f"{car.name} rolled {self.die_roll} at {river}.", "Even roll: stay here.", "Fuel and energy are not spent."])
            return
        start = car.position
        low = max(1, start - self.move_range)
        high = min(CELL_COUNT, start + self.move_range)
        self.move_options = {
            position for position in range(low, high + 1)
            if self.can_move_without_passing_river(start, position)
            and self.can_move_without_passing_debt_city(car, start, position)
        }

    def can_move_without_passing_river(self, start: int, destination: int) -> bool:
        if destination == start:
            return True
        if destination > start:
            crossings = sorted(pos for pos in RIVER_CROSSINGS if start < pos <= destination)
            return not crossings or destination == crossings[0]
        crossings = sorted((pos for pos in RIVER_CROSSINGS if destination <= pos < start), reverse=True)
        return not crossings or destination == crossings[0]

    def can_move_without_passing_debt_city(self, car: Vehicle, start: int, destination: int) -> bool:
        if car.money >= 0 or destination == start:
            return True
        if destination > start:
            cities = sorted(pos for pos in CITY_STOPS if start < pos <= destination and pos != CELL_COUNT)
            return not cities or destination == cities[0]
        cities = sorted((pos for pos in CITY_STOPS if destination <= pos < start and pos != CELL_COUNT), reverse=True)
        return not cities or destination == cities[0]

    def finish_move(self, destination: int) -> None:
        car = self.current_car()
        start = car.position
        distance = abs(destination - start)
        car.position = destination
        if car.name != "RV":
            car.energy = max(0, car.energy - 1)
        car.fuel = max(0, car.fuel - car.fuel_cons)
        self.move_options.clear()
        self.die_roll = None
        self.move_range = 0
        self.turn_done = True
        self.turn_service_used = False
        city = CITY_STOPS.get(car.position)
        self.message = f"{car.name} reached {city}." if city else f"{car.name} reached block {car.position}."
        self.add_transaction(f"{car.name} moved from {start} to {destination}, spent {car.fuel_cons} fuel.")
        if distance > 4:
            event_result = self.resolve_long_move_event(car, distance)
            if event_result == "none":
                self.reward_ai_state(car, +10, "moved 5+ blocks without penalty")
            else:
                self.reward_ai_state(car, -10, "moved 5+ blocks with penalty")
        elif distance > 0:
            self.reward_ai_state(car, +5, "moved 1-4 blocks")
        if car.position in CITY_STOPS and car.position != start:
            rank = self.rank_for_car(car)
            reward = 15 + (5 - rank)
            self.reward_ai_state(car, reward, f"entered {CITY_STOPS[car.position]} at rank {rank}")
        if car.position != CELL_COUNT:
            self.maybe_show_state_entry(car, start, car.position)
        if car.position == CELL_COUNT and self.winner is None:
            self.winner = car.name
            self.add_transaction(f"{car.name} reached Santa Monica and won the game.")
            self.export_history()
            self.open_popup("Game Over", [f"{car.name} reached Santa Monica.", f"History exported to {HISTORY_PATH.name}."])

    def next_turn(self) -> None:
        self.current_vehicle = (self.current_vehicle + 1) % len(self.vehicles)
        if self.current_vehicle == 0:
            self.round_number += 1
        self.die_roll = None
        self.move_range = 0
        self.turn_done = False
        self.turn_service_used = False
        self.message = f"{self.current_car().name}'s turn."

    def charge_forced_cost(self, car: Vehicle, cost: int, reason: str) -> None:
        car.money -= cost
        self.add_transaction(f"{car.name} paid ${cost} for {reason}.")
        if car.money < 0:
            self.reward_ai_state(car, -10, "money below zero")

    def resolve_long_move_event(self, car: Vehicle, distance: int) -> str:
        event_roll = random.randint(1, 3)
        if event_roll == 1:
            car.ticket_due = True
            self.message = f"{car.name} got a $100 ticket."
            self.add_transaction(f"{car.name} moved {distance} blocks and got a $100 ticket.")
            self.reward_ai_state(car, -10, "ticket")
            self.open_popup("Ticket", [f"{car.name} moved {distance} blocks.", "Police issued a $100 ticket.", "Pay it before this car can move again."])
            return "penalty"
        elif event_roll == 2:
            if car.tires > 0:
                car.tires -= 1
                self.message = f"{car.name} blew a tire and used a spare."
                self.add_transaction(f"{car.name} moved {distance} blocks, blew a tire, and used 1 spare.")
                self.reward_ai_state(car, +10, "spare tire prevented tow")
                self.open_popup("Tire Blowout", [f"{car.name} moved {distance} blocks.", "A tire blew out.", "Used 1 spare tire."])
            else:
                destination = self.nearest_service_stop(car.position, "mechanic")
                city = self.stop_name(destination)
                car.position = destination
                self.charge_forced_cost(car, SERVICE_COSTS["tow"], "towing after tire blowout")
                self.message = f"{car.name} blew a tire and was towed to {city}."
                self.add_transaction(f"{car.name} had no spare tire and was towed to {city}.")
                self.open_popup("Tire Blowout", [f"{car.name} moved {distance} blocks.", "No spare tire available.", f"Towed to {city} for $70."])
            return "penalty"
        else:
            self.add_transaction(f"{car.name} moved {distance} blocks; no long-distance event.")
            return "none"

    def nearest_service_city(self, position: int) -> int:
        service_stops = [stop for stop in CITY_STOPS if stop != CELL_COUNT]
        return min(service_stops, key=lambda stop: (abs(stop - position), stop))

    def nearest_service_stop(self, position: int, service_kind: str) -> int:
        service_stops = [stop for stop in CITY_STOPS if stop != CELL_COUNT]
        service_stops.extend(stop for stop, kind in self.service_points.items() if kind == service_kind)
        return min(service_stops, key=lambda stop: (abs(stop - position), stop))

    def preferred_service_stop(self, position: int, service_kind: str) -> int:
        service_stops = sorted([stop for stop in CITY_STOPS if stop != CELL_COUNT])
        service_stops.extend(stop for stop, kind in self.service_points.items() if kind == service_kind)
        service_stops = sorted(set(service_stops))
        previous_stops = [stop for stop in service_stops if stop < position]
        if previous_stops:
            previous = previous_stops[-1]
            if position - previous < 3:
                return previous
        future_stops = [stop for stop in service_stops if stop > position]
        if future_stops:
            return future_stops[0]
        return previous_stops[-1] if previous_stops else position

    def stop_name(self, position: int) -> str:
        if position in CITY_STOPS:
            return CITY_STOPS[position]
        if position in RIVER_CROSSINGS:
            return RIVER_CROSSINGS[position]
        return SERVICE_POINT_LABELS[self.service_points[position]]

    def state_for_position(self, position: int) -> str:
        for start, end, state in STATE_RANGES:
            if start <= position <= end:
                return state
        return "Route 66"

    def maybe_show_state_entry(self, car: Vehicle, start: int, destination: int) -> None:
        if self.human_vehicle is None or self.vehicles[self.human_vehicle] is not car:
            return
        old_state = self.state_for_position(start)
        new_state = self.state_for_position(destination)
        if old_state == new_state:
            return
        self.add_transaction(f"{car.name} entered {new_state}.")
        self.open_popup("Entering State", [f"Entering {new_state}", "Route 66 continues west."])

    def spend_money(self, car: Vehicle, cost: int) -> bool:
        car.money -= cost
        if car.money < 0:
            self.reward_ai_state(car, -10, "money below zero")
        return True

    def cargo_used(self, car: Vehicle) -> int:
        return car.tires + car.arms + car.gas_cans + car.coffee + car.collectibles

    def collectible_sell_value(self, origin: int, position: int) -> int:
        distance = abs(position - origin)
        return SERVICE_COSTS["collectible"] + distance * 3

    def best_collectible_sale(self, car: Vehicle) -> tuple[int, int] | None:
        if car.collectibles <= 0:
            return None
        while len(car.collectible_origins) < car.collectibles:
            car.collectible_origins.append(1)
        best_index = max(
            range(len(car.collectible_origins)),
            key=lambda index: self.collectible_sell_value(car.collectible_origins[index], car.position),
        )
        origin = car.collectible_origins[best_index]
        return best_index, self.collectible_sell_value(origin, car.position)

    def has_cargo_space(self, car: Vehicle) -> bool:
        if self.cargo_used(car) >= car.capacity:
            self.message = "Cargo is full."
            return False
        return True

    def use_city_service(self, action: str) -> None:
        if self.move_options:
            return
        car = self.current_car()
        if not self.service_available(car.position, action):
            self.message = "This service is not available here."
            return
        debt_locked = car.money <= 0 and car.position in CITY_STOPS and car.position != CELL_COUNT
        if debt_locked and action not in {"work_one", "work_two", "work_three", "sell_collectible"}:
            self.message = "Debt rule: work in this city until money is above $0."
            return
        turn_service = action in {"motel", "work_one", "work_two", "work_three", "capacity", "fuel_tank", "speed"}
        if turn_service and self.turn_service_used and not (debt_locked and action in {"work_one", "work_two", "work_three"}):
            self.message = "This turn already used a work or upgrade service."
            return

        if action == "fill_fuel":
            needed = car.fuel_tank - car.fuel
            if needed <= 0:
                self.message = "Fuel tank is already full."
                return
            unit_price = self.price_at(car.position, action)
            cost = needed * unit_price
            if self.spend_money(car, cost):
                car.fuel = car.fuel_tank
                self.message = f"Filled fuel for ${cost}."
                self.add_transaction(f"{car.name} filled fuel for ${cost} (${unit_price}/fuel).")
        elif action == "motel":
            cost = self.price_at(car.position, action)
            if self.spend_money(car, cost):
                car.energy = 3
                self.turn_done = True
                self.turn_service_used = True
                self.message = "Slept at motel. Energy restored to 3. Turn finished."
                self.add_transaction(f"{car.name} stayed at motel for ${cost}.")
        elif action == "tire":
            cost = self.price_at(car.position, action)
            if self.has_cargo_space(car) and self.spend_money(car, cost):
                car.tires += 1
                self.message = f"Bought 1 tire for ${cost}."
                self.add_transaction(f"{car.name} bought 1 tire for ${cost}.")
                self.reward_ai_state(car, +5, "bought tire")
        elif action == "gas_can":
            cost = self.price_at(car.position, action)
            if self.has_cargo_space(car) and self.spend_money(car, cost):
                car.gas_cans += 1
                self.message = f"Bought 1 gas can for ${cost}."
                self.add_transaction(f"{car.name} bought 1 gas can for ${cost}.")
                self.reward_ai_state(car, +5, "bought gas can")
        elif action == "coffee":
            cost = self.price_at(car.position, action)
            if self.has_cargo_space(car) and self.spend_money(car, cost):
                car.coffee += 1
                self.message = f"Bought 1 coffee for ${cost}."
                self.add_transaction(f"{car.name} bought 1 coffee for ${cost}.")
        elif action == "arm":
            cost = self.price_at(car.position, action)
            if self.has_cargo_space(car) and self.spend_money(car, cost):
                car.arms += 1
                self.message = f"Bought 1 arm for ${cost}."
                self.add_transaction(f"{car.name} bought 1 arm for ${cost}.")
        elif action == "collectible":
            cost = self.price_at(car.position, action)
            if self.has_cargo_space(car) and self.spend_money(car, cost):
                car.collectibles += 1
                car.collectible_origins.append(car.position)
                self.message = f"Bought 1 collectible for ${cost}."
                self.add_transaction(f"{car.name} bought 1 collectible for ${cost}.")
        elif action == "sell_collectible":
            sale = self.best_collectible_sale(car)
            if sale is None:
                self.message = "No collectible to sell."
                return
            index, value = sale
            origin = car.collectible_origins.pop(index)
            car.collectibles -= 1
            car.money += value
            self.message = f"Sold 1 collectible for ${value}."
            self.add_transaction(
                f"{car.name} sold 1 collectible bought at block {origin} for ${value}."
            )
        elif action == "work_one":
            was_in_debt = car.money < 0
            car.money += 40
            car.skip_turns = 1
            car.skip_reason = "working 1 turn"
            self.turn_done = True
            self.turn_service_used = True
            self.message = "Work started. Earned $40 and must skip 1 turn."
            self.add_transaction(f"{car.name} worked 1 turn, earned $40, and must skip 1 turn.")
            if was_in_debt:
                self.reward_ai_state(car, +20, "stopped and worked while in debt")
        elif action == "work_two":
            was_in_debt = car.money < 0
            car.money += 100
            car.skip_turns = 2
            car.skip_reason = "working 2 turns"
            self.turn_done = True
            self.turn_service_used = True
            self.message = "Work started. Earned $100 and must skip 2 turns."
            self.add_transaction(f"{car.name} worked 2 turns, earned $100, and must skip 2 turns.")
            if was_in_debt:
                self.reward_ai_state(car, +20, "stopped and worked while in debt")
        elif action == "work_three":
            was_in_debt = car.money < 0
            car.money += 150
            car.skip_turns = 3
            car.skip_reason = "working 3 turns"
            self.turn_done = True
            self.turn_service_used = True
            self.message = "Work started. Earned $150 and must skip 3 turns."
            self.add_transaction(f"{car.name} worked 3 turns, earned $150, and must skip 3 turns.")
            if was_in_debt:
                self.reward_ai_state(car, +20, "stopped and worked while in debt")
        elif action == "capacity":
            cost = self.price_at(car.position, action)
            if self.spend_money(car, cost):
                car.capacity += 2
                car.fuel_cons += 1
                self.turn_done = True
                self.turn_service_used = True
                self.message = "Upgraded capacity +2. Fuel use +1. Turn finished."
                self.add_transaction(f"{car.name} upgraded capacity for ${cost}.")
        elif action == "fuel_tank":
            cost = self.price_at(car.position, action)
            if self.spend_money(car, cost):
                car.fuel_tank += 3
                car.fuel_cons += 1
                self.turn_done = True
                self.turn_service_used = True
                self.message = "Upgraded fuel tank +3. Fuel use +1. Turn finished."
                self.add_transaction(f"{car.name} upgraded fuel tank for ${cost}.")
        elif action == "speed":
            cost = self.price_at(car.position, action)
            if self.spend_money(car, cost):
                car.speed += 1
                car.max_move += 5
                car.fuel_cons += 1
                self.turn_done = True
                self.turn_service_used = True
                self.message = "Upgraded speed +1. Fuel use +1. Turn finished."
                self.add_transaction(f"{car.name} upgraded speed for ${cost}.")

    def service_available(self, position: int, action: str) -> bool:
        if position in CITY_STOPS and position != CELL_COUNT:
            return True
        service_kind = self.service_points.get(position)
        allowed = {
            "gas": {"fill_fuel", "gas_can", "coffee"},
            "mechanic": {"tire", "capacity", "fuel_tank", "speed"},
            "motel": {"motel"},
        }
        return action in allowed.get(service_kind, set())

    def pay_ticket_current_car(self) -> None:
        if self.move_options:
            return
        car = self.current_car()
        if not car.ticket_due:
            self.message = "No ticket to pay."
            return
        if self.spend_money(car, TICKET_COST):
            car.ticket_due = False
            self.message = "Ticket paid."
            self.add_transaction(f"{car.name} paid a $100 ticket.")

    def tow_current_car(self) -> None:
        if self.move_options or self.turn_done:
            return
        car = self.current_car()
        if car.fuel >= car.fuel_cons:
            self.message = "Tow is only needed when fuel is empty."
            return
        if not self.spend_money(car, SERVICE_COSTS["tow"]):
            return
        destination = self.preferred_service_stop(car.position, "gas")
        car.position = destination
        self.turn_done = True
        self.turn_service_used = True
        city = self.stop_name(destination)
        self.message = f"Towed to {city} for $70. Turn finished."
        self.add_transaction(f"{car.name} was towed to {city} for $70.")

    def use_gas_can_current_car(self) -> None:
        if self.move_options or self.turn_done:
            return
        car = self.current_car()
        if car.gas_cans <= 0 or car.fuel >= car.fuel_cons:
            self.message = "Gas can is only needed when fuel is too low."
            return
        car.gas_cans -= 1
        car.fuel = min(car.fuel_tank, car.fuel + 2)
        self.message = "Used 1 gas can. Fuel +2."
        self.add_transaction(f"{car.name} used 1 gas can and restored 2 fuel.")
        self.reward_ai_state(car, +10, "gas can prevented tow")

    def sleep_current_car(self) -> None:
        if self.move_options or self.turn_done:
            return
        car = self.current_car()
        if car.name == "RV" or car.energy > 0:
            self.message = "Sleep is only needed when energy is empty."
            return
        car.energy = min(3, car.energy + 1)
        car.skip_turns = 1
        car.skip_reason = "sleeping on the road"
        self.turn_done = True
        self.turn_service_used = True
        self.message = "Slept on the road. Energy +1. Must skip next turn."
        self.add_transaction(f"{car.name} slept on the road; energy restored by 1 and must skip next turn.")

    def drink_coffee_current_car(self) -> None:
        if self.move_options or self.turn_done:
            return
        car = self.current_car()
        if car.coffee <= 0 or car.energy > 0 or car.name == "RV":
            self.message = "Coffee can only be used when energy is empty."
            return
        car.coffee -= 1
        car.energy = 1
        self.message = "Drank coffee. Energy +1; this car can move this turn."
        self.add_transaction(f"{car.name} consumed 1 coffee and restored 1 energy.")

    def export_history(self) -> None:
        HISTORY_PATH.write_text("\n".join(self.transactions) + "\n")
        self.message = f"History exported to {HISTORY_PATH.name}."

    def draw(self) -> None:
        if self.game_state == "select":
            self.draw_selection_screen()
            return

        self.screen.fill(BG)
        board = self.board_rect()
        pygame.draw.rect(self.screen, BOARD, board, border_radius=8)

        centers = self.cell_centers()
        size = self.cell_size(board)

        for start, end in zip(centers, centers[1:]):
            pygame.draw.line(self.screen, ROAD, start, end, max(5, size // 10))

        for index, center in enumerate(centers, start=1):
            is_city = index in CITY_STOPS
            is_river = index in RIVER_CROSSINGS
            service_kind = self.service_points.get(index)
            rect_size = size + 14 if is_city or is_river else size
            rect = pygame.Rect(0, 0, rect_size, rect_size)
            rect.center = center
            color = DEST_CELL if index == CELL_COUNT else CITY_CELL if is_city else CELL
            if is_river:
                color = RIVER_CELL
            if service_kind and not is_city:
                color = SERVICE_POINT_COLORS[service_kind]
            if index in self.move_options:
                color = HIGHLIGHT
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, CELL_EDGE, rect, 3, border_radius=6)
            number_font = self.small if is_city else self.font
            draw_text(self.screen, number_font, str(index), center, TEXT)
            self.draw_stop_icon(rect, index)

        self.draw_vehicles(centers)
        self.draw_vehicle_info()
        self.draw_panel()
        self.draw_hover_tooltip()
        self.draw_popup()

        pygame.display.flip()

    def draw_selection_screen(self) -> None:
        self.screen.fill(BG)
        width, _ = self.screen.get_size()
        draw_text(self.screen, self.title, "Choose Your Vehicle", (width // 2, 86), WHITE)
        draw_text(self.screen, self.panel_font, "Human player picks first. The other three cars will be AI controlled.", (width // 2, 124), (210, 214, 218))

        for idx, (rect, car) in enumerate(zip(self.selection_card_rects(), self.vehicles)):
            pygame.draw.rect(self.screen, PANEL, rect, border_radius=8)
            pygame.draw.rect(self.screen, PANEL_EDGE, rect, 2, border_radius=8)
            self.draw_car_icon(car, (rect.centerx, rect.y + 62), 1.15)
            draw_text(self.screen, self.title, car.name, (rect.centerx, rect.y + 116), TEXT)
            lines = [
                f"Speed: {car.speed}",
                f"Max move: {car.max_move}",
                f"Fuel: {car.fuel_tank}",
                f"Fuel use: {car.fuel_cons}",
                f"Capacity: {car.capacity}",
            ]
            y = rect.y + 148
            for line in lines:
                draw_text_left(self.screen, self.panel_font, line, (rect.x + 24, y), MUTED)
                y += 22
            button = pygame.Rect(rect.x + 36, rect.bottom - 44, rect.width - 72, 30)
            pygame.draw.rect(self.screen, BUTTON, button, border_radius=7)
            draw_text(self.screen, self.panel_font, "Select", button.center, WHITE)

        pygame.display.flip()

    def draw_vehicles(self, centers: list[tuple[int, int]]) -> None:
        offsets = [(-13, -22), (13, -22), (-13, 22), (13, 22)]
        for index, car in enumerate(self.vehicles):
            center = centers[car.position - 1]
            ox, oy = offsets[index]
            car_center = (center[0] + ox, center[1] + oy)
            body = self.draw_car_icon(car, car_center, 0.46)
            if index == self.current_vehicle:
                pygame.draw.rect(self.screen, WHITE, body.inflate(6, 6), 2, border_radius=7)

    def draw_stop_icon(self, cell: pygame.Rect, position: int) -> None:
        icon = pygame.Rect(0, 0, 21, 21)
        icon.center = (cell.right - 5, cell.top + 5)
        if position in CITY_STOPS and position != CELL_COUNT:
            pygame.draw.rect(self.screen, WHITE, icon, border_radius=3)
            pygame.draw.rect(self.screen, CELL_EDGE, icon, 1, border_radius=3)
            base_y = icon.bottom - 4
            for idx, height in enumerate((11, 15, 8)):
                building = pygame.Rect(icon.x + 3 + idx * 5, base_y - height, 4, height)
                pygame.draw.rect(self.screen, TEXT, building)
            return
        if position in RIVER_CROSSINGS:
            pygame.draw.circle(self.screen, WHITE, icon.center, 11)
            pygame.draw.circle(self.screen, CELL_EDGE, icon.center, 11, 1)
            for offset in (-4, 2):
                pygame.draw.arc(self.screen, RIVER_CELL, icon.inflate(-4, -10).move(0, offset), 0, 3.14, 2)
            return
        service_kind = self.service_points.get(position)
        if not service_kind:
            return
        pygame.draw.circle(self.screen, WHITE, icon.center, 11)
        pygame.draw.circle(self.screen, CELL_EDGE, icon.center, 11, 1)
        if service_kind == "gas":
            pump = pygame.Rect(icon.x + 6, icon.y + 5, 8, 12)
            pygame.draw.rect(self.screen, TEXT, pump, border_radius=2)
            pygame.draw.rect(self.screen, GAS_CELL, pump.inflate(-3, -6))
            pygame.draw.line(self.screen, TEXT, (pump.right, pump.y + 4), (icon.right - 4, icon.y + 8), 2)
        elif service_kind == "mechanic":
            pygame.draw.line(self.screen, TEXT, (icon.x + 5, icon.bottom - 6), (icon.right - 5, icon.y + 6), 3)
            pygame.draw.circle(self.screen, TEXT, (icon.x + 7, icon.bottom - 7), 3, 2)
            pygame.draw.circle(self.screen, TEXT, (icon.right - 6, icon.y + 6), 3, 2)
        elif service_kind == "motel":
            bed = pygame.Rect(icon.x + 4, icon.y + 10, 13, 6)
            pygame.draw.rect(self.screen, TEXT, bed, border_radius=2)
            pygame.draw.rect(self.screen, MOTEL_CELL, (bed.x + 2, bed.y - 4, 5, 4), border_radius=1)
            pygame.draw.line(self.screen, TEXT, (bed.x, bed.bottom), (bed.x, bed.bottom + 3), 2)
            pygame.draw.line(self.screen, TEXT, (bed.right, bed.bottom), (bed.right, bed.bottom + 3), 2)

    def hover_label(self, position: int) -> str:
        if position in CITY_STOPS:
            return f"{position}. {CITY_STOPS[position]} - Big City"
        if position in RIVER_CROSSINGS:
            return f"{position}. {RIVER_CROSSINGS[position]} - River Crossing"
        service_kind = self.service_points.get(position)
        if service_kind:
            return f"{position}. {SERVICE_POINT_LABELS[service_kind]}"
        return f"{position}. Road"

    def draw_hover_tooltip(self) -> None:
        if self.popup_title or self.show_history:
            return
        mouse_pos = pygame.mouse.get_pos()
        cell = self.cell_at(mouse_pos)
        if cell is None:
            return
        label = self.hover_label(cell)
        rendered = self.small.render(label, True, TEXT)
        rect = rendered.get_rect()
        rect.topleft = (mouse_pos[0] + 14, mouse_pos[1] + 14)
        screen_w, screen_h = self.screen.get_size()
        rect.x = min(rect.x, screen_w - rect.width - 12)
        rect.y = min(rect.y, screen_h - rect.height - 12)
        bg = rect.inflate(12, 8)
        pygame.draw.rect(self.screen, WHITE, bg, border_radius=5)
        pygame.draw.rect(self.screen, CELL_EDGE, bg, 1, border_radius=5)
        self.screen.blit(rendered, rect)

    def draw_car_icon(self, car: Vehicle, center: tuple[int, int], scale: float) -> pygame.Rect:
        if car.name == "Sedan":
            return self.draw_sedan(car, center, scale)
        if car.name == "RV":
            return self.draw_rv(car, center, scale)
        if car.name == "Pickup":
            return self.draw_pickup(car, center, scale)
        return self.draw_sports_car(car, center, scale)

    def draw_wheels(self, body: pygame.Rect, scale: float) -> None:
        radius = max(3, round(6 * scale))
        y = body.bottom - radius + round(2 * scale)
        for x in (body.left + round(body.width * 0.22), body.right - round(body.width * 0.22)):
            pygame.draw.circle(self.screen, CELL_EDGE, (x, y), radius)
            pygame.draw.circle(self.screen, (210, 210, 205), (x, y), max(1, radius // 2))

    def draw_sedan(self, car: Vehicle, center: tuple[int, int], scale: float) -> pygame.Rect:
        body = pygame.Rect(0, 0, round(58 * scale), round(24 * scale))
        body.center = center
        roof = pygame.Rect(0, 0, round(31 * scale), round(16 * scale))
        roof.midbottom = (body.centerx, body.y + round(8 * scale))
        pygame.draw.rect(self.screen, car.color, body, border_radius=round(8 * scale))
        pygame.draw.polygon(
            self.screen,
            car.color,
            [
                (roof.left, roof.bottom),
                (roof.left + round(8 * scale), roof.top),
                (roof.right - round(8 * scale), roof.top),
                (roof.right, roof.bottom),
            ],
        )
        pygame.draw.rect(self.screen, WINDOW, roof.inflate(round(-10 * scale), round(-7 * scale)), border_radius=round(3 * scale))
        self.draw_wheels(body, scale)
        return body

    def draw_rv(self, car: Vehicle, center: tuple[int, int], scale: float) -> pygame.Rect:
        body = pygame.Rect(0, 0, round(74 * scale), round(34 * scale))
        body.center = center
        pygame.draw.rect(self.screen, car.color, body, border_radius=round(7 * scale))
        cab = pygame.Rect(body.right - round(22 * scale), body.y + round(6 * scale), round(16 * scale), round(13 * scale))
        side_window = pygame.Rect(body.x + round(11 * scale), body.y + round(7 * scale), round(18 * scale), round(11 * scale))
        door = pygame.Rect(body.x + round(36 * scale), body.y + round(7 * scale), round(12 * scale), round(22 * scale))
        pygame.draw.rect(self.screen, WINDOW, side_window, border_radius=round(2 * scale))
        pygame.draw.rect(self.screen, WINDOW, cab, border_radius=round(2 * scale))
        pygame.draw.rect(self.screen, PANEL_EDGE, door, 1, border_radius=round(2 * scale))
        pygame.draw.line(self.screen, WHITE, (body.x + round(7 * scale), body.centery), (body.right - round(7 * scale), body.centery), max(1, round(2 * scale)))
        self.draw_wheels(body, scale)
        return body

    def draw_pickup(self, car: Vehicle, center: tuple[int, int], scale: float) -> pygame.Rect:
        body = pygame.Rect(0, 0, round(66 * scale), round(25 * scale))
        body.center = center
        cab = pygame.Rect(body.x + round(8 * scale), body.y - round(8 * scale), round(26 * scale), round(19 * scale))
        bed = pygame.Rect(body.x + round(36 * scale), body.y + round(5 * scale), round(25 * scale), round(13 * scale))
        pygame.draw.rect(self.screen, car.color, body, border_radius=round(6 * scale))
        pygame.draw.rect(self.screen, car.color, cab, border_radius=round(5 * scale))
        pygame.draw.rect(self.screen, WINDOW, cab.inflate(round(-9 * scale), round(-7 * scale)), border_radius=round(2 * scale))
        pygame.draw.rect(self.screen, (115, 86, 55), bed, border_radius=round(3 * scale))
        pygame.draw.line(self.screen, CELL_EDGE, (bed.left, bed.top), (bed.right, bed.top), max(1, round(2 * scale)))
        self.draw_wheels(body, scale)
        return body.union(cab)

    def draw_sports_car(self, car: Vehicle, center: tuple[int, int], scale: float) -> pygame.Rect:
        body = pygame.Rect(0, 0, round(68 * scale), round(21 * scale))
        body.center = center
        pygame.draw.polygon(
            self.screen,
            car.color,
            [
                (body.left, body.bottom - round(6 * scale)),
                (body.left + round(12 * scale), body.y + round(4 * scale)),
                (body.left + round(42 * scale), body.y),
                (body.right - round(5 * scale), body.y + round(8 * scale)),
                (body.right, body.bottom - round(4 * scale)),
                (body.left + round(7 * scale), body.bottom),
            ],
        )
        window = pygame.Rect(body.left + round(27 * scale), body.y + round(3 * scale), round(19 * scale), round(8 * scale))
        pygame.draw.rect(self.screen, WINDOW, window, border_radius=round(3 * scale))
        pygame.draw.line(self.screen, WHITE, (body.left + round(8 * scale), body.bottom - round(7 * scale)), (body.right - round(7 * scale), body.bottom - round(7 * scale)), max(1, round(2 * scale)))
        self.draw_wheels(body, scale)
        return body

    def draw_panel(self) -> None:
        self.service_buttons.clear()
        self.emergency_button = None
        panel = self.panel_rect()
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_EDGE, panel, 2, border_radius=8)

        x = panel.x + 18
        y = panel.y + 18
        draw_text_left(self.screen, self.title, "Route 66 Stop", (x, y), TEXT)
        y += 44

        car = self.current_car()
        city = CITY_STOPS.get(car.position)
        river = RIVER_CROSSINGS.get(car.position)
        service_kind = self.service_points.get(car.position)
        blocked = self.movement_block_reason(car)
        if self.die_roll is None:
            if self.turn_done:
                draw_text_left(self.screen, self.small, "Turn finished. Press Next for the next car.", (x, y), MUTED)
            elif blocked:
                draw_text_left(self.screen, self.small, blocked, (x, y), ERROR)
            else:
                draw_text_left(self.screen, self.small, "Press Go to roll 1-6 and choose a block.", (x, y), MUTED)
        else:
            draw_text_left(
                self.screen,
                self.small,
                f"Roll {self.die_roll} x speed {car.speed} = range {self.move_range}",
                (x, y),
                MUTED,
            )
        y += 36

        if city:
            draw_text_left(self.screen, self.panel_font, f"{car.position}. {city}", (x, y), TEXT)
            y += 30
            if car.position == CELL_COUNT:
                draw_text_left(self.screen, self.small, "Destination: finish the race here.", (x, y), MUTED)
                y += 34
            else:
                y = self.draw_city_services(panel, x, y)
        elif river:
            draw_text_left(self.screen, self.panel_font, f"{car.position}. {river}", (x, y), TEXT)
            y += 30
            draw_text_left(self.screen, self.small, "River crossing:", (x, y), TEXT)
            y += 24
            draw_text_left(self.screen, self.small, "You must stop here.", (x, y), MUTED)
            y += 22
            draw_text_left(self.screen, self.small, "Roll odd to leave.", (x, y), MUTED)
            y += 22
            draw_text_left(self.screen, self.small, "Even roll: stay, fuel/energy frozen.", (x, y), MUTED)
        else:
            stop_name = SERVICE_POINT_LABELS[service_kind] if service_kind else f"Block {car.position}"
            draw_text_left(self.screen, self.panel_font, f"{car.position}. {stop_name}", (x, y), TEXT)
            y += 30
            if service_kind:
                y = self.draw_service_point_services(panel, x, y, service_kind)
            else:
                draw_text_left(self.screen, self.small, "No service on this block.", (x, y), MUTED)
                y += 24
                draw_text_left(self.screen, self.small, "Move to a city or service stop.", (x, y), MUTED)

        msg_color = ERROR if self.message.startswith(("Not enough", "Cargo")) else MUTED
        draw_text_left(self.screen, self.small, self.message, (x, panel.bottom - 142), msg_color)
        self.draw_emergency_button()
        self.draw_history_button()
        self.draw_go_button()
        self.draw_new_game_button()

        y = panel.bottom - 152
        draw_text_left(self.screen, self.panel_font, "Controls", (x, y), TEXT)
        y += 28
        draw_text_left(self.screen, self.small, "Go: roll and show range", (x, y), MUTED)
        y += 22
        draw_text_left(self.screen, self.small, "Tow / Sleep / Pay when blocked", (x, y), MUTED)

    def draw_transaction_area(self, box: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, WHITE, box, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_EDGE, box, 1, border_radius=6)
        draw_text_left(self.screen, self.panel_font, "Transactions", (box.x + 10, box.y + 8), TEXT)
        line_y = box.y + 34
        for entry in self.transactions[-2:]:
            short = entry if len(entry) <= 36 else entry[:33] + "..."
            draw_text_left(self.screen, self.small, short, (box.x + 10, line_y), MUTED)
            line_y += 18

    def draw_service_button(self, rect: pygame.Rect, label: str, action: str, enabled: bool = True) -> None:
        color = BUTTON_ALT if enabled else BUTTON_DISABLED
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        draw_text(self.screen, self.small, label, rect.center, WHITE)
        if enabled:
            self.service_buttons.append((rect, action))

    def draw_city_services(self, panel: pygame.Rect, x: int, y: int) -> int:
        car = self.current_car()
        enabled = not self.move_options
        draw_text_left(self.screen, self.small, "Click a service:", (x, y), MUTED)
        y += 22

        rows = [
            ("Gas", [("Fill fuel", "fill_fuel"), ("Gas can", "gas_can"), ("Coffee", "coffee")]),
            ("Motel", [("Motel", "motel")]),
            (
                "Mechanic",
                [
                    ("Tire", "tire"),
                    ("Cap +2", "capacity"),
                    ("Tank +3", "fuel_tank"),
                    ("Speed +1", "speed"),
                ],
            ),
            ("Shop", [("Arm", "arm"), ("Buy coll", "collectible"), ("Sell coll", "sell_collectible")]),
            ("Work", [("1T +$40", "work_one"), ("2T +$100", "work_two"), ("3T +$150", "work_three")]),
        ]

        for title, actions in rows:
            draw_text_left(self.screen, self.small, title, (x, y), TEXT)
            y += 18
            button_x = x
            button_w = 88
            for label, action in actions:
                if button_x + button_w > panel.right - 18:
                    button_x = x
                    y += 34
                rect = pygame.Rect(button_x, y, button_w, 28)
                self.draw_service_button(rect, self.service_button_label(car.position, label, action), action, enabled)
                button_x += button_w + 7
            y += 38

        cargo = f"Cargo {self.cargo_used(car)}/{car.capacity}: tires {car.tires}, arms {car.arms}, cans {car.gas_cans}, coffee {car.coffee}, coll {car.collectibles}"
        draw_text_left(self.screen, self.small, cargo, (x, y), MUTED)
        return y + 22

    def draw_service_point_services(self, panel: pygame.Rect, x: int, y: int, service_kind: str) -> int:
        car = self.current_car()
        enabled = not self.move_options
        draw_text_left(self.screen, self.small, "Click a service:", (x, y), MUTED)
        y += 24
        service_actions = {
            "gas": [("Fill fuel", "fill_fuel"), ("Gas can", "gas_can"), ("Coffee", "coffee")],
            "mechanic": [("Tire", "tire"), ("Cap +2", "capacity"), ("Tank +3", "fuel_tank"), ("Speed +1", "speed")],
            "motel": [("Motel", "motel")],
        }
        button_x = x
        button_w = 88
        for label, action in service_actions[service_kind]:
            if button_x + button_w > panel.right - 18:
                button_x = x
                y += 34
            rect = pygame.Rect(button_x, y, button_w, 28)
            self.draw_service_button(rect, self.service_button_label(car.position, label, action), action, enabled)
            button_x += button_w + 7
        return y + 40

    def service_button_label(self, position: int, label: str, action: str) -> str:
        if action == "fill_fuel":
            return f"Fuel ${self.price_at(position, action)}"
        if action == "sell_collectible":
            sale = self.best_collectible_sale(self.current_car())
            return f"Sell ${sale[1]}" if sale else "Sell"
        if action in {"work_one", "work_two", "work_three"}:
            return label
        return f"{label} ${self.price_at(position, action)}"

    def draw_vehicle_info(self) -> None:
        car = self.current_car()
        rect = self.vehicle_info_rect()
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_EDGE, rect, 2, border_radius=8)

        self.draw_car_icon(car, (rect.x + 50, rect.y + 55), 0.86)

        x = rect.x + 96
        y = rect.y + 18
        driver = "Human" if self.is_human_turn() else "AI"
        draw_text_left(self.screen, self.title, f"Round {self.round_number}: {car.name} ({driver})", (x, y), TEXT)

        available_w = rect.right - x - 12
        tx_w = 200
        ranking_w = 150
        gap = 8
        left_w = max(150, (available_w - tx_w - ranking_w - gap * 3) // 2)
        stats_box = pygame.Rect(x, rect.y + 50, left_w, 42)
        inventory_box = pygame.Rect(stats_box.right + gap, rect.y + 50, left_w, 42)
        tx_box = pygame.Rect(inventory_box.right + gap, rect.y + 12, tx_w, 80)
        ranking_box = pygame.Rect(tx_box.right + gap, rect.y + 12, ranking_w, 80)

        self.draw_stat_box(
            stats_box,
            [
                (f"Block {car.position}", MUTED),
                (f"Spd {car.speed}", MUTED),
                (f"Max {car.max_move}", MUTED),
                (f"Fuel {car.fuel}/{car.fuel_tank}", ERROR if car.fuel < 3 else MUTED),
                (f"Use {car.fuel_cons}", MUTED),
                (f"Energy {car.energy}", ERROR if car.energy < 2 else MUTED),
                (f"Money ${car.money}", ERROR if car.money < 50 else MUTED),
                (f"Value {self.ai.values.get(self.ai.state_key(self, car), 0.0):+.1f}", MUTED),
            ],
        )
        self.draw_stat_box(
            inventory_box,
            [
                (f"Cargo {self.cargo_used(car)}/{car.capacity}", MUTED),
                (f"Tires {car.tires}", MUTED),
                (f"Arms {car.arms}", MUTED),
                (f"Cans {car.gas_cans}", MUTED),
                (f"Coffee {car.coffee}", MUTED),
                (f"Coll {car.collectibles}", MUTED),
            ],
        )
        self.draw_transaction_area(tx_box)
        self.draw_ranking_area(ranking_box)

    def draw_stat_box(self, box: pygame.Rect, stats: list[tuple[str, tuple[int, int, int]]]) -> None:
        pygame.draw.rect(self.screen, WHITE, box, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_EDGE, box, 1, border_radius=6)
        self.draw_inline_stats(stats, box.x + 8, box.y + 7, box.right - 8, line_height=17)

    def draw_ranking_area(self, box: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, WHITE, box, border_radius=6)
        pygame.draw.rect(self.screen, PANEL_EDGE, box, 1, border_radius=6)
        draw_text_left(self.screen, self.panel_font, "Ranking", (box.x + 10, box.y + 8), TEXT)
        y = box.y + 34
        for rank, (index, car) in enumerate(self.rankings(), start=1):
            color = TEXT if index == self.current_vehicle else MUTED
            driver = "H" if index == self.human_vehicle else "AI"
            short_name = {"Sports Car": "Sports"}.get(car.name, car.name)
            draw_text_left(self.screen, self.small, f"{rank}. {short_name} {car.position} ({driver})", (box.x + 10, y), color)
            y += 16

    def draw_inline_stats(
        self,
        stats: list[tuple[str, tuple[int, int, int]]],
        x: int,
        y: int,
        max_x: int,
        line_height: int = 20,
    ) -> None:
        current_x = x
        current_y = y
        for text, color in stats:
            width = self.small.size(text + "   ")[0]
            if current_x + width > max_x:
                current_x = x
                current_y += line_height
            draw_text_left(self.screen, self.small, text, (current_x, current_y), color)
            current_x += width

    def draw_emergency_button(self) -> None:
        car = self.current_car()
        rect = self.emergency_button_rect()
        action = self.emergency_action(car)
        enabled = action is not None and not self.move_options and not self.turn_done
        label = (
            "Wait" if action == "skip_wait"
            else "Pay" if action == "pay_ticket"
            else "Use Can" if action == "gas_can"
            else "Coffee" if action == "coffee"
            else "Sleep" if action == "sleep"
            else "Tow"
        )
        pygame.draw.rect(self.screen, ERROR if enabled else BUTTON_DISABLED, rect, border_radius=7)
        draw_text(self.screen, self.panel_font, label, rect.center, WHITE)
        if enabled:
            self.emergency_button = (rect, action)

    def draw_history_button(self) -> None:
        rect = self.history_button_rect()
        self.history_button = rect
        pygame.draw.rect(self.screen, BUTTON_ALT, rect, border_radius=7)
        draw_text(self.screen, self.small, "History", rect.center, WHITE)

    def draw_new_game_button(self) -> None:
        rect = self.new_game_button_rect()
        self.new_game_button = rect
        pygame.draw.rect(self.screen, BUTTON_ALT, rect, border_radius=7)
        draw_text(self.screen, self.panel_font, "New Game", rect.center, WHITE)

    def draw_go_button(self) -> None:
        rect = self.go_button_rect()
        car = self.current_car()
        enabled = not self.move_options and (self.turn_done or self.movement_block_reason(car) is None)
        label = "Next" if self.turn_done else "Go"
        pygame.draw.rect(self.screen, BUTTON if enabled else BUTTON_DISABLED, rect, border_radius=7)
        draw_text(self.screen, self.panel_font, label, rect.center, WHITE)

    def draw_popup(self) -> None:
        if not self.popup_title and not self.show_history:
            return

        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))

        modal = pygame.Rect(0, 0, min(560, width - 120), min(360, height - 120))
        modal.center = (width // 2, height // 2)
        pygame.draw.rect(self.screen, PANEL, modal, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_EDGE, modal, 2, border_radius=8)

        x = modal.x + 24
        y = modal.y + 22
        title = "Transaction History" if self.show_history else self.popup_title or ""
        draw_text_left(self.screen, self.title, title, (x, y), TEXT)
        y += 46

        if self.show_history:
            entries = self.transactions[-12:]
            for entry in entries:
                short = entry if len(entry) <= 64 else entry[:61] + "..."
                draw_text_left(self.screen, self.small, short, (x, y), MUTED)
                y += 20
            draw_text_left(self.screen, self.small, "Game over exports history automatically. Esc/OK closes.", (x, modal.bottom - 76), MUTED)
        else:
            for line in self.popup_lines:
                draw_text_left(self.screen, self.panel_font, line, (x, y), TEXT)
                y += 28

        ok = self.popup_ok_rect()
        pygame.draw.rect(self.screen, BUTTON, ok, border_radius=7)
        draw_text(self.screen, self.panel_font, "OK", ok.center, WHITE)

    def update_ai_turn(self) -> None:
        if self.game_state != "play" or self.is_human_turn() or self.popup_title or self.show_history or self.winner:
            return
        now = pygame.time.get_ticks()
        if now < self.ai_next_action_at:
            return
        if self.ai.take_turn(self):
            self.ai_next_action_at = now + 650

    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.game_state == "select":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                        self.setup_new_game()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for idx, rect in enumerate(self.selection_card_rects()):
                            if rect.collidepoint(event.pos):
                                self.select_vehicle(idx)
                                break
                    continue
                if event.type == pygame.KEYDOWN:
                    if self.popup_title or self.show_history:
                        if event.key == pygame.K_ESCAPE:
                            self.show_history = False
                            self.close_popup()
                        continue
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_h:
                        self.show_history = True
                    if event.key == pygame.K_SPACE and not self.move_options and self.is_human_turn():
                        self.roll_for_current_car()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.popup_title or self.show_history:
                        if self.popup_ok_rect().collidepoint(event.pos):
                            self.show_history = False
                            self.close_popup()
                        continue
                    if not self.is_human_turn():
                        continue
                    service_clicked = False
                    for rect, action in self.service_buttons:
                        if rect.collidepoint(event.pos):
                            self.use_city_service(action)
                            service_clicked = True
                            break
                    if service_clicked:
                        continue
                    if self.history_button and self.history_button.collidepoint(event.pos):
                        if self.winner:
                            self.export_history()
                        self.show_history = True
                        continue
                    if self.new_game_button and self.new_game_button.collidepoint(event.pos):
                        self.setup_new_game()
                        continue
                    if self.emergency_button and self.emergency_button[0].collidepoint(event.pos):
                        if self.emergency_button[1] == "tow":
                            self.tow_current_car()
                        elif self.emergency_button[1] == "gas_can":
                            self.use_gas_can_current_car()
                        elif self.emergency_button[1] == "sleep":
                            self.sleep_current_car()
                        elif self.emergency_button[1] == "coffee":
                            self.drink_coffee_current_car()
                        elif self.emergency_button[1] == "pay_ticket":
                            self.pay_ticket_current_car()
                        elif self.emergency_button[1] == "skip_wait":
                            self.roll_for_current_car()
                        continue
                    if self.go_button_rect().collidepoint(event.pos):
                        if not self.move_options:
                            self.roll_for_current_car()
                    else:
                        clicked = self.cell_at(event.pos)
                        if clicked in self.move_options:
                            self.finish_move(clicked)
            self.update_ai_turn()
            self.draw()


if __name__ == "__main__":
    Route66Board().run()
