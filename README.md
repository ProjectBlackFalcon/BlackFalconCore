# BlackFalconCore

### The core of the black falcon bot project.

This repository is the central intelligence of the bot swarm. 

It's main role is to provide a high level API (the swarm node) to interact with the bots.

It schedules and runs the bots, routes strategies and reports, manages configurations, and handles data streams and batches.

## Get started

Requires Python 3.7
[Install guide for Ubuntu, Debian, and Mint here](https://tecadmin.net/install-python-3-7-on-ubuntu-linuxmint/)

#### The easy way
We have a swarm node running 24/7 (or so we try), you can ask us to use it if you want to, we're cool with that. We'll send you a credentials file for you to play around with botting.

#### The hard way
 1. Get the latest BlackFalconAPI, it is updated every tuesday.
 2. Ensure you have access to the bot assets. You have two options for this:
     - Directly request a credentials file from us to access the assets database (we're also cool with that)
     - [Setup your own assets database](https://github.com/ProjectBlackFalcon/AssetsManager/blob/master/README.md)
 3. Clone this repo where you want to run the swarm node: `git clone https://github.com/ProjectBlackFalcon/BlackFalconCore.git`
 4. Move your credentials file to the root directory `mv path/to/credentials.json BlackFalconCore/`
 5. Start the swarm node: `cd BlackFalconCore; python3.7 swarm_node/swarm_node.py`. Once it has downloaded and loaded the assets files, you should see `Listening on port 8721 for clients..` which means the swarm node started successfully.
 
 #### Using the swarm node
 Once the node is running, you can connect with your favorite websocket client and issue commands to the bot swarm.
 
 Or, because we're nice like that, you can use the GUI client we made. You'll find it at GUI/manual_strat.py. Beware though, it is very much shit and pretty buggy.


## The architecture

### Architecture goals
 - We should be able to distribute bots on multiple hosts
 - Bots should be able to interact with each other in game
 - Each bot should be as slim as possible in terms of performance footprint (RAM, CPU)
 - Limit the complexity of the architecture as much as possible

![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/80fac944fa2a6132451858f407883080/Archi.drawio.svg)


### Swarm API 
Provides a single language agnostic acces point to the swarm. This will typically be used to issue high level commands or fetch data about the swarm.

[The queries to execute strategies are documented here](https://github.com/ProjectBlackFalcon/BlackFalconCore/blob/master/strategies/strategies.md)

### Swarm manager
The swarm manager is a cluster-wide scheduler, load balancer, and reverse proxy. Its role is to spawn swarm nodes, assign them new bots, route requests, and hold a cartography.

### Swarm node
Each node is localized on a physical host and its responsibility is to spawn clients and forward orders coming from the swarm manager to the appropriate one. The common assets for all the bots are also loaded there at the host level. It means these are common for all the bot instances (clients) on this node, which greatly reduces the memory footprint, allowing us to run more bots on the same machine. It also holds a local cartography.

This is going to be as slim as possible, essentially only forwarding messages with.

It exposes an API using JSON over websocket to provide a high level entry point to use the bots.

### Intelligence bricks
These are going to be modules which implement bot behaviour. For example, the `core` brick will implement movements, connection / disconnection, interactions with activables and NPC. The `harvester` brick will implement all the logic for harvesting resources and will depend on the `core` brick.

### Static assets
Read only assets which only need to be loaded once. This includes maps, items, etc.

### Dynamic assets
Assets that may be updated by a bot as it does its thing. This includes bot information, treasure hunt clues, known paths, etc.

### Clients 
The clients embark most of the processing. They take orders from their parent swarm node and translate them into a series of commands the BlackFalconAPI can digest.

The clients use these components:
- The commander: spawns and controls the listener, the BlackFaclonAPI, and its connector. It also manages executors. The commander is the point of contact of the swarm node and abstracts the underlying components (listener, connector, API, executors)
- The listener: maintains the game state, which is basically everything from the point of view of the bot. This game state is the source of truth about the bot's environnement. The listener recieves all the data the API sends it and updates the game state with it. The listener is a daemon that lives and dies with the controller
- The BlackFalconAPI and its connector: the BlackFalconAPI is the client's interface with the game. As it is interacted with via JSON over websocket, we need a connector to plug it in. They are both daemons that live and die with the commander.
- Executors: transient functions that implement strategies. Executors are blocking and executed sequentially by the commander. They always return whether or not they suceeded, failed, or crashed, and may (should) return info on why.

### Bot API (BlackFalconAPI)
Uses JSON over websocket. This is the translator between the game and the rest of the code. It parses the data packets from the game to JSON and vice-versa.

### Bot
The actual bot in-game.

## The chain of command

We need to define the way we want to give orders to bots. We want to be able to:
 - Issue arbitrarily high level commands such a 'goto', 'craft', 'chat', or even 'play'...
 - Be able to closely follow the execution of these commands through the thorough validation of each atomic order.
 
 ### Block diagram detailing the chain of command
 
 ![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/283c0b53b7cdd34006c7a59616c74ae0/Command_chain.drawio.svg)
 
 It is very clear here that the Swarm Manager and the Swarm Node are only routing the command to the proper client.
 
 We implement two levels of command: 
 - Strategy: highest level of command. Strategies are human-oriented. Example of strategies are 'harvest fish', 'collect data', 'chat with people', 'craft items'... Strategies come with parameters, for example a goto will require target coordinates. Strategies can be dependant on each others, for example, a bot that harvests resources has to be able to make gotos, which are defined by a strategy.
 - Order: lowest level of command. This is what the bot API accepts as an input. An order always has an expected result (i.e. an alteration of the game state).
 
 ### Concurrency diagram of the chain of command
 
 ![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/5fa00ecb568338003000ae87a334320c/Comman_concurrency_diagram.drawio.svg)
 
 Note: the API actually continuously streams data to the Listener, not only after an order is issued, I just can't do UML and don't know how to represent that.