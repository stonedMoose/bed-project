#!/usr/bin/python

from Tkinter import *
from ttk import *
import os


def mock_temp_command(entry):
    """
    Mock server command to update temperatues
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
            print "Sending message to update temp:", entry.get()
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


def create_sensor_interface(id, style, sensor_rank):
    """
    Create interface for a sensor
    """
    b = Button(tk, text="Capteur {:2d}".format(id), command=lambda: tracer("capteur" + str(id) + ".txt"), image=IMG, compound="left")
    spacer = Label(tk, text="  ")
    spacer1 = Label(tk, text="  ")
    p = Progressbar(tk, style=style[0], orient="horizontal", length=300, mode="determinate", maximum=100, value=0)
    l = Label(tk, text="", foreground="white", background=style[1], font=("Helvetica", 12), width=4, anchor=CENTER)
    e = Entry(tk)
    b_update = Button(tk, text="Maj temperature", command=lambda: mock_temp_command(e))

    # configure entry input
    e.insert(0, 'Entrez une temperature')
    e.config(foreground='grey')
    e.bind('<FocusIn>', lambda event: on_entry_click(event, e))
    e.bind('<FocusOut>', lambda event: on_focusout(event, e))

    items[id] = [l, p]

    b.grid(row=sensor_rank, column=0)
    spacer.grid(row=sensor_rank, column=1)
    p.grid(row=sensor_rank, column=2)
    l.grid(row=sensor_rank, column=3)
    spacer1.grid(row=sensor_rank, column=4)
    e.grid(row=sensor_rank, column=5, ipady=3.5)
    b_update.grid(row=sensor_rank, column=6)


def tracer(fichier):
    """
    Draw temperatures history
    """
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
        c.create_text((10 * i - xmin) * unx + d, (ymax - 6) * uny + d, text='%d' % (i))

    l = temperature(fichier)
    l2 = []
    for i in range(len(l)):
        l2.append([(l[i][0] - xmin) * unx + d, (ymax - l[i][1]) * uny + d])
        c.create_oval(l2[i][0] - 5, l2[i][1] - 5, l2[i][0] + 5, l2[i][1] + 5, fill='blue')

    if len(l2) >= 2:
        c.create_line(l2, fill="red")


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
                liste.append([c, int(line)])
                c += 10
    except IOError:
        pass
    return liste


def refresher(ids):
    new_ids = sorted([int(f.replace('capteur','').replace(".txt",""))
                      for f in os.listdir(os.path.dirname(__file__)) if re.match(r'capteur[0-9]+', f)])

    if ids != new_ids:
        print 'refresh'
        clear_grid()
        add_sensors_interfaces(new_ids)
        ids = [i for i in new_ids]
        tk.geometry("750x" + str(len(ids)*28))

    # loop updating progress bar and value label
    for id in sorted(items.keys()):
        temp_list = temperature("capteur" + str(id) + ".txt")
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
    tk.geometry("750x28")
    s = Style()

    for style in styles:
        s.configure(style[0], foreground=style[1], background=style[1], thickness=20)


def add_sensors_interfaces(ids):
    for i, id in enumerate(ids):
        create_sensor_interface(id, styles[i % len(styles)], i)


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

global items, tk, LABEL, BAR, IMG
LABEL = 0
BAR = 1
items = dict()
tk = Tk()
IMG = PhotoImage(file="graphe.png")
ids_list = []

init(styles)
refresher(ids_list)
tk.mainloop()
