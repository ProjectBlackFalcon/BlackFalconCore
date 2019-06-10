import json

import pymongo

from credentials import credentials


def cell2coord(cell):
    return cell % 14 + int((cell // 14) / 2 + 0.5), (13 - cell % 14 + int((cell // 14) / 2))


def distance_coords(coord_1, coord_2):
    return ((coord_2[0] - coord_1[0]) ** 2 + (coord_2[1] - coord_1[1]) ** 2) ** 0.5


def distance_cell(cell_1, cell_2):
    return distance_coords(cell2coord(cell_1), cell2coord(cell_2))


def coord_fetch_map(map_info, coord, worldmap):
    maps = []
    for map in map_info:
        if map['coord'] == coord and map['worldMap'] == worldmap:
            maps.append(map)
    if len(maps) == 1 and maps[0] is not None:
        return maps[0]['cells']
    elif len(maps) > 1:
        for map in maps:
            if map['hasPriorityOnWorldMap']:
                return map['cells']


def flatten_map(map):
    flattened = []
    for line in map:
        flattened += line
    return flattened


def get_neighbour_cells(cell):
    neighbours = []
    for i in range(560):
        if distance_cell(cell, i) == 1:
            neighbours.append(i)
    return neighbours[:]


def get_walkable_neighbour_cells(map_info, cell, map_coords, worldmap):
    walkable_neighbours = []
    for neighbour in get_neighbour_cells(cell):
        if flatten_map(coord_fetch_map(map_info, '{};{}'.format(map_coords[0], map_coords[1]), worldmap))[neighbour] == 0:
            walkable_neighbours.append(neighbour)
    return walkable_neighbours[:]


def get_closest_walkable_neighbour_cell(map_info, target_cell, player_cell, map_coords, worldmap):
    walkable_neighbours = get_walkable_neighbour_cells(map_info, target_cell, map_coords, worldmap)
    if walkable_neighbours:
        closest = walkable_neighbours[0], 10000
    else:
        return False
    for walkable_neighbour in walkable_neighbours:
        if distance_cell(walkable_neighbour, player_cell) < closest[1]:
            closest = walkable_neighbour, distance_cell(walkable_neighbour, player_cell)

    if closest[1] < 10000:
        return closest[0]
    return False


def mongo_client():
    return pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password']
    )


def get_profile(bot, assets):
    client = mongo_client()

    profile = client.blackfalcon.bots.find_one({'name': bot['name']})
    if profile is None:
        profile = json.loads(json.dumps(assets['blank_bot_profile']))
        profile['name'] = bot['name']
        profile['username'] = bot['username']
        profile['password'] = bot['password']
        profile['server'] = bot['server']
        client.blackfalcon.bots.insert_one(profile)
    return profile


def update_profile(bot_name, new_profile):
    client = mongo_client()
    client.blackfalcon.bots.find_one_and_replace({'name': bot_name}, new_profile)


def get_known_zaaps(bot_name):
    client = mongo_client()
    return client.blackfalcon.bots.find_one({'name': bot_name})['known_zaaps']


def get_closest_known_zaap(bot_name, pos):
    known_zaaps = get_known_zaaps(bot_name)
    closest = None, 100000
    for zaap_pos in known_zaaps:
        if distance_coords(pos, zaap_pos) < closest[1]:
            closest = zaap_pos, distance_coords(pos, zaap_pos)
    return tuple(closest[0]) if closest is not None else None
