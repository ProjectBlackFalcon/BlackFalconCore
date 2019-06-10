import numpy as np
from PIL import Image
from heapq import *
import time
from random import randint

from tools import logger as log
import strategies


def goto(**kwargs):
    strategy = kwargs['strategy']
    listener = kwargs['listener']
    orders_queue = kwargs['orders_queue']
    assets = kwargs['assets']

    target_x = strategy['parameters']['x']
    target_y = strategy['parameters']['y']
    target_cell = strategy['parameters']['cell']
    target_worldmap = strategy['parameters']['worldmap']

    logger = log.get_logger(__file__, strategy['bot']['name'])

    # get current pos
    # check if path exists already
    # if it does, select that
    # otherwise make a new one
    # actually perform the goto

    log.close_logger(logger)
    return strategy


class PathMaker:
    def __init__(self, strategy, listener, orders_queue, logger, assets, target_coord, target_cell=None, worldmap=1, harvest=False, forbid_zaaps=False):
        self.strategy = strategy
        self.listener = listener
        self.orders_queue = orders_queue
        self.logger = logger
        self.assets = assets
        self.target_coord = target_coord
        self.target_cell = target_cell
        self.target_worldmap = worldmap
        self.harvest = harvest
        self.forbid_zaaps = forbid_zaaps

    def getmap(self):
        current_map, current_cell, current_worldmap, map_id = self.listener['pos'], self.listener['cell'], self.listener['worldmap'], self.listener['map_id']
        return current_map, current_cell, current_worldmap, map_id

    def distance(self, pos1, pos2):
        return ((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2) ** 0.5

    def pathmaker(self, target_coord, target_cell=None, worldmap=1, harvest=False, forbid_zaaps=False):
        current_map, current_cell, current_worldmap, map_id = self.getmap()

        if current_worldmap != worldmap:

            # Incarnam to Astrub
            if current_worldmap == 2 and worldmap == 1:
                self.pathmaker((4, -3), worldmap=2)
                strategies.go_to_astrub(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    }
                )
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Astrub to Incarnam
            elif current_worldmap == 1 and worldmap == 2:
                gate_map = (6, -19)
                self.pathmaker(gate_map, target_cell=397)
                strategies.go_to_incarnam(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    }
                )
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Bot is in hunting hall
            elif list(current_map) == [-25, -36] and current_worldmap == -1:
                strategies.exit_hunting_hall(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    strategy={
                        'bot': self.strategy['bot'],
                    }
                )
                current_map, current_cell, current_worldmap, map_id = self.getmap()

            # Bot is in a building or underground
            elif current_worldmap == -1:
                closest_zaap = self.get_closest_known_zaap(target_coord)
                if closest_zaap is not None:
                    success = strategies.enter_havenbag(
                        listener=self.listener,
                        strategy={'bot': self.strategy['bot']},
                        orders_queue=self.orders_queue
                    )['report']['success']

                    if success:
                        report = strategies.use_zaap(
                            listener=self.listener,
                            orders_queue=self.orders_queue,
                            assets=self.assets,
                            strategy={
                                'bot': self.strategy['bot'],
                                'parameters': {'target_zaap': closest_zaap}
                            }
                        )['report']
                        current_map, current_cell, current_worldmap, map_id = self.getmap()
                        if not report['success']:
                            self.logger.warn('Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                            raise RuntimeError('Unable to use Zaap to go to {}'.format(closest_zaap))
                else:
                    raise RuntimeError('No known zaaps')

            # TODO manage more worldmap changing
            else:
                raise RuntimeError('Worldmap change not supported')

        closest_zaap = strategies.support_functions.get_closest_known_zaap(self.strategy['bot']['name'], target_coord)
        if closest_zaap is not None and not forbid_zaaps:
            distance_zaap_target = self.distance(closest_zaap, target_coord)
            if worldmap == current_worldmap and self.distance(current_map, target_coord) > distance_zaap_target + 5:
                report = strategies.enter_havenbag(
                    listener=self.listener,
                    strategy={'bot': self.strategy['bot']},
                    orders_queue=self.orders_queue
                )['report']

                if report['success']:
                    report = strategies.use_zaap(
                        listener=self.listener,
                        orders_queue=self.orders_queue,
                        assets=self.assets,
                        strategy={
                            'bot': self.strategy['bot'],
                            'parameters': {'target_zaap': closest_zaap}
                        }
                    )['report']
                    current_map, current_cell, current_worldmap, map_id = self.getmap()
                    if not report['success']:
                        self.logger.warn('Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                        raise RuntimeError('Unable to use Zaap to go to {}'.format(closest_zaap))
                else:
                    # If unable to enter havenbag, than just walk to the closest zaap and use this one
                    closest_zaap_2 = strategies.support_functions.get_closest_known_zaap(self.strategy['bot']['name'], current_map)
                    self.pathmaker(closest_zaap_2, forbid_zaaps=True)
                    if closest_zaap != closest_zaap_2:
                        report = strategies.use_zaap(
                            listener=self.listener,
                            orders_queue=self.orders_queue,
                            assets=self.assets,
                            strategy={
                                'bot': self.strategy['bot'],
                                'parameters': {'target_zaap': closest_zaap}
                            }
                        )['report']
                        if not report['success']:
                            self.logger.warn(
                                'Unable to use Zaap to go to {}. Reason: {}'.format(closest_zaap, report['details']))
                            raise RuntimeError('Unable to use Zaap to go to {}'.format(closest_zaap))
                    current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.assets['brak_maps'] and list(target_coord) in self.assets['brak_maps']:
            # Bot needs to enter brak
            disc_zaaps = strategies.support_functions.get_known_zaaps(self.strategy['bot']['name'])
            if (-26, 35) in disc_zaaps:
                success = strategies.enter_havenbag(
                    listener=self.listener,
                    strategy={'bot': self.strategy['bot']},
                    orders_queue=self.orders_queue
                )['report']['success']

                if success:
                    report = strategies.use_zaap(
                        listener=self.listener,
                        orders_queue=self.orders_queue,
                        assets=self.assets,
                        strategy={
                            'bot': self.strategy['bot'],
                            'parameters': {'target_zaap': (-26, 35)}
                        }
                    )['report']
                    if not report['success']:
                        self.logger.warn('Unable to use Zaap to go to {}. Reason: {}'.format((-26, 35), report['details']))
                        raise RuntimeError('Unable to use Zaap to go to {}'.format((-26, 35)))
                current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) in self.assets['brak_maps'] and list(target_coord) not in self.assets['brak_maps']:
            # Bot needs to exit brak
            if list(target_coord) in self.assets['brak_maps']:
                self.pathmaker((-20, 34))
                strategies.change_map(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    assets=self.assets,
                    strategy={
                        'bot': self.strategy['bot'],
                        'parameters': {'cell': 307, 'direction': 'e'}
                    }
                )
            elif list(target_coord) in self.bot.resources.brak_north_maps:
                self.pathmaker((-26, 31))
                strategies.exit_brak_north(
                    listener=self.listener,
                    orders_queue=self.orders_queue,
                    assets=self.assets,
                    strategy={'bot': self.strategy['bot']}
                )
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) in self.bot.resources.west_dd_territory_maps and list(target_coord) in self.bot.resources.dd_territory_maps:
            # Bot needs to enter dd territory from west
            self.goto((-23, -1), target_cell=387)
            self.bot.interface.enter_dd_territory()
            current_map, current_cell, current_worldmap, map_id = self.getmap()
        if list(current_map) in self.bot.resources.dd_territory_maps and list(target_coord) in self.bot.resources.west_dd_territory_maps:
            # Bot needs to exit dd territory to the west
            self.goto((-22, -1))
            self.bot.interface.change_map(294, 'w')
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.bot.resources.castle_maps and list(target_coord) in self.bot.resources.castle_maps:
            # Bot needs to enter the castle
            disc_zaaps = self.bot.llf.get_discovered_zaaps(self.bot.credentials['name'])
            if [3, -5] in disc_zaaps and self.bot.interface.enter_heavenbag()[0]:
                self.bot.interface.use_zaap((3, -5))
                current_map, current_cell, current_worldmap, map_id = self.getmap()
        if list(current_map) in self.bot.resources.castle_maps and list(target_coord) not in self.bot.resources.castle_maps:
            # Bot needs to exit the castle through the northern gate
            if target_coord[1] <= current_map[1]:
                self.goto((4, -8))
                self.bot.interface.change_map(140, 'w')
                current_map, current_cell, current_worldmap, map_id = self.getmap()

        if list(current_map) not in self.bot.resources.bwork_maps and list(target_coord) in self.bot.resources.bwork_maps:
            # Bot needs to enter bwork village
            self.goto((-1, 8), target_cell=383)
            self.bot.interface.enter_bwork()
            current_map, current_cell, current_worldmap, map_id = self.getmap()
        if list(current_map) in self.bot.resources.bwork_maps and list(target_coord) not in self.bot.resources.bwork_maps:
            # Bot needs to exit bwork village
            self.goto((-2, 8), target_cell=260)
            self.bot.interface.exit_bwork()
            current_map, current_cell, current_worldmap, map_id = self.getmap()

        if current_map == target_coord and current_cell == target_cell and worldmap == current_worldmap:
            return

        if current_map == target_coord and worldmap == current_worldmap and target_cell is not None:
            if self.bot.interface.move(target_cell):
                return

        pf = PathFinder(self.bot, current_map, target_coord, current_cell, target_cell, worldmap)
        path_directions = pf.get_map_change_cells()
        for i in range(len(path_directions)):
            if self.bot.interface.change_map(path_directions[i][0], path_directions[i][1])[0]:
                current_map, current_cell, current_worldmap, map_id = self.getmap()
                self.bot.position = current_map, current_worldmap
                if current_worldmap == 1:
                    self.bot.llf.add_discovered_zaap(self.bot.credentials['name'], self.bot.position)
                if harvest:
                    self.harvest_map()
            else:
                raise ValueError('Interface returned false on move command. Position : {}, Cell : {}, Direction : {}'.format(self.bot.position, path_directions[i][0], path_directions[i][1]))

        if tuple(current_map) != tuple(target_coord):
            self.goto(target_coord, target_cell, worldmap)

        if target_cell is not None:
            self.bot.interface.move(target_cell)
        self.bot.position = (target_coord, worldmap)


