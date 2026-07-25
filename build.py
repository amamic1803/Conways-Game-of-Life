import os
import random
import shutil
import sys

import PyInstaller.__main__


def build(name, console, onefile, uac_admin, icon, files, folders):
	work_path = "build"
	while os.path.isdir(work_path):
		work_path = f"build_{random.randint(1, 1_000_000_000)}"
	work_path = os.path.join(os.path.abspath("."), work_path)

	result_path = os.path.abspath(".")

	if os.path.isfile(os.path.join(result_path, f"{name}.exe")):
		os.remove(os.path.join(result_path, f"{name}.exe"))

	run_list = ['main.py',
	            '--noconfirm',
	            '--clean',
	            '--name', name,
	            '--workpath', work_path,
	            '--specpath', work_path,
	            '--distpath', result_path]

	if console:
		run_list.append("--console")
	else:
		run_list.append("--noconsole")

	if onefile:
		run_list.append("--onefile")
	else:
		run_list.append("--onedir")

	if uac_admin:
		run_list.append("--uac-admin")

	if icon != "":
		icon_path = os.path.join(os.path.abspath("."), icon)
		if not os.path.isfile(icon_path):
			raise Exception("Invalid icon!")
		else:
			run_list.extend(('--icon', icon_path))

	for file in files:
		if os.path.isfile(os.path.join(os.path.abspath("."), file)):
			dest_dir = os.path.dirname(file)
			if dest_dir == "":
				dest_dir = "."
			run_list.extend(('--add-data', f'{os.path.join(os.path.abspath("."), file)}{os.pathsep}{dest_dir}'))
		else:
			raise Exception("Invalid file!")

	for folder in folders:
		if os.path.isdir(folder):
			for walk in os.walk(folder, followlinks=False):
				for file in walk[2]:
					if os.path.isfile(os.path.join(walk[0], file)):
						dest_dir = os.path.dirname(os.path.join(walk[0], file))
						if dest_dir == "":
							dest_dir = "."
						run_list.extend(('--add-data', f'{os.path.join(os.path.abspath("."), os.path.join(walk[0], file))}{os.pathsep}{dest_dir}'))
					else:
						raise Exception("Invalid folder!")
		else:
			raise Exception("Invalid folder!")

	PyInstaller.__main__.run(run_list)
	shutil.rmtree(path=work_path, ignore_errors=True)

def main():
	name = "Conway's Game of Life"
	version = "11.0.0"

	console = False
	onefile = True
	uac_admin = False
	icon = "resources/icon.ico"

	files = []
	folders = ["resources"]

	if len(sys.argv) == 2:
		if sys.argv[1] == "--version":
			print(version)
		elif sys.argv[1] == "--name":
			print(name)
	else:
		name = f"{name}-v{version}"
		if os.path.isfile(os.path.join(os.path.abspath("."), f"{name}.exe")):
			os.remove(os.path.join(os.path.abspath("."), f"{name}.exe"))
		internal_name = "build_binary"
		build(internal_name, console, onefile, uac_admin, icon, files, folders)
		os.rename(os.path.join(os.path.abspath("."), f"{internal_name}.exe"), os.path.join(os.path.abspath("."), name + ".exe"))


if __name__ == '__main__':
	main()
