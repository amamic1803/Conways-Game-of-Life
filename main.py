from abc import ABC, abstractmethod
import os
import sys
import tkinter as tk


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

class UserInterface(tk.Frame):
	class Toolbar(tk.Frame, SimulationListener):
		def __init__(self, simulation: Simulation, master, **kwargs):
			super().__init__(master, **kwargs)

			self.simulation = simulation
			self.simulation.add_listener(self)
			self.speed: int = 1  # simulation steps per second
			self.running: bool = False

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
			self.rowconfigure(0, weight=1)
			self.rowconfigure(1, weight=1)
			self.columnconfigure(0, weight=1)
			self.columnconfigure(1, weight=1)

			self.start_stop_btn = tk.Button(self.controls, anchor="center", text="START", borderwidth=0,
			                         font="Helvetica 11 bold",
			                         background="#ffffff", activebackground="#ffffff", foreground="#000000",
			                         activeforeground="#000000")
			self.start_stop_btn.grid(row=0, column=0, sticky="nsew")
			self.start_stop_btn.bind("<ButtonRelease-1>", lambda _: self.on_start_stop_click())

			self.step_btn = tk.Button(self.controls, anchor="center", text="STEP", borderwidth=1,
			                        font="Helvetica 11 bold",
			                        background="#ffffff", activebackground="#ffffff", foreground="#000000",
			                        activeforeground="#000000")
			self.step_btn.grid(row=1, column=0, sticky="nsew")
			self.step_btn.bind("<ButtonRelease-1>", lambda _: self.simulation.step())

			self.reset_bt = tk.Button(self.controls, anchor="center", text="RESET", borderwidth=0, font="Helvetica 11 bold",
			                   background="#ffffff", activebackground="#ffffff", foreground="red",
			                   activeforeground="red")
			self.reset_bt.grid(row=1, column=1, sticky="nsew")
			self.reset_bt.bind("<ButtonRelease-1>", lambda _: self.on_reset_click())

			self.speed_frame = tk.Frame(self.controls, background="#ffffff", highlightthickness=0)
			self.speed_frame.grid(row=0, column=1, sticky="nsew")
			self.speed_down_btn = tk.Button(self.speed_frame, text="-",
			                          anchor="center", borderwidth=0, highlightthickness=0,
			                          background="#ffffff", activebackground="#ffffff", font="Helvetica 11")
			self.speed_down_btn.pack(side="left", fill="y", expand=True)
			self.speed_down_btn.bind("<ButtonRelease-1>", lambda _: self.on_speed_change(faster=False))
			self.speed_lbl = tk.Label(self.speed_frame, anchor="center", text=str(self.speed), font="Helvetica 11 bold",
			                          foreground="#000000", background="#ffffff", highlightthickness=0)
			self.speed_lbl.pack(side="left", fill="y", expand=True)
			self.speed_up_btn = tk.Button(self.speed_frame, text="+",
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
				self.start_stop_btn.config(text="START")
				self.start_stop_btn.config(foreground="#000000", activeforeground="#000000")
				self.step_btn.config(foreground="#000000", activeforeground="#000000")
			else:
				self.running = True
				self.start_stop_btn.config(text="STOP")
				def auto_sim(curr_num):
					if curr_num == sim_num:
						if calc_gen():
							root.after(int(round(sim_speed, 0)), lambda send_num=curr_num: auto_sim(send_num))
						else:
							stop_sim_click()
				self.start_stop_btn.config(foreground="#808080", activeforeground="#808080")
				self.step_btn.config(foreground="#808080", activeforeground="#808080")
				self.auto_sim(self.simulation.generation)

		def on_reset_click(self):
			# if running, stop
			if self.running:
				self.on_start_stop_click()
			self.simulation.reset()

	class Canvas(tk.Canvas, SimulationListener):
		def __init__(self, simulation: Simulation, master, **kwargs):
			super().__init__(master, **kwargs)
			self.bind("<MouseWheel>", lambda event: print(event))

			# zoom_in_img = tk.PhotoImage(file=self.resource_path("resources/zoom-in.png"))
			# zoom_out_img = tk.PhotoImage(file=self.resource_path("resources/zoom-out.png"))
			# zoom_in_btn = tk.Button(self.root, image=zoom_in_img,
			#                     borderwidth=0, highlightthickness=0,
			#                     background="#ffffff", activebackground="#ffffff")
			# zoom_in_btn.place(x=535, y=0, height=40, width=40)
			# zoom_out_btn = tk.Button(self.root, image=zoom_out_img,
			#                      anchor="center", borderwidth=0, highlightthickness=0,
			#                      background="#ffffff", activebackground="#ffffff")
			# zoom_out_btn.place(x=535, y=40, height=40, width=40)

			# zoom_in_btn.bind("<ButtonRelease-1>", lambda event: change_zoom(False))
			# zoom_out_btn.bind("<ButtonRelease-1>", lambda event: change_zoom(True))

		def on_simulation_update(self) -> None:
			for i in range(field_sizes[current_field][1]):
				for j in range(field_sizes[current_field][0]):
					if (i + vertical_move, j + horizontal_move) in kocke:
						cnv.itemconfig(kocke_gui[i][j], fill="#ffffff")
					else:
						cnv.itemconfig(kocke_gui[i][j], fill="#000000")

		def draw_zoom(self):
			self.canvas.delete("all")
			self.tiles.clear()
			self.vertical_lines.clear()
			self.horizontal_lines.clear()

			# horizontal lines
			horizontal_loc = 0
			while horizontal_loc < self.canvas.winfo_height():
				self.horizontal_lines.append(
					self.canvas.create_line(0, horizontal_loc, self.canvas.winfo_width(), horizontal_loc,
					                        fill="#808080"))
				horizontal_loc += self.tile_size + 1
			self.horizontal_lines.append(
				self.canvas.create_line(0, horizontal_loc, self.canvas.winfo_width(), horizontal_loc, fill="#808080"))

			# vertical lines
			vertical_loc = 0
			while vertical_loc < self.canvas.winfo_width():
				self.vertical_lines.append(
					self.canvas.create_line(vertical_loc, 0, vertical_loc, self.canvas.winfo_height(), fill="#808080"))
				vertical_loc += self.tile_size + 1
			self.vertical_lines.append(
				self.canvas.create_line(vertical_loc, 0, vertical_loc, self.canvas.winfo_height(), fill="#808080"))

			for i in range(field_sizes[current_field][1]):
				red_gui = []
				for j in range(field_sizes[current_field][0]):
					red_gui.append(cnv.create_rectangle(j * (field_sizes[current_field][2] + 1),
					                                    i * (field_sizes[current_field][2] + 1) + 1,
					                                    j * (field_sizes[current_field][2] + 1) +
					                                    field_sizes[current_field][2],
					                                    i * (field_sizes[current_field][2] + 1) +
					                                    field_sizes[current_field][2] + 1, fill="#000000", width=0))
				kocke_gui.append(red_gui)

			if old_zoom is not None:
				horizontal_move += (field_sizes[old_zoom][0] - field_sizes[current_field][0]) // 2
				vertical_move += (field_sizes[old_zoom][1] - field_sizes[current_field][1]) // 2
				if old_zoom != current_field and old_zoom == 0:
					vertical_move += 1
			update_gui()

		def change_zoom(self, out):
			old = current_field
			if out:
				if current_field != 2:
					current_field += 1
			else:
				if current_field != 0:
					current_field -= 1
			draw_current_zoom(old)

		def mis_listen(self, event=None):
			if not started:
				if event.x % (field_sizes[current_field][2] + 1) <= (field_sizes[current_field][2] - 1) and (
						event.y - 1) % (field_sizes[current_field][2] + 1) <= (field_sizes[current_field][2] - 1):
					if ((event.y - 1) // (field_sizes[current_field][2] + 1) + vertical_move,
					    event.x // (field_sizes[current_field][2] + 1) + horizontal_move) in kocke:
						cnv.itemconfig(kocke_gui[(event.y - 1) // (field_sizes[current_field][2] + 1)][
										   event.x // (field_sizes[current_field][2] + 1)], fill="#000000")
						kocke.remove(((event.y - 1) // (field_sizes[current_field][2] + 1) + vertical_move,
						              event.x // (field_sizes[current_field][2] + 1) + horizontal_move))
					else:
						cnv.itemconfig(kocke_gui[(event.y - 1) // (field_sizes[current_field][2] + 1)][
										   event.x // (field_sizes[current_field][2] + 1)], fill="#ffffff")
						kocke.add(((event.y - 1) // (field_sizes[current_field][2] + 1) + vertical_move,
						           event.x // (field_sizes[current_field][2] + 1) + horizontal_move))
				updt_br_cell()

	def __init__(self, simulation: Simulation, master):
		super().__init__(master)

		self.simulation: Simulation = simulation

		self.toolbar = UserInterface.Toolbar(self.simulation, master=self, background="#ffffff", highlightthickness=0, height=60)
		self.toolbar.pack(side="top", fill="x")

		self.canvas = UserInterface.Canvas(self.simulation, master=self, highlightthickness=0, background="#000000")
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

		user_interface = UserInterface(simulation, master=window)
		user_interface.place(relx=0, rely=0, relwidth=1, relheight=1)

		window.mainloop()


if __name__ == "__main__":
	App()
