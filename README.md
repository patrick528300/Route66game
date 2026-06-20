**To play the game, run python3 route66game.py**


Overview of the game and goal
There will be four players. Each player chooses a vehicle (sedan, RV, pickup, and sports car) and races from Chicago to Los Angeles. Whoever first reached Santa Monica wins the game.
Setup:
At the beginning, each player chooses a type of vehicle, and will be given 300 dollars. They will use that money to put on gas, book motels, deal with emergencies, or upgrade their vehicles. Each player also has energy points 3, with fuel = full, tire = 1 (but capacity - 1). In case the money runs out, players can choose to either work at big cities by sacrificing turns, buy collectibles in a city and sell them to another city, or gamble at casinos. 
Different types of cars :
Sedan. Speed = 1, capacity = 3, fuel tank = 5, fuel cons: 1, energy = 3. Specialist: None.
RV. Speed = 1 (maximum move per turn = 5) , capacity = 4, fuel tank = 20, fuel cons: 4. Energy = 3. Specialist: energy restores to 2 when sleeping at roadside. 
Pickup. Speed = 1, capacity = 5, fuel tank = 15, fuel cons: 3, energy = 3. Specialist: bigger capacity. 
Sports car. Speed = 2 (maximum move per turn = 10), capacity = 2, fuel tank = 5, fuel cons: 2, energy = 3. Specialist: moving fast. 
Different places: 
Big cities (Chicago, St. Louis, Oklahoma City, Armarillo, Santa Fe, Flagstaff, Barstow, Pasadena), where you can have all services: put on gas, motel / sleeping, repair / upgrade car, buy tire / arm / gas can / coffee, buy or sell collectibles. Players can work to earn money – each turn players earn $50. Big cities do not have casinos. 
Gas Station - put on gas, buy gas can, buy coffee. 
Mechanics - repair / upgrade car, buy tires
Motel - sleeping, so the player can restore energy to 3. 
Casino - win or lose money. Put 50 dollars in, and roll a dice. If dice > 4, win 200 dollars, otherwise lose $50. 
River Crossing - East St. Louis (Mississippi River Crossing), Needles (Colorado River Crossing). Roll a dice and if the result is odd, then the vehicle can cross the river and move, otherwise the vehicle has to wait, but gas and energy freeze while waiting. 
Destination - Santa Monica

Placing services on the map: gas stations, mechanics, motels, and casinos will be randomly placed on blocks other than big cities or river crossings, and on the same block, there can be more than 1 service. Amount: gas station 10, motel 6, mechanic 5, casino 5

Resources: 
Gas. spend fuel every turn to roll a dice so the vehicle moves
Tires. Used when a tire blows off. Otherwise the vehicle will be towed to nearest mechanics (and the mechanics cannot be the other side of Mississippi River or Colorado River) 
Coffee. Used when energy = 0. Ignore energy = 0 for 1 turn (can still move). Must rest before drinking coffee again. 
Collectible. Buy in a city, deliver it to other cities and sell it for profit. 

Running the game
Roll a dice and multiply the dice result by speed, clipped by the maximum move, then the player knows the range they’re able to move in this turn. Then players can move vehicles to any block within the range forward or backward. 
In every turn the energy will be reduced by 1. Players have to stay in a motel to restore the energy to be 3. 

In each turn fuel is dropped by the fuel comp. If the fuel tank < fuel, then the vehicle cannot move. The vehicle will be towed to the nearest gas station (not including the ones on the other bank of Mississippi River or Colorado River).  Players have to stop by at gas stations to put on gas. If the vehicles have gas cans, consume the gas can and each gas can provides 2 fuel, so the vehicle can move again. 

If the energy is dropped to 0, players can drink coffee to continue looking for a motel. If players do not have coffee, or they have consumed coffee, then they had to stop moving for 1 round (so they could sleep), and energy would be raised to 1. RV gets energy +2 if RV sleeps on the road. Whenever a player stops at a casino, the energy becomes 2. 

If the players actually move >= 5 blocks, toss a dice. If the result is 1 or 2, then the player gets a ticket of $100 that must be paid next turn before moving the vehicle. If the result is 3 or 4, a tire blows off and a spare tire should be consumed; otherwise the vehicle will be towed to the nearest mechanic (not including the ones on the other bank of Mississippi River or Colorado River). (ticket is $100, and towing is $70). The player does not need to buy a tire at the mechanic – the vehicle can move next turn. 

If a player gets debts (money < 0), they can still move or spend money if they are not in a big city, but they cannot pass through nearby big cities. They have to work long enough to get their money > 0, otherwise they cannot leave the big city or spend money any more. Players earn $50 each turn when they stay to work in a city. 

Players can choose to stay in a town to work. Each turn they stay in a big city, they can earn 50 dollars. 

Things that take a turn:’
Move
Car under upgraded 
Work 
Things that can be done after moving and do not take a turn:
Buy stuff (coffee, …)
Stay at a motel
Put on gas
Gamble (at a casino) 


Upgrade Car: go to a mechanic, spend money, and wait to be repaired
Capacity + 2. Waiting time: 1 turn. Bill: $50. Consequence: fuel consumption + 1
Fuel tank + 3. Waiting time: 1 turn. Bill: $50. Consequence: fuel consumption + 1
Speed + 1. Waiting time: 2 turns. Bill: $100, Consequence: fuel consumption +1

