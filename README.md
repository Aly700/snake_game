# Networked Snake Game

Welcome to Networked Snake Game, implemented 
in Python using a server-client architecture. This game allows multiple 
players to connect to a central server to play the game, making it a fun 
and interactive experience.

## Features

- Multiplayer gameplay through network communication.
- Server handles all game logic and updates.
- Simple and intuitive client interface for player interactions.

## Prerequisites

Before you run the game, ensure you have Python 3.x installed on your 
machine. The game was developed using Python 3.8, but it should work with 
any Python 3.x version.

## Installation Instructions

Follow these steps to get the game running on your local machine:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Aly700/snake_game.git

2. **Install Dependencies**  
   Install the necessary Python libraries:
   ```bash
   pip install pygame rsa

## Running the Game

### Server
Start the game server first. It will listen for incoming client connections and manage the game state:

   ```bash
   python snake_server.py
   ```

## Client
Once the server is running, you can start the client(s) on the same or different machines:

```bash
python snake_client.py
```

Open multiple terminals and run the client script in each to simulate multiple players.






