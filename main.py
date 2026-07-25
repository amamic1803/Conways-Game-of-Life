from abc import ABC, abstractmethod
import os
import sys
import tkinter as tk

import numpy as np
from PIL import Image, ImageTk


def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

class SimulationListener(ABC):
	@abstractmethod
	def on_simulation_update(self) -> None:
		pass

class Simulation:
	def __init__(self):
		self.listeners: set[SimulationListener] = set()
		self.cells: set[tuple[int, int]] = set()

	def add_listener(self, listener: SimulationListener) -> None:
		self.listeners.add(listener)

	def remove_listener(self, listener: SimulationListener) -> None:
		self.listeners.discard(listener)

	def notify_listeners(self) -> None:
		for listener in self.listeners:
			listener.on_simulation_update()

	def step(self) -> None:
		cells_temp: set[tuple[int, int]] = set()
		black_candidates: dict[tuple[int, int], int] = {}
		for i in self.cells:
			num_alive = 0
			for x in range(-1, 2):
				for y in range(-1, 2):
					if x != 0 or y != 0:
						neighbour = (i[0] + x, i[1] + y)
						if neighbour in self.cells:
							num_alive += 1
						else:
							black_candidates[neighbour] = black_candidates.get(neighbour, 0) + 1
			if 2 <= num_alive <= 3:
				cells_temp.add(i)
		for (black_candidate, white_neighbours) in black_candidates.items():
			if white_neighbours == 3:
				cells_temp.add(black_candidate)
		self.cells = cells_temp
		self.notify_listeners()

	def reset(self) -> None:
		self.cells.clear()
		self.notify_listeners()

	def toggle(self, cell: tuple[int, int]) -> None:
		if cell in self.cells:
			self.cells.remove(cell)
		else:
			self.cells.add(cell)
		self.notify_listeners()