class PathFinder:
    def __init__(self, start_map, end_map, start_cell, end_cell, worldmap, mapinfo, logger, max_enlargement=15):
        self.logger = logger
        self.start = start_map
        self.end = end_map
        self.worldmap = worldmap
        self.start_cell = start_cell
        self.start_cell = self.pick_start_cell()
        self.end_cell = end_cell
        self.end_cell = self.pick_end_cell()
        self.logger.info('Going from map {}, cell {} to map {}, cell {}, worldmap : {}'.format(start_map, start_cell, end_map, self.end_cell, worldmap))
        self.bbox = (
            min(start_map[0], end_map[0]),
            min(start_map[1], end_map[1]),
            max(start_map[0], end_map[0]),
            max(start_map[1], end_map[1])
        )
        self.shape = (abs(self.bbox[1]-self.bbox[3])+1, abs(self.bbox[0]-self.bbox[2])+1)
        self.mapinfo = mapinfo
        self.maps_coords = []
        self.glued_maps = []
        self.adapted_maps = []
        self.path_cells = []
        self.map_change_coords = []
        self.map_change_cells = []
        self.map_change_directions = []
        self.max_enlargement = max_enlargement
        self.enlargement_n = 0

    def load_map_info(self):
        corners = [(0, 0), (1, 0), (0, 1), (0, 2), (13, 0), (12, 1), (13, 1), (13, 2), (13, 37), (13, 38), (12, 39),
                   (13, 39), (0, 37), (0, 38), (1, 38), (0, 39)]
        for map in self.mapinfo:
            for pos in corners:
                map['cells'][pos[1]][pos[0]] = 2
        return self.mapinfo

    def coord_fetch_map(self, coord, worldmap):
        maps = []
        for map in self.mapinfo:
            if map['coord'] == coord and map['worldMap'] == worldmap:
                maps.append(map)
        if len(maps) == 1 and maps[0] is not None:
            return maps[0]['cells']
        elif len(maps) > 1:
            for map in maps:
                if map['hasPriorityOnWorldMap']:
                    return map['cells']

    def enlarge(self):
        self.enlargement_n += 1
        self.logger.info('Enlarging')
        self.bbox = (
            self.bbox[0]-1,
            self.bbox[1]-1,
            self.bbox[2]+1,
            self.bbox[3]+1
        )
        self.shape = (abs(self.bbox[1]-self.bbox[3])+1, abs(self.bbox[0]-self.bbox[2])+1)
        self.mapinfo = self.load_map_info()
        self.maps_coords = []
        self.glued_maps = []
        self.adapted_maps = []
        self.path_cells = []
        self.map_change_coords = []
        self.map_change_cells = []
        self.map_change_directions = []

    def get_maps_coords(self):
        xn = abs(self.bbox[0]-self.bbox[2])+1
        yn = abs(self.bbox[1]-self.bbox[3])+1
        maps = []
        for y in range(yn):
            for x in range(xn):
                maps.append('{};{}'.format(self.bbox[0]+x, self.bbox[1]+y))
        sorted(maps, key=lambda p: [p[1], p[0]])
        self.maps_coords = maps[:]
        return maps[:]

    def id_fetch_map(self, id):
        for map in self.mapinfo:
            if map['id'] == id:
                return map

    def glue_maps(self, maps_as_arrays, shape):
        if shape[0]*shape[1] != len(maps_as_arrays):
            raise Exception('n_row*n_col is different than the number of arrays given')
        else:
            maps_as_arrays = np.array(maps_as_arrays)
            # print(maps_as_arrays.shape)
            arr = maps_as_arrays.reshape(shape[0], shape[1], 40, 14)
            out = np.concatenate([np.concatenate([map for map in arr[i]], axis=1) for i in range(shape[0])], axis=0)
            start_pos = (
                self.cell2coord(self.start_cell)[0]+14*(self.start[0]-self.bbox[0]),
                self.cell2coord(self.start_cell)[1]+40*(self.start[1]-self.bbox[1])
            )
            goal_pos = (
                self.cell2coord(self.end_cell)[0]+14*(self.end[0]-self.bbox[0]),
                self.cell2coord(self.end_cell)[1]+40*(self.end[1]-self.bbox[1])
            )

            # Euclidean distance
            while ((goal_pos[0] - start_pos[0]) ** 2 + (goal_pos[1] - start_pos[1]) ** 2) ** 0.5 <= 2:
                self.end_cell = None
                self.end_cell = self.pick_end_cell()
                goal_pos = (
                    self.cell2coord(self.end_cell)[0] + 14 * (self.end[0] - self.bbox[0]),
                    self.cell2coord(self.end_cell)[1] + 40 * (self.end[1] - self.bbox[1])
                )
            out[start_pos[1]][start_pos[0]] = -2
            out[goal_pos[1]][goal_pos[0]] = -3
            self.glued_maps = out[:]
            return out[:]

    def adapt_shape_maps(self, maps):
        maps = np.array(maps)
        shape = maps.shape
        flattened = maps.flatten()
        new_base = np.zeros((14*shape[1]//14 + 20*shape[0]//40-1, 14*shape[1]//14 + 20*shape[0]//40))
        new_base[new_base == 0] = -1
        for i in range(len(flattened)):
            coord = i % shape[1] + int((i//shape[1])/2+0.5), (shape[1]-1 - i % shape[1] + int((i//shape[1])/2))
            new_base[coord[1]][coord[0]] = flattened[i]
        self.adapted_maps = new_base[:]
        return new_base[:]

    def map_to_image(self, map_as_array, scaling_factor):
        # print('[Pathfinder] Generating image...')
        map_as_array = np.array(map_as_array)
        map_as_array[map_as_array == 0] = 0
        # map_as_array[map_as_array != 0] = 1
        a = np.kron(map_as_array, np.ones((scaling_factor, scaling_factor))).astype(int)
        a[a == 0] = 255*180  # Walkable
        a[a == 2] = 255*32
        a[a == 5] = 255*200
        a[a == 4] = 255*255*255  # Path
        a[a == -2] = 255*128
        a[a == -3] = 255*128
        Image.fromarray(a).save('Out.png')
        return Image.fromarray(a)
        # print('[Pathfinder] Done')

    def heuristic(self, a, b):
        return (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2

    def astar(self, start_pos, goal_pos):
        start = time.time()
        self.logger.info('Generating path...')

        start_pos = start_pos[1], start_pos[0]
        goal_pos = goal_pos[1], goal_pos[0]

        # print(self.glued_maps.shape)

        neighbors = [(1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (0, 1), (-1, 0), (0, -1)]

        close_set = set()
        came_from = {}
        gscore = {start_pos: 0}
        fscore = {start_pos: self.heuristic(start_pos, goal_pos)}
        oheap = []

        heappush(oheap, (fscore[start_pos], start_pos))
        while oheap:
            current = heappop(oheap)[1]
            if current == goal_pos:
                data = []
                while current in came_from:
                    data.append(current)
                    current = came_from[current]
                self.path_cells = data

            close_set.add(current)
            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                tentative_g_score = gscore[current] + self.heuristic(current, neighbor)
                if 0 <= neighbor[0] < self.adapted_maps.shape[0]:
                    if 0 <= neighbor[1] < self.adapted_maps.shape[1]:
                        if self.adapted_maps[neighbor[0]][neighbor[1]] not in [0, -2, -3]:
                            continue
                    else:
                        # array bound y walls
                        continue
                else:
                    # array bound x walls
                    continue

                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                    continue

                if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1]for i in oheap]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_pos)
                    heappush(oheap, (fscore[neighbor], neighbor))
        if self.path_cells:
            self.logger.info('Done in {}s'.format(round(time.time()-start, 1)))
        else:
            self.logger.info('Unable to get path')
        return False

    def add_path_to_adapted_maps(self):
        for x, y in self.path_cells:
            self.adapted_maps[x][y] = 4

    def add_map_change_coords_to_adapted_maps(self):
        for x, y in self.map_change_coords:
            self.adapted_maps[x][y] = 5

    def get_path_try(self):
        if not self.maps_coords:
            self.get_maps_coords()

        maps_list = []
        for coord in self.maps_coords:
            map_infos = self.coord_fetch_map(coord, self.worldmap)
            if map_infos is not None:
                maps_list.append(map_infos)
            else:
                maps_list.append([[1 for i in range(14)] for j in range(40)])
        self.glue_maps(maps_list, self.shape)
        self.adapt_shape_maps(self.glued_maps)
        # self.map_to_image(self.glued_maps, 10)

        # IndexError: index 0 is out of bounds for axis 0 with size 0
        start_pos = (np.where(self.adapted_maps == -2)[1][0], np.where(self.adapted_maps == -2)[0][0])
        goal_pos = (np.where(self.adapted_maps == -3)[1][0], np.where(self.adapted_maps == -3)[0][0])

        self.astar(goal_pos, start_pos)

    def get_path(self):
        self.get_path_try()
        # print(self.path_cells)
        while not self.path_cells and self.enlargement_n < self.max_enlargement:
            self.enlarge()
            self.get_path_try()
        if not self.path_cells:
            self.logger.warn('Could not generate path from {} cell {} to {} cell {}'.format(self.start, self.start_cell, self.end, self.end_cell))
            raise RuntimeError('Could not generate path from {} cell {} to {} cell {}'.format(self.start, self.start_cell, self.end, self.end_cell))
        # self.path_cells.append(self.cell2coord_diag(self.end_cell))

    def get_map_change_cells(self):
        if not self.path_cells:
            self.get_path()

        # print(self.path_cells)
        total_width = len(self.glued_maps[1])
        width = 14
        path_map_change_cells = []
        path_cells = []
        top_map_change_cells = [i for i in range(28)]
        left_map_change_cells = [i for i in range(560) if i % 14 == 0]
        right_map_change_cells = [i for i in range(560) if i % 14 == 13]
        bottom_map_change_cells = [i for i in range(532, 560)]
        for x, y in self.path_cells:
            cell = self.coord2cell_diag((y, x))
            path_cells.append(cell)

        path_cells.append(self.end_cell)
        for i in range(len(path_cells)-1):
            current = (path_cells[i] - width*((path_cells[i] // width) % (total_width//width)) - (total_width-width)*(path_cells[i]//total_width)) % 560
            nxt = (path_cells[i+1] - width*((path_cells[i+1] // width) % (total_width//width)) - (total_width-width)*(path_cells[i+1]//total_width)) % 560
            if current in top_map_change_cells and nxt in bottom_map_change_cells:
                path_map_change_cells.append(current)
                self.map_change_directions.append('n')
            elif current in bottom_map_change_cells and nxt in top_map_change_cells:
                path_map_change_cells.append(current)
                self.map_change_directions.append('s')
            elif current in left_map_change_cells and nxt in right_map_change_cells:
                path_map_change_cells.append(current)
                self.map_change_directions.append('w')
            elif current in right_map_change_cells and nxt in left_map_change_cells:
                path_map_change_cells.append(current)
                self.map_change_directions.append('e')

        out = [(path_map_change_cells[i], self.map_change_directions[i]) for i in range(len(path_map_change_cells))]
        return out[:]

    def cell2coord(self, cell):
        return (cell % 14), cell//14

    def coord2cell(self, coord):
        coord = coord[1] % 14, coord[0] % 40
        return coord[1]*14+coord[0]

    def coord2cell_diag(self, coord):
        width = len(self.glued_maps[0])
        i = 0
        result = i % width + int((i//width)/2+0.5), (width-1 - i % width + int((i//width)/2))
        while result != coord:
            i += 1
            result = i % width + int((i//width)/2+0.5), (width-1 - i % width + int((i//width)/2))
        return i

    def cell2coord_diag(self, cell):
        width = len(self.glued_maps[0])
        return cell % width + int((cell//width)/2+0.5), (width-1 - cell % width + int((cell//width)/2))

    def pick_end_cell(self):
        if self.end_cell is None:
            end_map_cells = self.coord_fetch_map('{};{}'.format(self.end[0], self.end[1]), self.worldmap)
            map_change_cells = list(set([i for i in range(28)] + [i for i in range(560) if i % 14 == 0] + [i for i in range(560) if i % 14 == 13] + [i for i in range(532, 560)]))
            found_walkable = False
            timeout = 10
            timer = time.time()
            while not found_walkable and (time.time()-timer < timeout):
                x, y = self.cell2coord(map_change_cells[randint(0, len(map_change_cells)-1)])
                if end_map_cells[y][x] == 0:
                    found_walkable = True
                self.end_cell = self.coord2cell((y, x))
            if not found_walkable:
                self.logger.warn('Map is inaccessible')
                raise Exception('Map is inaccessible')
        return self.end_cell

    def pick_start_cell(self):
        if self.start_cell is None:
            start_map_cells = self.coord_fetch_map('{};{}'.format(self.start[0], self.start[1]), self.worldmap)
            map_change_cells = list(set([i for i in range(28)] + [i for i in range(560) if i % 14 == 0] + [i for i in range(560) if i % 14 == 13] + [i for i in range(532, 560)]))
            found_walkable = False
            while not found_walkable:
                x, y = self.cell2coord(map_change_cells[randint(0, len(map_change_cells)-1)])
                # print(self.coord2cell((x, y)), end_map_cells[y][x])
                if start_map_cells[y][x] == 0:
                    found_walkable = True
                self.start_cell = self.coord2cell((y, x))
        return self.start_cell


__author__ = 'Alexis'