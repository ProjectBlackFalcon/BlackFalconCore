import ast
import json
import os
import pymongo

import numpy as np
import queue
import time
from threading import Thread
from tkinter import *
import requests
import ws_connector
from credentials import credentials


def load_map_info():
    assets_paths = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    files_packs = {}
    assets = {}
    for file in os.listdir(assets_paths):
        if file.endswith('.json') and 'map_info' in file:
            if file.replace('.json', '').split('_')[-1].isdigit():
                if '_'.join(file.replace('.json', '').split('_')[:-1]) not in files_packs.keys():
                    files_packs['_'.join(file.replace('.json', '').split('_')[:-1])] = [file]
                else:
                    files_packs['_'.join(file.replace('.json', '').split('_')[:-1])].append(file)
            else:
                files_packs[file.replace('.json', '')] = [file]

    for asset_name, file_pack in files_packs.items():
        for file in file_pack:
            with open(assets_paths + '/' + file, 'r', encoding='utf8') as f:
                data = json.load(f)
            if asset_name not in assets.keys():
                assets[asset_name] = data
            else:
                if type(data) is list:
                    assets[asset_name] += data
                elif type(data) is dict:
                    assets[asset_name].update(data)
    return assets


def fetch_map(coord, worldmap):
    maps = []
    for map in map_info['map_info']:
        if map['coord'] == coord and map['worldMap'] == worldmap:
            maps.append(map)
    if len(maps) == 1 and maps[0] is not None:
        return maps[0]
    elif len(maps) > 1:
        for map in maps:
            if map['hasPriorityOnWorldMap']:
                return map


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


