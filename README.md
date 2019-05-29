# BlackFalconCore

### The core of the black falcon bot project.

This repository is the central intelligence of the bot swarm. 

It's role is to schedule and run the bots, handle intelligence bricks, manage configurations, handle data streams and batches, and provide a high level REST API to interact with the swarm.

## The architecture

### Architecture goals
 - We should be able to distribute bots on multiple hosts
 - Bots should be able to interact with each other in game
 - Each bot should be as slim as possible in terms of performance footprint (RAM, CPU)
 - Limit the complexity of the architecture as much as possible

![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/80fac944fa2a6132451858f407883080/Archi.drawio.svg)


### Swarm API 
Provides a single language agnostic acces point to the swarm. This will typically be used to issue high level commands or fetch data about the swarm.

Querying is going to be REST or GraphQL

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
The clients embark most of the processing. They take orders from their parent swarm node and translate them into a series of commands edible by the low level API.

They embark three main components:
- The processor: transforms json orders into a plan to be executed by the commander
- The commander: spawns and sends orders to the API.
- The listener: holds the game state, which is basically everything from the point of view of the bot. This game state is the source of truth about the bot's environnement. The listener recieves all the data the API sends it and updates the game state with it.

### Bot API
Uses JSON over websocket. This is the translator between the game and the rest of the code. It parses the data packets from the game to JSON and vice-versa.

### Bot
The actual bot in-game.

## The chain of command

We need to define the way we want to give orders to bots. We want to be able to:
 - Issue arbitrarily high level commands such a 'goto', 'craft', 'chat', or even 'play'...
 - Be able to closely follow the execution of these commands through the thorough validation of each atomic order.
 
 ### Block diagram detailing the chain of command
 
 ![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/cac93370d5ab8d48efff3cfe0e1a6000/Command_chain.drawio.svg)
 
 It is very clear here that the Swarm Manager and the Swarm Node are only routing the command to the proper client.
 
 We implement several levels of command: 
 - Strategy: highest level of command. Strategies are human-oriented. Example of strategies are 'harvest fish', 'collect data', 'chat with people', 'craft items'...
 - Tactic: a strategy broken down into a list of successive atomic orders associated with an expected result.
 - Order: the lowest level a command. This is what the bot API accepts as an input. An order always have an expected result (an alteration of the game state).
 
 ### Concurrency diagram of the chain of command
 
 ![lel](https://trello-attachments.s3.amazonaws.com/5ce57f181041ba0b5ae4c693/5ce962d91c07d78f9cb266b7/9fe111b8bc92ec4246e22a0b8b1316d8/Comman_concurrency_diagram.drawio.svg)
 
 Note: the API actually continuously streams data to the Listener, not only after an order is issued, I just can't do UML and don't know how to represent that.