class UIToolbar(tk.Frame, SimulationListener):
	def __init__(self, simulation: Simulation, master, **kwargs):
		super().__init__(master, **kwargs)

		self.simulation = simulation
		self.simulation.add_listener(self)
		self.speed: int = 1  # simulation steps per second
		self.running: bool = False
		self.running_id: int = 0  # run id, incremented every run, used to stop old runs

		self.title_lbl = tk.Label(self, anchor="center", text="Conway's Game of Life",
								  font="Helvetica 26 italic", background="#ffffff",
								  foreground="#000000", highlightthickness=0, padx=10)
		self.title_lbl.pack(side="left", fill="y", expand=True)

		self.stats = tk.Frame(self, background="#ffffff", highlightthickness=0)
		self.stats.pack(side="left", fill="y", expand=True)
		self.stats_txt = tk.Label(self.stats, anchor="center", text="CELLS", font="Helvetica 11 bold",
								  foreground="#74e66a", background="#808080", highlightthickness=0, padx=5)
		self.stats_txt.pack(side="top", fill="x", expand=True)
		self.stats_num = tk.Label(self.stats, anchor="center", text="0", font="Helvetica 20 bold",
								  foreground="#ffffff", background="#808080", highlightthickness=0, padx=5)
		self.stats_num.pack(side="top", fill="x", expand=True)

		self.controls = tk.Frame(self, background="#ffffff")
		self.controls.pack(side="left", fill="y", expand=True)
		self.controls.rowconfigure(0, weight=1, uniform="controls")
		self.controls.rowconfigure(1, weight=1, uniform="controls")
		self.controls.columnconfigure(0, weight=1, uniform="controls")
		self.controls.columnconfigure(1, weight=1, uniform="controls")

		self.start_stop_btn = tk.Button(self.controls, anchor="center", text="Start", borderwidth=0,
								 font="Helvetica 11 bold", cursor="hand2",
								 background="#ffffff", activebackground="#ffffff", foreground="#000000",
								 activeforeground="#000000")
		self.start_stop_btn.grid(row=0, column=0, sticky="nsew")
		self.start_stop_btn.bind("<ButtonRelease-1>", lambda _: self.on_start_stop_click())

		self.step_btn = tk.Button(self.controls, anchor="center", text="Step", borderwidth=1,
								font="Helvetica 11 bold", cursor="hand2",
								background="#ffffff", activebackground="#ffffff", foreground="#000000",
								activeforeground="#000000")
		self.step_btn.grid(row=1, column=0, sticky="nsew")
		self.step_btn.bind("<ButtonRelease-1>", lambda _: self.simulation.step())

		self.reset_bt = tk.Button(self.controls, anchor="center", text="Reset", borderwidth=0, font="Helvetica 11 bold",
						   background="#ffffff", activebackground="#ffffff", foreground="red",
						   activeforeground="red", cursor="hand2")
		self.reset_bt.grid(row=1, column=1, sticky="nsew")
		self.reset_bt.bind("<ButtonRelease-1>", lambda _: self.on_reset_click())

		self.speed_frame = tk.Frame(self.controls, background="#ffffff", highlightthickness=0)
		self.speed_frame.grid(row=0, column=1, sticky="nsew")
		self.speed_down_btn = tk.Button(self.speed_frame, text="-", cursor="hand2",
								  anchor="center", borderwidth=0, highlightthickness=0,
								  background="#ffffff", activebackground="#ffffff", font="Helvetica 11")
		self.speed_down_btn.pack(side="left", fill="y", expand=True)
		self.speed_down_btn.bind("<ButtonRelease-1>", lambda _: self.on_speed_change(faster=False))
		self.speed_lbl = tk.Label(self.speed_frame, anchor="center", text=str(self.speed), font="Helvetica 11 bold",
								  foreground="#000000", background="#ffffff", highlightthickness=0)
		self.speed_lbl.pack(side="left", fill="y", expand=True)
		self.speed_up_btn = tk.Button(self.speed_frame, text="+", cursor="hand2",
									  borderwidth=0, highlightthickness=0,
									  background="#ffffff", activebackground="#ffffff", font="Helvetica 11")
		self.speed_up_btn.pack(side="left", fill="y", expand=True)
		self.speed_up_btn.bind("<ButtonRelease-1>", lambda _: self.on_speed_change(faster=True))

	def on_simulation_update(self) -> None:
		self.stats_num.config(text=str(len(self.simulation.cells)))

	def on_speed_change(self, faster):
		if faster:
			self.speed = min(self.speed * 2, 64)
		else:
			self.speed = max(self.speed // 2, 1)
		self.speed_lbl.config(text=str(self.speed))

	def on_start_stop_click(self):
		if self.running:
			self.running = False
			self.running_id += 1
			self.start_stop_btn.config(text="Start")
		else:
			self.running = True
			self.start_stop_btn.config(text="Stop")
			def auto_sim(curr_id):
				if curr_id == self.running_id:
					self.simulation.step()
					self.after(int(round(1000 / self.speed, 0)), lambda send_id=curr_id: auto_sim(send_id))
			auto_sim(self.running_id)

	def on_reset_click(self):
		# if running, stop
		if self.running:
			self.on_start_stop_click()
		self.simulation.reset()

class UICanvas(tk.Canvas, SimulationListener):
	def __init__(self, simulation: Simulation, master, **kwargs):
		super().__init__(master, **kwargs)

		# variables
		self.simulation: Simulation = simulation      # simulation
		self.zoom: int = 25                           # cell dimensions in px
		self.offset_x: int = 0                        # canvas x offset in px
		self.offset_y: int = 0                        # canvas y offset in px
		self.drag_x: int = 0                          # current drag x coordinate
		self.drag_y: int = 0                          # current drag y coordinate
		self._img = None                              # reference to the image to prevent garbage collection
		self.selection: set[tuple[int, int]] = set()  # cells toggled in the current selection

		# listen for state changes in the simulation
		self.simulation.add_listener(self)

		# mouse wheel zoom
		self.bind("<MouseWheel>", self.on_scroll)

		# mouse left button select/drag (cell toggle)
		self.bind("<Button-1>", self.on_select_start)
		self.bind("<B1-Motion>", self.on_select_motion)
		self.bind("<ButtonRelease-1>", self.on_select_stop)

		# mouse right button drag
		self.bind('<Button-3>', self.on_drag_start)
		self.bind('<B3-Motion>', self.on_drag_motion)
		self.bind('<ButtonRelease-3>', self.on_drag_stop)

		# listen for size changes to redraw
		self.bind("<Configure>", self.on_configure)

	def on_simulation_update(self) -> None:
		self.redraw()

	def on_configure(self, _):
		self.redraw()

	def on_drag_start(self, event):
		self.drag_x = event.x
		self.drag_y = event.y
		self.configure(cursor="fleur")

	def on_drag_motion(self, event):
		self.offset_x += self.drag_x - event.x
		self.offset_y += self.drag_y - event.y
		self.drag_x = event.x
		self.drag_y = event.y
		self.redraw()

	def on_drag_stop(self, _):
		self.configure(cursor="arrow")

	def on_select_start(self, event):
		self.selection.clear()
		self.on_select_motion(event)

	def on_select_motion(self, event):
		x = self.offset_x + event.x
		y = self.offset_y + event.y
		cell = (x // self.zoom, y // self.zoom)
		if cell not in self.selection:
			self.selection.add(cell)
			self.simulation.toggle(cell)

	def on_select_stop(self, event):
		self.on_select_motion(event)

	def on_scroll(self, event):
		world_x = (self.offset_x + event.x) / self.zoom
		world_y = (self.offset_y + event.y) / self.zoom
		if event.delta > 0:
			self.zoom = min(75, self.zoom + 1)
		else:
			self.zoom = max(1, self.zoom - 1)
		self.offset_x = int(round(world_x * self.zoom - event.x))
		self.offset_y = int(round(world_y * self.zoom - event.y))
		self.redraw()

	def redraw(self):
		width = self.winfo_width()
		height = self.winfo_height()

		if width <= 1 or height <= 1:
			return

		img_np = np.zeros((height, width, 3), dtype=np.uint8)

		min_x = self.offset_x // self.zoom
		min_y = self.offset_y // self.zoom
		max_x = (self.offset_x + width - 1) // self.zoom
		max_y = (self.offset_y + height - 1) // self.zoom
		for cell_x, cell_y in self.simulation.cells:
			if min_x <= cell_x <= max_x and min_y <= cell_y <= max_y:
				px = cell_x * self.zoom - self.offset_x
				py = cell_y * self.zoom - self.offset_y
				img_np[max(py, 0):py + self.zoom, max(px, 0):px + self.zoom] = [255, 255, 255]

		img_pil = Image.fromarray(img_np)
		img_tk = ImageTk.PhotoImage(img_pil)

		self.create_image(0, 0, image=img_tk, anchor="nw")
		self._img = img_tk

class UI(tk.Frame):
	def __init__(self, simulation: Simulation, master):
		super().__init__(master)

		self.simulation: Simulation = simulation

		self.toolbar = UIToolbar(self.simulation, master=self, background="#ffffff", highlightthickness=0, height=60)
		self.toolbar.pack(side="top", fill="x")

		self.canvas = UICanvas(self.simulation, master=self, highlightthickness=0, background="#000000")
		self.canvas.pack(side="top", fill="both", expand=True)

class App:
	MIN_WIDTH = 800
	MIN_HEIGHT = 450

	def __init__(self):
		simulation = Simulation()

		window = tk.Tk()
		#window.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
		window.geometry(f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}+{(window.winfo_screenwidth() - self.MIN_WIDTH) // 2}+{(window.winfo_screenheight() - self.MIN_HEIGHT) // 2}")
		window.title("Conway's Game of Life")
		window.config(background="#ffffff")
		window.iconbitmap(resource_path("icon.ico"))

		user_interface = UI(simulation, master=window)
		user_interface.place(relx=0, rely=0, relwidth=1, relheight=1)

		window.mainloop()


if __name__ == "__main__":
	App()
