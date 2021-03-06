import hashlib
import json
import random
import uuid

import numpy as np
from heapq import *
import time
import itertools
import sys

import pymongo
import psycopg2

from credentials import credentials


def cell2coord(cell):
    return cell % 14 + int((cell // 14) / 2 + 0.5), (13 - cell % 14 + int((cell // 14) / 2))


def dist(coord_1, coord_2):
    return ((coord_2[0] - coord_1[0]) ** 2 + (coord_2[1] - coord_1[1]) ** 2) ** 0.5


def distance_cell(cell_1, cell_2):
    return dist(cell2coord(cell_1), cell2coord(cell_2))


def fetch_map_cells(map_info, coord, worldmap):
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
        if flatten_map(fetch_map_cells(map_info, '{};{}'.format(map_coords[0], map_coords[1]), worldmap))[neighbour] == 0:
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


def get_closest_reachable_cell(map_info, target_cell, player_cell, map_coords, worldmap):
    cells = fetch_map_cells(map_info, '{};{}'.format(map_coords[0], map_coords[1]), worldmap)
    cells_vector = [item for sublist in cells for item in sublist]

    reachable_cells = []
    for cell, cell_type in enumerate(cells_vector):
        if cell_type not in [-1, 1, 2] and can_walk_to_node(cells_2_map(cells), player_cell, {'cell': cell}):
            reachable_cells.append(cell)

    closest, distance = [], distance_cell(reachable_cells[0], target_cell)
    for cell in reachable_cells:
        if 0 < distance_cell(cell, target_cell):
            if distance_cell(cell, target_cell) < distance:
                closest, distance = [cell], distance_cell(cell, target_cell)
            elif distance_cell(cell, target_cell) == distance:
                closest.append(cell)

    closest_to_player, distance = closest[0], sys.maxsize
    for cell in closest:
        if distance_cell(cell, player_cell) < distance:
            closest_to_player, distance = cell, distance_cell(cell, player_cell)

    return closest_to_player


def mongo_client():
    return pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password'],
    )


def create_profile(id, bot_name, username, password, server):
    if mongo_client().blackfalcon.bots.find_one({'name': bot_name}) is not None:
        raise Exception('Bot already exists. Delete it using the \'delete_bot\' command first.')
    profile = {
        'id': id,
        'name': bot_name,
        'username': username,
        'password': password,
        'server': server,
        'known_zaaps': [],
        'sub_end': 0,
        'position': (69, 420),
        'cell': 0,
        'worldmap': 1,
        'banned': False,
        'stuff': {},
        'stats': {},
    }
    mongo_client().blackfalcon.bots.insert_one(profile)


def delete_profile(bot_name):
    mongo_client().blackfalcon.bots.delete_one({'name': bot_name})


def get_profile(bot_name, client=None):
    if client is None:
        client = mongo_client()
    profile = client.blackfalcon.bots.find_one({'name': bot_name})
    if profile is None:
        raise Exception('Bot does not exist. Create a profile using the \'new_bot\' command first.')
    return profile


def update_profile_full(bot_name, new_profile, client=None):
    if client is None:
        client = mongo_client()
    client.blackfalcon.bots.replace_one({'name': bot_name}, new_profile)


def update_profile(bot_name, key, new_value):
    client = mongo_client()
    profile = get_profile(bot_name, client=client)
    profile[key] = new_value
    update_profile_full(bot_name, profile, client=client)


def get_account(username, client=None):
    if client is None:
        client = mongo_client()
    account = client.blackfalcon.account.find_one({'username': username})
    if account is None:
        raise Exception('Account does not exist.')
    return account


def update_account_full(username, new_account, client=None):
    if client is None:
        client = mongo_client()
    client.blackfalcon.account.replace_one({'username': username}, new_account)


def update_account(username, key, new_value):
    client = mongo_client()
    account = get_account(username, client=client)
    account[key] = new_value
    update_account_full(username, account, client=client)


def get_known_zaaps(bot_name):
    client = mongo_client()
    return client.blackfalcon.bots.find_one({'name': bot_name})['known_zaaps']


def add_known_zaap(bot_name, pos: list):
    if type(pos) is not list:
        raise TypeError('Positions must be lists')
    profile = get_profile(bot_name)
    if pos not in profile['known_zaaps']:
        profile['known_zaaps'].append(pos)
        update_profile_full(bot_name, profile)


def get_closest_known_zaap(bot_name, pos):
    known_zaaps = get_known_zaaps(bot_name)
    closest = None, 100000
    for zaap_pos in known_zaaps:
        if dist(pos, zaap_pos) < closest[1]:
            closest = zaap_pos, dist(pos, zaap_pos)
    return tuple(closest[0]) if closest[0] is not None else None


def heuristic(node1, node2):
    coords_1 = [int(coord) for coord in node1['coord'].split(';')]
    coords_2 = [int(coord) for coord in node2['coord'].split(';')]
    return dist(coords_1, coords_2)


def get_path_nodes(graph, start_node_id, end_node_id):
    close_set = set()
    came_from = {}
    gscore = {start_node_id: 0}
    fscore = {start_node_id: heuristic(graph[start_node_id], graph[end_node_id])}
    oheap = []

    heappush(oheap, (fscore[start_node_id], start_node_id))

    while oheap:

        current = heappop(oheap)[1]

        if current == end_node_id:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            path = []
            coords = ''
            for node_id in data:
                if graph[node_id]['coord'] != coords:
                    path.append({'coord': graph[node_id]['coord'], 'cell': random.choice(graph[node_id]['edge']), 'direction': graph[node_id]['direction']})
                    coords = graph[node_id]['coord']

            path.append({'coord': graph[start_node_id]['coord'], 'cell': graph[start_node_id]['cell'], 'direction': graph[start_node_id]['direction']})
            return list(reversed(path[1:]))

        close_set.add(current)
        neighbours = graph[current]['neighbours']
        for neighbour in neighbours:
            tentative_g_score = gscore[current] + heuristic(graph[current], graph[neighbour])

            if neighbour in close_set and tentative_g_score >= gscore.get(neighbour, 0):
                continue

            if tentative_g_score < gscore.get(neighbour, 0) or neighbour not in [i[1] for i in oheap]:
                came_from[neighbour] = current
                gscore[neighbour] = tentative_g_score
                fscore[neighbour] = tentative_g_score + heuristic(graph[neighbour], graph[end_node_id])
                heappush(oheap, (fscore[neighbour], neighbour))

    return False


def fetch_map(map_info, coord, worldmap):
    maps = []
    for map in map_info:
        if map['coord'] == coord and map['worldMap'] == worldmap:
            maps.append(map)
    if len(maps) == 1 and maps[0] is not None:
        return maps[0]
    elif len(maps) > 1:
        for map in maps:
            if map['hasPriorityOnWorldMap']:
                return map


def map_id_2_coord(map_info, map_id):
    for map in map_info:
        if int(map['id']) == map_id:
            return [int(coord) for coord in map['coord'].split(';')]
    raise Exception('Map id {} not in map info'.format(map_id))


def get_worldmap(map_info, map_id):
    for map in map_info:
        if int(map['id']) == map_id:
            return map['worldMap']
    raise Exception('Map id {} not in map info'.format(map_id))


def cells_2_map(cells):
    maps = np.array(cells)
    shape = maps.shape
    flattened = maps.flatten()
    new_base = np.zeros((14 * shape[1] // 14 + 20 * shape[0] // 40 - 1, 14 * shape[1] // 14 + 20 * shape[0] // 40))
    new_base[new_base == 0] = -1
    for i in range(len(flattened)):
        coord = i % shape[1] + int((i // shape[1]) / 2 + 0.5), (shape[1] - 1 - i % shape[1] + int((i // shape[1]) / 2))
        new_base[coord[1]][coord[0]] = flattened[i]
    return new_base[:]


def cell_2_coord(cell):
    return (14 - 1 - cell % 14 + int((cell // 14) / 2)), cell % 14 + int((cell // 14) / 2 + 0.5)


def can_walk_to_node(map, cell, node):
    start_pos = cell_2_coord(cell)
    goal_pos = cell_2_coord(node['cell'])

    neighbors = [(1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (0, 1), (-1, 0), (0, -1)]

    close_set = set()
    came_from = {}
    gscore = {start_pos: 0}
    fscore = {start_pos: (goal_pos[0] - start_pos[0]) ** 2 + (goal_pos[1] - start_pos[1]) ** 2}
    oheap = []

    heappush(oheap, (fscore[start_pos], start_pos))

    while oheap:

        current = heappop(oheap)[1]

        if current == goal_pos:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            return True

        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            tentative_g_score = gscore[current] + (neighbor[0] - current[0]) ** 2 + (neighbor[1] - current[1]) ** 2
            if 0 <= neighbor[0] < map.shape[0]:
                if 0 <= neighbor[1] < map.shape[1]:
                    if map[neighbor[0]][neighbor[1]] in [-1, 1, 2]:
                        continue
                else:
                    # array bound y walls
                    continue
            else:
                # array bound x walls
                continue

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + (goal_pos[0] - neighbor[0]) ** 2 + (goal_pos[1] - neighbor[1]) ** 2
                heappush(oheap, (fscore[neighbor], neighbor))

    return False


def get_path(map_info, graph, start_pos: tuple, end_pos: tuple, start_cell=None, end_cell=None, worldmap=1):
    start = time.time()
    potential_start_nodes_ids = []
    potential_end_nodes_ids = []
    start_cell_set = False if start_cell is None else True
    end_cell_set = False if end_cell is None else True
    for key, node in graph.items():
        if node['coord'] == '{};{}'.format(start_pos[0], start_pos[1]) and node['worldmap'] == worldmap:
            tmp_start_cell = node['cell'] if start_cell_set is False else start_cell
            cells = fetch_map(map_info, node['coord'], worldmap)['cells']
            if can_walk_to_node(cells_2_map(cells), tmp_start_cell, node):
                potential_start_nodes_ids.append(key)
        if node['coord'] == '{};{}'.format(end_pos[0], end_pos[1]) and node['worldmap'] == worldmap:
            tmp_end_cell = node['cell'] if end_cell_set is False else end_cell
            cells = fetch_map(map_info, node['coord'], worldmap)['cells']
            if can_walk_to_node(cells_2_map(cells), tmp_end_cell, node):
                potential_end_nodes_ids.append(key)

    couples = list(itertools.product(potential_start_nodes_ids, potential_end_nodes_ids))
    best_path, length = None, sys.maxsize
    for couple in couples:
        path = get_path_nodes(graph, couple[0], couple[1])
        if path is not False and len(path) < length:
            best_path = path
            length = len(path)
    return best_path


def generate_token(valid_until, description):
    """
    generated a token to access the swarm node

    :param valid_until: timestamp in seconds since 01/01/1970
    :param description: A description of whet the token is used for
    :return: token
    """
    token = str(uuid.uuid4())
    client = mongo_client()
    client.blackfalcon.tokens.insert_one({'token': token, 'valid_until': valid_until, 'description': description})
    return token


def delete_token(token):
    client = mongo_client()
    client.blackfalcon.tokens.delete_one({'token': token})


def token_is_authorized(token):
    """
    Used to control access to the swarm node
    :param token: a token provided in the credentials.py
    :return: bool
    """
    client = mongo_client()
    token_data = client.blackfalcon.tokens.find_one({'token': token})
    if token_data is None:
        return False
    if token_data['valid_until'] < time.time():
        delete_token(token)
        return False
    return token_data['valid_until']


def log_prices(object_type, data, server, sampling_time):
    conn = psycopg2.connect(
        dbname=credentials['postgre']['database'],
        user=credentials['postgre']['user'],
        host=credentials['postgre']['host'],
        password=credentials['postgre']['password'],
        port=credentials['postgre']['port']
    )
    cursor = conn.cursor()

    if object_type == 'item':
        objects = []
        for item_id, item in list(data.items()):
            for object in item['items_stats']:
                formatted_object = (
                    item_id,
                    server,
                    object['prices'][0],
                    object['prices'][1],
                    object['prices'][2],
                    -1,
                    str(object['effects']).replace("'", '"'),
                    hashlib.sha256(str(object['effects']).encode('utf8')).hexdigest(),
                    int(sampling_time)
                )
                objects.append(formatted_object)
        cursor.executemany("INSERT INTO itemprices (itemid, server, price1, price10, price100, craftcost, stats, hash, sampleid) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)

    elif object_type == 'resource':
        objects = []
        for item_id, item in list(data.items()):
            for object in item['items_stats']:
                formatted_object = (
                    item_id,
                    'Julith',
                    object['prices'][0],
                    object['prices'][1],
                    object['prices'][2],
                    sampling_time
                )
                objects.append(formatted_object)
        cursor.executemany("INSERT INTO resourceprices (itemid, server, price1, price10, price100, sampleid) VALUES(%s,%s,%s,%s,%s,%s)", objects)

    else:
        raise Exception('Type must be "item" or "resource", got {}'.format(object_type))
    conn.commit()
    conn.close()
    return len(objects)


if __name__ == '__main__':
    # mapinfo = []
    # for i in range(8):
    #     with open('../assets/map_info_{}.json'.format(i), 'r', encoding='utf8') as f:
    #         mapinfo += json.load(f)
    # graph = {}
    # for i in range(2):
    #     with open('../assets/pathfinder_graph_{}.json'.format(i), 'r', encoding='utf8') as f:
    #         graph.update(json.load(f))
    #
    # print('Starting')
    # print(get_path(mapinfo, graph, (4, -18), (3, -5)))
    # client = mongo_client()
    # print([thing for thing in client.blackfalcon.tokens.find({})])
    # token = generate_token(time.time() + 90, 'Test token')
    # print(token)
    # print(token_is_authorized(token))
    log_prices('lel', '')
