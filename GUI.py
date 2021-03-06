__author__ = 'boh01'

from threading import Thread
import os
import Tkinter as tk
import ttk
import math
import csv

import TimerGUI


class Window(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.window = tk.Tk()  # Init
        self.window.geometry("700x550+200+100")
        self.window.minsize(300, 300)
        self.window.title("Time Tracker - Ben Holleran June 2015")
        self.window.protocol("WM_DELETE_WINDOW", self.onQuit)
        self.window.bind("<Configure>", self.resize)

        # Variables

        self.graph_style = 1
        self.timer = 5 * 60
        self.jobs = []


        # Menu bar
        self.toolbar = tk.Menu(self.window)

        self.filemenu = tk.Menu(self.toolbar, tearoff=0)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Poll", command=self.runPoll)
        self.filemenu.add_command(label="Exit", command=self.toolbar.quit)
        self.toolbar.add_cascade(label="File", menu=self.filemenu)
        self.toolbar.add_command(label="Poll", command=self.runPoll)
        self.toolbar.add_command(label="Set Timer", command=self.setTimer)
        self.toolbar.add_command(label="Refresh Graph", command=self.custom_graph)
        self.toolbar.add_command(label="Refresh Full Graph", command=self.draw_graph)
        self.toolbar.add_command(label="Quit", command=self.window.quit)
        self.window.config(menu=self.toolbar)


        # Window
        self.nb = ttk.Notebook(self.window)
        self.nb.enable_traversal()
        self.graph_frame = ttk.Frame(self.nb, name='graph')
        self.graph_canvas = tk.Canvas(self.graph_frame)
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)
        self.time_frame = ttk.Frame(self.nb, name='time')
        self.nb.add(self.graph_frame, text="Graph")
        self.nb.add(self.time_frame, text="Time")
        self.nb.pack(fill=tk.BOTH, expand=True, padx=2, pady=3)

        self.graph_canvas.pack()

    def onQuit(self):
        print "User aborted, quitting."
        # self.RMAThread.interrupt_main()
        # self.VisThread.interrupt_main()
        self.window.destroy()
        os._exit(1)

    def runPoll(self):
        t = TimerGUI.TimeKeeper()
        while len(self.jobs):
            job = self.jobs.pop()
            self.window.after_cancel(job)
        if self.timer < 1:
            self.timer = 1
        self.jobs.append(self.window.after(int(self.timer * 1000), self.runPoll))
        self.resize()
        t.run()
        print "Here"

    def setTimer(self):
        tmp_pop = popupWindow(self.window, self)
        self.window.wait_window(tmp_pop.top)

    def run(self):
        self.jobs.append(self.window.after(0, self.runPoll))

    def resize(self, event=None):
        if self.graph_style == 1:
            self.custom_graph()
        else:
            self.draw_graph()

    def custom_graph(self):
        self.graph_style = 1
        self.draw_graph(["Ben"])

    def draw_graph(self, disable=None, enable=None):
        if not disable:
            self.graph_style = 0
        self.graph_canvas.delete("all")

        self.graph_frame.update()
        size = (self.graph_frame.winfo_width(), self.graph_frame.winfo_height())
        max_size = max(size)
        min_size = min(size)

        def pluck(iterable, key, value):
            for index, item in enumerate(iterable):
                if item[key] == value:
                    return index
            return None

        def color(a, b=None):
            import random

            random.seed(a)
            x = [random.random(), random.random(), random.random()]
            if b:
                random.seed(b)
                y = [random.random(), random.random(), random.random()]
            else:
                y = [0, 0, 0]
            c = "#"
            for i, n in enumerate(x):
                number = int((x[i] * 3600) + (y[i] * 400))
                c += hex(number)[2:].rjust(3, "0")
            return c

        home_dir = os.path.join(os.getenv("APPDATA"), "Timekeeper")
        log_filename = os.path.join(home_dir, "log.csv")
        config_filename = os.path.join(home_dir, "config.cfg")
        log_file = open(log_filename, "rb")
        config_file = open(log_filename, "rb")
        raw_data = csv.reader(log_file)
        config_data = csv.reader(config_file)
        raw_entries = []
        for entry in raw_data:
            raw_entries.append(entry)


        ##
        events = []
        for index, entry in enumerate(raw_entries):
            duration = 0
            try:
                duration = float(entry[3]) - float(raw_entries[index - 1][3])
            except IndexError:
                pass
            if duration > 0 and duration < 3600 * 5:  # 5 hours
                event = {}
                event["date"] = str(entry[0])
                event["category"] = str(entry[1])
                event["task"] = str(entry[2])
                event["time"] = str(entry[3])
                event["duration"] = duration
                events.append(event)

        categories = {}
        for event in events:
            if event["category"] not in categories:
                categories[event["category"]] = event["duration"]
            else:
                categories[event["category"]] += event["duration"]

        if disable:
            for category in disable:
                del categories[category]

        if enable:
            for category in categories.keys():
                if category not in enable:
                    del categories[category]

        sorted_categories = sorted(categories.items(), key=lambda x: x[1])

        tasks = {}
        for event in events:
            if event["category"] not in tasks:
                tasks[event["category"]] = {}
            if event["task"] not in tasks[event["category"]]:
                tasks[event["category"]][event["task"]] = event["duration"]
            else:
                tasks[event["category"]][event["task"]] += event["duration"]

        sorted_tasks = []
        for category in reversed(sorted_categories):
            sorted_tasks.append((category, sorted(tasks[category[0]].items(), key=lambda x: x[1], reverse=True)))

        total_time = 0
        for category in sorted_categories:
            total_time += category[1]

        time_per_degree = total_time / 360.0

        last_slice = 90

        center = (size[0] / 2.0, size[1] / 2.0)
        task_corners = ((center[0]- (min_size/2.0)+25,center[1]- (min_size/2.0)+25),
                        (center[0]+ (min_size/2.0)-25,center[1]+ (min_size/2.0)-25))
        self.graph_canvas.create_rectangle(0,0,size[0], size[1])
        for category in sorted_tasks:
            for task in category[1]:
                bit = - task[1] / time_per_degree
                #bit = min(bit, -.3)
                if bit < -.5:
                    self.graph_canvas.create_arc(task_corners[0][0], task_corners[0][1], task_corners[1][0], task_corners[1][1],
                                             style=tk.PIESLICE, fill=color(category[0][0], task[0]), start=last_slice,
                                             extent=bit)
                    if bit < -10:
                        self.graph_canvas.create_text(center[0] + (math.cos(-math.radians((last_slice + (bit / 2.0)))) * min_size/3.0),
                                                      center[1] + (math.sin(-math.radians((last_slice + (bit / 2.0)))) * min_size/3.0),
                                                      text=task[0])
                    else:
                        self.graph_canvas.create_text(center[0] + (math.cos(-math.radians((last_slice + (bit / 2.0)))) * min_size/2.1),
                                                      center[1] + (math.sin(-math.radians((last_slice + (bit / 2.0)))) * min_size/2.1),
                                                      text=task[0])
                last_slice += bit

        last_slice = 90

        task_corners = ((center[0]- (min_size/4.0),center[1]- (min_size/4.0)),
                        (center[0]+ (min_size/4.0),center[1]+ (min_size/4.0)))

        for category in sorted_categories:
            bit = category[1] / time_per_degree
            if bit > .5:
                self.graph_canvas.create_arc(task_corners[0][0], task_corners[0][1], task_corners[1][0], task_corners[1][1],
                                         style=tk.PIESLICE, fill=color(category[0]), start=last_slice, extent=bit)
                if bit > 20:
                    self.graph_canvas.create_text(center[0] + (math.cos(-math.radians((last_slice + (bit / 2.0)))) * min_size/8.0),
                                                  center[1] + (math.sin(-math.radians((last_slice + (bit / 2.0)))) * min_size/8.0),
                                                  text=category[0])
                else:
                    self.graph_canvas.create_text(center[0] + (math.cos(-math.radians((last_slice + (bit / 2.0)))) * min_size/3.8),
                                                  center[1] + (math.sin(-math.radians((last_slice + (bit / 2.0)))) * min_size/3.8),
                                                  text=category[0])
            last_slice += bit


class popupWindow(object):
    def __init__(self, master, window):
        self.parent = window
        top = self.top = tk.Toplevel(master)
        self.l = tk.Label(top, text="Time in minutes between polls:")
        self.l.pack()
        self.l2 = tk.Label(top, text="")
        self.l2.pack()
        self.e = tk.Entry(top)
        self.e.pack()
        self.b = tk.Button(top, text='Apply', command=self.cleanup)
        self.b.pack()
        self.e.bind('<Return>', self.cleanup)
        self.e.focus()
        top.lift()

    def cleanup(self, event=None):
        self.value = self.e.get()
        try:
            self.value = float(self.value)
        except ValueError:
            self.value = 5 * 60
            self.l2.config(text="Value cannot be converted to a number. Try again")
            return
        self.parent.timer = self.value * 60.0
        self.top.destroy()


a = Window()
a.start()
a.window.mainloop()
