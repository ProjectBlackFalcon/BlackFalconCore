import ast
import json
import queue
from threading import Thread
from tkinter import *
import requests
import ws_connector


def get_strategies():
    link = 'https://raw.githubusercontent.com/ProjectBlackFalcon/BlackFalconCore/master/swarm_manager/strategies.md'
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
                field[-1].grid(row=len(form) + 1, column=1)

                field.append(Entry(form_frame))
                field[-1].grid(row=len(form) + 1, column=2)

                form.append(field)
    form.append(strat['command'])
    Button(form_frame, text='GO', command=lambda: execute_strat(form)).grid(row=len(form) + 1, column=2)


def execute_strat(form):
    strategy = {
        'bot': bot_name.get(),
        'command': form[-1]
    }
    parameters = {}
    for field in form[:-1]:
        parameters[field[0].cget('text')] = ast.literal_eval(field[1].get()) if field[1].get().isdigit() else field[1].get()
    strategy['parameters'] = parameters

    orders.put((json.dumps(strategy),))


def login(orders):
    print('Logging in')
    Thread(target=ws_connector.Connection, args=(address.get(), port.get(), orders, queue.Queue())).start()


strategies = get_strategies()
tk = Tk()
tk.title('Manual strategy sender')

main_frame = Frame(tk)
main_frame.grid(row=1, column=1)


login_frame = Frame(main_frame)
login_frame.grid(row=1, column=1)
Label(login_frame, text="Swarm node address").grid(row=0, column=1)
address = Entry(login_frame)
address.insert(END, '89.234.181.110')
address.grid(row=0, column=2)
Label(login_frame, text="Swarm node port").grid(row=1, column=1)
port = Entry(login_frame)
port.insert(END, 8721)
port.grid(row=1, column=2)

orders = queue.Queue()
Button(login_frame, text='Login', command=lambda: login(orders)).grid(row=2, column=2)

Label(main_frame, text="Bot name").grid(row=2, column=1)
bot_name = Entry(main_frame)
bot_name.insert(END, 'Mystinu')
bot_name.grid(row=2, column=2)

selected_strat = StringVar(tk)
choices = ['Pick a strat'] + list(strategies.keys())
selected_strat.set(choices[0])
popupMenu = OptionMenu(main_frame, selected_strat, *choices)
Label(main_frame, text="Choose a strategy").grid(row=3, column=1)
popupMenu.grid(row=3, column=2)
selected_strat.trace('w', pick_dropdown)

form_frame = Frame(tk)
form_frame.grid(row=5, column=1)

orders.put((json.dumps({"bot": "Mystinu", "command": "connect", "parameters": {}}),))
tk.mainloop()
