# Route 66 — Road Trip Strategy Game

Route 66 is a turn-based resource-management race from Chicago to Santa Monica. Players choose vehicles with different strengths, then balance speed against fuel, energy, money, cargo, repairs, and roadside risk across a 66-space route.

The fastest vehicle is not automatically the best. Moving aggressively increases exposure to tickets, tire failures, towing, and resource shortages, while conservative players can work, trade collectibles, rest, and upgrade their vehicles for a safer late game.

## Gameplay features

- **Five asymmetric vehicles:** Sedan, RV, Pickup, Sports Car, and Motorcycle each trade off speed, range, capacity, and resilience.
- **Resource planning:** manage fuel, energy, cash, spare tires, gas cans, coffee, and cargo.
- **A changing route:** gas stations, motels, mechanics, and casinos are randomized between fixed cities and river crossings.
- **Risk and recovery:** speeding tickets, tire failures, towing, debt, and forced rest can reshape the race.
- **Local economy:** work in major cities, gamble, or carry collectibles west and sell them for distance-based profit.
- **Human and autonomous drivers:** select any vehicles for human control; the rest are driven by rule-based agents.
- **History export:** the game records decisions and events for replay and balance analysis.

## Quick start

### Requirements

- Python 3.10+
- Pygame

```bash
git clone https://github.com/patrick528300/Route66game.git
cd Route66game
python3 -m pip install pygame
python3 route66game.py
```

On the opening screen, select one or more human-controlled vehicles. Unselected vehicles become AI drivers.

### Controls

- Click a vehicle card to toggle human control.
- Press **Space** or click **Roll** to begin a human turn.
- Click a highlighted road cell to choose a destination.
- Use the service panel for fuel, lodging, repairs, purchases, work, upgrades, or gambling.
- Press **H** to view history and **N** to start a new game.
- Press **Esc** to close a popup or exit.

## The strategic loop

1. Roll for movement range and choose how far to travel.
2. Spend fuel and energy while evaluating the next reliable service stop.
3. Decide whether to push forward, detour, rest, work, trade, or upgrade.
4. Recover from tickets, breakdowns, river delays, debt, and resource shortages.
5. Reach space 66 — Santa Monica — before the other drivers.

## Vehicle trade-offs

| Vehicle | Strength | Main constraint |
| --- | --- | --- |
| Sedan | Balanced and economical | No special ability |
| RV | Large tank; restores energy when sleeping roadside | High fuel consumption |
| Pickup | Highest cargo capacity | High fuel consumption |
| Sports Car | Fastest road movement | Small tank and cargo capacity |
| Motorcycle | Can crawl forward without fuel or with a flat tire | Very small tank and capacity |

## Engineering highlights

- Encapsulates vehicle state with a Python data class and centralizes rule enforcement in `Route66Board`.
- Models fixed cities and river crossings alongside procedurally placed service points.
- Handles dependent state transitions for movement, fuel use, fatigue, debt, towing, repair, upgrades, cargo, and random hazards.
- Keeps autonomous-driver decisions in a separate `Route66AI` module while exposing the same legal board actions used by human players.
- Uses compact state keys and observed rewards to retain decision values during a run, combined with explicit survival-risk estimates.
- Exports a human-readable event history for debugging and playtest review.

## Project structure

| File | Purpose |
| --- | --- |
| `route66game.py` | Pygame UI, vehicle model, board state, and game rules |
| `route66_ai.py` | Autonomous driver, survival-risk evaluation, and action selection |
| `route66_points.json` | Route and display point data |
| `route66gamerule.txt` | Detailed rules reference |
| `route66_history.txt` | Example exported play history |

## Design and development

I originally designed Route 66 as a tabletop-style road-trip game, including the vehicle classes, route economy, service distribution, emergencies, and balancing. I later directed its translation into a playable software system, specifying executable behavior, testing edge cases, and iterating on game balance.

The project is intentionally presented as a game and simulation engineering project—not as an AI product. Its strongest technical problem is maintaining consistent behavior while many resources and recovery rules interact during the same turn.

## Roadmap

- Separate the game engine from Pygame rendering
- Add deterministic random seeds and save/load support
- Add automated tests for towing, debt, emergencies, and service placement
- Add a short tutorial and clearer in-game rule explanations
- Collect playtest statistics to compare vehicle balance and agent behavior