def coord_2_cell(x, y):
    for i in range(560):
        cy, cx = (14 - 1 - i % 14 + int((i // 14) / 2)), i % 14 + int((i // 14) / 2 + 0.5)
        if cx == x and cy == y:
            return i


def get_strategies():
    link = 'https://raw.githubusercontent.com/ProjectBlackFalcon/BlackFalconCore/master/strategies/strategies.md'
    raw_text_strats = requests.get(link).text
    strategies = {}
    last_bracket_counter, bracket_counter = 0, 0
    strategy = ''
    name = None
    for line in raw_text_strats.split('\n'):

        if '###' in line:
            name = line.replace('###', '').strip()
            bracket_counter = 0

        for char in line:
            if char == '{':
                last_bracket_counter = bracket_counter
                bracket_counter += 1
            if char == '}':
                last_bracket_counter = bracket_counter
                bracket_counter -= 1

        if bracket_counter > 0:
            strategy += line

        if last_bracket_counter == 1 and bracket_counter == 0:
            strategies[name] = (json.loads(strategy + '}'))
            strategy = ''
            last_bracket_counter = 0
    return strategies


def pick_dropdown(*args):
    strat = selected_strat.get()
    if strat != 'Pick a strat':
        strat = strategies[strat]
    else:
        return

    for child in form_frame.winfo_children():
        child.destroy()

    form = []
    for key in strat.keys():
        if key == 'parameters':
            for param, example_value in strat[key].items():
                field = []

                field.append(Label(form_frame, text=param))
                field[-1].grid(row=len(form) + 1, column=0)

                field.append(Entry(form_frame))
                field[-1].grid(row=len(form) + 1, column=1)

                form.append(field)
    form.append(strat['command'])
    Button(form_frame, text='GO', command=lambda: execute_strat(form)).grid(row=len(form) + 1, column=1)


def execute_strat(form):
    strategy = {
        'bot': bot_name.get(),
        'command': form[-1]
    }
    parameters = {}
    for field in form[:-1]:
        try:
            number = int(field[1].get())
            parameters[field[0].cget('text')] = number
        except:
            if field[1].get() == '':
                parameters[field[0].cget('text')] = None
            else:
                try:
                    parameters[field[0].cget('text')] = ast.literal_eval(field[1].get())
                except:
                    parameters[field[0].cget('text')] = field[1].get()
    strategy['parameters'] = parameters

    success_label = Label(form_frame, text='Pending...', fg='orange')
    success_label.grid(row=len(form) + 1, column=2)

    orders[bot_name.get()].put((json.dumps(strategy),))
    Thread(target=check_result, args=(success_label, )).start()


def check_result(success_label):
    report = json.loads(reports[bot_name.get()].get()[0])
    if 'report' in report.keys() and report['report']['success']:
        success_label['text'] = 'Success'
        success_label['fg'] = 'green'
    elif 'report' in report.keys() and report['report']['success']:
        success_label['text'] = 'Failed'
        success_label['fg'] = 'red'
    else:
        success_label['text'] = 'Crashed'
        success_label['fg'] = 'red'


def get_pos_info():
    client = pymongo.MongoClient(
        host=credentials['mongo']['host'],
        port=credentials['mongo']['port'],
        username=credentials['mongo']['username'],
        password=credentials['mongo']['password'],
    )
    previous_profile = None
    while 1:
        profile = client.blackfalcon.bots.find_one({'name': bot_name.get()})
        if profile is None:
            raise Exception('Bot does not exist. Create a profile using the \'new_bot\' command first.')

        if profile != previous_profile:
            pos_info_1['text'] = str(profile['position'])
            pos_info_2['text'] = str(profile['worldmap']) + ' | ' + str(profile['cell'])
            map_data = fetch_map(f'{profile["position"][0]};{profile["position"][1]}', profile['worldmap'])
            canvas.delete("all")
            canvas.create_rectangle(0, 0, 340, 330, fill="light grey")
            if map_data is not None:
                map = cells_2_map(map_data['cells'])

                for y in range(len(map)):
                    for x in range(len(map[y])):
                        if map[y, x] == 0:
                            canvas.create_rectangle(x * 10, y * 10, (x + 1) * 10, (y + 1) * 10, fill='white')
                        if map[y, x] == 2:
                            canvas.create_rectangle(x * 10, y * 10, (x + 1) * 10, (y + 1) * 10, fill='dark grey')
                        if map[y, x] == 1:
                            canvas.create_rectangle(x * 10, y * 10, (x + 1) * 10, (y + 1) * 10, fill='grey')
                        if map[y, x] >= 3:
                            canvas.create_rectangle(x * 10, y * 10, (x + 1) * 10, (y + 1) * 10, fill='light green')
                bot_pos = (14 - 1 - profile['cell'] % 14 + int((profile['cell'] // 14) / 2)), profile['cell'] % 14 + int((profile['cell'] // 14) / 2 + 0.5)
                canvas.create_rectangle(bot_pos[1] * 10, bot_pos[0] * 10, (bot_pos[1] + 1) * 10, (bot_pos[0] + 1) * 10, fill='red')
            previous_profile = profile
            time.sleep(0.5)
        time.sleep(0.5)


def login(orders, reports):
    print('Logging in')
    orders[bot_name.get()] = queue.Queue()
    reports[bot_name.get()] = queue.Queue()
    Thread(target=ws_connector.Connection, args=(address.get(), port.get(), orders[bot_name.get()], reports[bot_name.get()])).start()
    execute_strat(['connect'])


def moved(event):
    canvas_coords['text'] = f'Coords: {event.x // 10}, {event.y // 10} | Cell : {coord_2_cell(event.x // 10, event.y // 10)}'


map_info = load_map_info()
strategies = get_strategies()
tk = Tk()
tk.title('Manual strategy sender')

main_frame = Frame(tk)
main_frame.grid(row=1, column=1)


login_frame = Frame(tk)
login_frame.grid(row=0, column=1)
Label(login_frame, text="Swarm node address").grid(row=0, column=1)
address = Entry(login_frame)
address.insert(END, '89.234.181.110')
address.grid(row=0, column=2)
Label(login_frame, text="Swarm node port").grid(row=1, column=1)
port = Entry(login_frame)
port.insert(END, 8721)
port.grid(row=1, column=2)

pos_info_1 = Label(login_frame, text="No info available")
pos_info_1.grid(row=0, column=3)
pos_info_2 = Label(login_frame, text="No info available")
pos_info_2.grid(row=1, column=3)

orders = {}
reports = {}
Button(login_frame, text='Login', command=lambda: login(orders, reports)).grid(row=2, column=2)

Label(main_frame, text="Bot name").grid(row=2, column=1)
bot_name = Entry(main_frame)
bot_name.insert(END, 'Usain-bot')
bot_name.grid(row=2, column=2)

selected_strat = StringVar(tk)
choices = ['Pick a strat'] + list(strategies.keys())
selected_strat.set(choices[0])
popupMenu = OptionMenu(main_frame, selected_strat, *choices)
Label(main_frame, text="Choose a strategy").grid(row=3, column=1)
popupMenu.grid(row=3, column=2)
selected_strat.trace('w', pick_dropdown)

form_frame = Frame(tk)
form_frame.grid(row=2, column=1)

canvas = Canvas(tk, width=340, height=330)
canvas_coords = Label(tk, text='')
canvas_coords.grid(row=2, column=2)
canvas.grid(row=0, rowspan=2, column=2)
canvas.bind("<Motion>", moved)
canvas.create_rectangle(0, 0, 340, 330, fill="light grey")

Thread(target=get_pos_info).start()

tk.mainloop()
