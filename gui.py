#!/usr/bin/python

from Tkinter import *
from ttk import *
import os
import matplotlib.pyplot as plt
# from server import setBaseTemp


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
            # setBaseTemp(value, salle)
        else:
            if temp < 0 or temp > 100:
                print "The temperature must be between 0 and 100"
            else:
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
               command=lambda: matplotlib_tracer(id),
               image=IMG, compound="left")
    p = Progressbar(tk, style=style[0], orient="horizontal", length=300, mode="determinate", maximum=100, value=0)
    l = Label(tk, text="", foreground="white", background=style[1], font=("Helvetica", 12), width=4, anchor=CENTER)
    items[id] = [l, p]

    b.grid(row=row_rank, column=0)
    p.grid(row=row_rank, column=2, columnspan=2)
    l.grid(row=row_rank, column=4)


def tracer(id):
    """
    Draw temperatures history
    """
    fichier = "capteur" + str(id) + ".txt"
    d = 20
    h = w = 500

    tl = Toplevel()
    tl.title(fichier)
    tl.resizable(height=False, width=False)
    c = Canvas(tl, height=h, width=w)
    c.pack()

    xmin, xmax, ymin, ymax = 0, 100, 0, 100
    unx = w / (xmax - xmin)
    uny = h / (ymax - ymin)

    c.create_line((xmin - xmin) * unx + d, (ymax - ymin) * uny - d, (xmax - xmin) * unx - d, (ymax - ymin) * uny - d)
    c.create_line((xmin - xmin) * unx + d, (ymax - ymin) * uny - d, (xmin - xmin) * unx + d, (ymax - ymax) * uny + d)

    for i in range(11):
        c.create_line((0 - xmin) * unx + d, (ymax - 10 * i) * uny + d, (2 - xmin) * unx + d, (ymax - 10 * i) * uny + d)
        c.create_text((-2 - xmin) * unx + d, (ymax - 10 * i) * uny + d, text='%d' % (10 * i))
        c.create_line((10 * i - xmin) * unx + d, (ymax - 10) * uny + d, (10 * i - xmin) * unx + d, (ymax - 8) * uny + d)
        c.create_text((10 * i - xmin) * unx + d, (ymax - 6) * uny + d, text='%d' % i)

    l, _ = temperature(fichier)
    l2 = []
    for i in range(len(l)):
        l2.append([(l[i][0] - xmin) * unx + d, (ymax - l[i][1]) * uny + d])
        c.create_oval(l2[i][0] - 5, l2[i][1] - 5, l2[i][0] + 5, l2[i][1] + 5, fill='blue')

    if len(l2) >= 2:
        c.create_line(l2, fill="red")


def matplotlib_tracer(id):
    fichier = "capteur" + str(id) + ".txt"
    _, y = temperature(fichier)
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
    couple_liste, liste = [], []
    try:
        with open(file_path) as f:
            c = 0
            for line in f:
                liste.append(int(line))
                couple_liste.append([c, int(line)])
                c += 10
    except IOError:
        pass
    return couple_liste, liste


def refresher(ids):
    new_ids = sorted([int(f.replace('capteur','').replace(".txt",""))
                      for f in os.listdir(os.path.dirname(__file__)) if re.match(r'capteur[0-9]+', f)])

    if ids != new_ids:
        clear_grid()
        add_interfaces(new_ids)
        ids = [i for i in new_ids]

    # loop updating progress bar and value label
    for id in sorted(items.keys()):
        temp_list, a = temperature("capteur" + str(id) + ".txt")

        if temp_list:
            t = temp_list[-1][1]
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
    w=0
    for id in ids:
        room_identifier = str(id)[0]
        room_initialized = room_identifier == old_room_identifier
        if not room_initialized:
            old_room_identifier = str(id)[0]
            create_room_interface(str(id)[0], i)
            i += 2
            w += 35

        create_sensor_interface(id, styles[i % len(styles)], i)
        i += 1
        w += 28
    tk.geometry("450x" + str(w))


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
