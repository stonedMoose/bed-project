#!/usr/bin/python

from Tkinter import *
from ttk import *
import os
import matplotlib.pyplot as plt
from server import setBaseTemp


def update_temp(entry, room_nb):
    """
    Send message to update temperature
    """
    value = entry.get()
    if value == 'Entrez une temperature':
        pass
    else:
        try:
            temp = float(entry.get())
        except ValueError:
            print "You must enter float or int value for a temperature"
            
        else:
            if temp < 0 or temp > 100:
                print "The temperature must be between 0 and 100"
            else:
                setBaseTemp(temp, room_nb)
                print "Sending message to update temp:", temp, "of room", room_nb
        entry.delete(0, "end")  # delete all the text in the entry
        entry.insert(0, 'Entrez une temperature')
        entry.config(foreground='grey')


def on_entry_click(event, entry):
    """function that gets called whenever entry is clicked"""
    if entry.get() == 'Entrez une temperature':
        entry.delete(0, "end")  # delete all the text in the entry
        entry.insert(0, '')  # Insert blank for user input
        entry.config(foreground='black')


def on_focusout(event, entry):
    if entry.get() == '':
        entry.insert(0, 'Entrez une temperature')
        entry.config(foreground='grey')


def create_room_interface(room_nb, row_rank):
    l = Label(tk, text="Salle " + room_nb + ":   ", font="Helvetica 12 bold")
    e = Entry(tk)
    e.insert(0, 'Entrez une temperature')
    e.config(foreground='grey')
    e.bind('<FocusIn>', lambda event: on_entry_click(event, e))
    e.bind('<FocusOut>', lambda event: on_focusout(event, e))
    b_update = Button(tk, text="Maj temperature", command=lambda: update_temp(e, room_nb), width=20)

    l.grid(row=row_rank, column=0, sticky=W+N+S, rowspan=2, pady=5)
    e.grid(row=row_rank, column=2, ipady=3.5, sticky=W+N+S, rowspan=2, pady=5)
    b_update.grid(row=row_rank, column=3, columnspan=2, sticky=W+N+S, rowspan=2, pady=5)


def create_sensor_interface(id, style, row_rank):
    """
    Create interface for a sensor
    """
    b = Button(tk,
               text="Capteur {:2}".format(str(id)[1]),
               command=lambda: tracer(id),
               image=IMG, compound="left")
    p = Progressbar(tk, style=style[0], orient="horizontal", length=300, mode="determinate", maximum=100, value=0)
    l = Label(tk, text="", foreground="white", background=style[1], font=("Helvetica", 12), width=4, anchor=CENTER)
    items[id] = [l, p]

    b.grid(row=row_rank, column=0)
    p.grid(row=row_rank, column=2, columnspan=2)
    l.grid(row=row_rank, column=4)


def tracer(id):
    fichier = "capteur" + str(id) + ".txt"
    y = temperature(fichier)
    x = [i for i, _ in enumerate(y)]

    plt.cla()
    plt.plot(x, y)
    plt.title("Salle " + str(id)[0] + ", Capteur " + str(id)[1])
    plt.ylabel("Temperature en degres celsius")

    plt.get_current_fig_manager().window.geometry("600x600+500+0")
    plt.show()


def temperature(fichier):
    """
    Retrieve temperature list in fichier
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, fichier)
    liste = []
    try:
        with open(file_path) as f:
            c = 0
            for line in f:
                liste.append(float(line))
    except IOError:
        pass
    return liste


def refresher(ids):
    new_ids = sorted([int(f.replace('capteur','').replace(".txt",""))
                      for f in os.listdir(os.path.dirname(__file__)) if re.match(r'capteur[0-9]+', f)])

    if ids != new_ids:
        clear_grid()
        add_interfaces(new_ids)
        ids = [i for i in new_ids]

    # loop updating progress bar and value label
    for id in sorted(items.keys()):
        temp_list= temperature("capteur" + str(id) + ".txt")

        if temp_list:
            t = temp_list[-1]
            items[id][LABEL].configure(text=str(t))
            items[id][BAR].configure(value=t)

    tk.after(5000, refresher, ids)


def init(styles):
    """
    Initiate tk window with style list
    """
    tk.title("GUI - BED project")
    tk.resizable(height=False, width=False)
    s = Style()

    for style in styles:
        s.configure(style[0], foreground=style[1], background=style[1], thickness=20)


def add_interfaces(ids):
    old_room_identifier = None
    i=0
    h=0
    for id in ids:
        room_identifier = str(id)[0]
        room_initialized = room_identifier == old_room_identifier
        if not room_initialized:
            old_room_identifier = str(id)[0]
            create_room_interface(str(id)[0], i)
            i += 2
            h += 35

        create_sensor_interface(id, styles[i % len(styles)], i)
        i += 1
        h += 28
    tk.geometry("450x" + str(h))


def clear_grid():
    for child in tk.grid_slaves():
        child.grid_forget()

"""
Main code
"""
styles = [
    ["blue.Horizontal.TProgressbar", "blue"],
    ["green.Horizontal.TProgressbar", "green"],
    ["orange.Horizontal.TProgressbar", "orange"],
    ["purple.Horizontal.TProgressbar", "purple"],
    ["gold3.Horizontal.TProgressbar", "gold3"],
    ["khaki.Horizontal.TProgressbar", "khaki"],
    ["red.Horizontal.TProgressbar", "red"],
    ["cyan.Horizontal.TProgressbar", "cyan"],
    ["pink.Horizontal.TProgressbar", "pink"],
]

global items, tk, LABEL, BAR, IMG, fig, ax
LABEL = 0
BAR = 1
items = dict()
tk = Tk()
IMG = PhotoImage(file="graphe.png")
ids_list = []

init(styles)
refresher(ids_list)
tk.mainloop()
