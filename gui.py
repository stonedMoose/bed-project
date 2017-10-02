from tkinter import *
from tkinter.ttk import *

fen = Tk()
fen.geometry("500x500")

'''frame = Frame(fen)
frame.grid()'''

s = Style()
#s.theme_use('calm')


s.configure("blue.Vertical.TProgressbar", foreground='blue', background='blue', thickness=30)
p=Progressbar(fen, style="blue.Vertical.TProgressbar", orient="vertical", length=300, mode="determinate", maximum=100, value=14)
#Progressbar(frame, style="red.Vertical.TProgressbar", orient="vertical", length=300, mode="determinate", maximum=4, value=1).grid(row=1, column=1)


s.configure("yellow.Vertical.TProgressbar", foreground='yellow', background='yellow', thickness=30)
p2=Progressbar(fen, style="yellow.Vertical.TProgressbar", orient="vertical", length=300, mode="determinate", maximum=100, value=43)
#Progressbar(frame, style="green.Vertical.TProgressbar", orient="vertical", length=300, mode="determinate", maximum=4, value=3).grid(row=1, column=15)

lbl=Label(fen, text="T1", foreground="white", background="blue", width=4, anchor=CENTER)

lbl2=Label(fen, text="T2", foreground="white", background="yellow", width=4, anchor=CENTER)

lbcon=Label(fen, text="Connection:", width=10, anchor=CENTER)
lbstatus=Label(fen, background="GREEN", width=2, anchor=CENTER)

lbcon.place(x=30, y=30)
lbstatus.place(x=120, y=30)

lbl.place(x=30, y=70)
lbl2.place(x=90, y=70)

p.place(x=30, y=90)
p2.place(x=90, y=90)

mainloop()
