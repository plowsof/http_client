import sys
import os
from shutil import copyfile
import random
import time
import threading
import platform
import configparser
from zipfile import ZipFile

if getattr(sys, 'frozen', False):
	application_path = os.path.dirname(sys.executable)
	os.chdir(application_path)

print('CWD: ' + os.getcwd())
cl_version = "20210206"
print("Version: %s" % cl_version)
dir_path = os.getcwd()

loc_mm_http = os.path.join(dir_path,"user/sofplus/addons/http.func")
__ftpbase__ = "http://sofmaps.byethost8.com/base/"
__cookie_name__ = "__test"
__windowname__ = "SoF"
__cookie_val__ = "0b3d8f36d546ae983b6d491748a0e7b0"
__temp_path__ = "."
__dbgsnd__ = 1

__gitbase__ = "https://github.com/plowsof/sof1maps/raw/main/"

read_config = configparser.ConfigParser()
try:
	read_config.read("http-sof.ini")
	__windowname__ = read_config.get("Settings", "process_name")
	__dbgsnd__ = read_config.get("Settings", "debug_sounds")
	__ftpbase__ = read_config.get("Settings", "ftp_base")
	__cookie_val__ = read_config.get("Settings", "cookie_val")
	__cookie_name__ = read_config.get("Settings", "cookie_name")
	pass
except:
	pass 

base_url = __ftpbase__
sp_sounds = base_url + "sp_sounds.txt"
cookies = {__cookie_name__: __cookie_val__}
spData = os.path.join(".","user/sofplus/data/")

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import ntpath
import requests
import glob

def on_created(event):
	global cookies
	global base_url, __gitbase__
	#on-created does not mean its finished being created..

	print(f"hey buddy, {event.src_path} has been created")
	fname = ntpath.basename(event.src_path)
	if "http_tmp" in fname:
		while True:
			ctime = os.path.getctime(event.src_path)
			mtime = os.path.getmtime(event.src_path)
			diff = mtime - ctime
			time.sleep(0.1)
			ctime = os.path.getctime(event.src_path)
			mtime = os.path.getmtime(event.src_path)
			newdiff = mtime - ctime
			if diff == newdiff:
				#after 0.1s nothing changed.. ok
				break
		with open(event.src_path, "r") as f:
			x = f.read().splitlines()
		filename = x[1].split()[2].replace("\"","")
		checkFtp(filename,0)

	#get Zip from github
	elif "http_mapname" in fname:
		print("mapname file")
		with open(event.src_path, "r") as f:
			x = f.readlines()
		mapname = x[1].split()[2].replace("\"","").lower()
		url = __gitbase__ + mapname + ".zip"
		print(url)
		if download_url(url,"http_tmp_mapfiles.zip"):
			#trigger disconnect via SoFplus find file
			with open("user/sofplus/data/http_flist_exists", "w+") as f:
				f.write("AeO<3")
			#extract/install files
			with ZipFile('http_tmp_mapfiles.zip', 'r') as zipObj:
			# Extract all the contents of zip file in different directory
				zipObj.extractall('user')
			#trigger reconnect via SoFplus find file
			with open("user/sofplus/data/http_flist_finished", "w+") as f:
				f.write("AeO<3")

	elif fname == "http_done":
		cleanup()

def download_url(url, save_path, chunk_size=128):
	r = requests.get(url)
	if r.status_code != 404:
		with open(save_path, 'wb') as fd:
			for chunk in r.iter_content(chunk_size=chunk_size):
				fd.write(chunk)
		return True
	else:
		print(r)
		print("FALSE error")
		return False

def checkFtp(fname,from_vault):
	global base_url
	global cookies
	url = base_url + fname.lower()
	#myAddTextWrapper(f'http_print Checking/Downloading file @ {url}...\n',1)
	saveas = os.path.join("./user/",fname.lower())
	print(f"saving the file to: {saveas}")
	# Download the file from `url` and save it locally under `file_name`:
	#myAddTextWrapper("set http_busy 1\n",1)
	r = requests.get(url, cookies=cookies)
	if r.status_code != 404:
		with open("user/sofplus/data/http_flist_exists", "w+") as f:
			f.write("AeO<3")
		if not os.path.exists(os.path.dirname(saveas)):
			try:
				os.makedirs(os.path.dirname(saveas))
			except Exception as e: 
				raise e
		with open(saveas, 'wb+') as w:
			for chunk in r.iter_content(chunk_size=512):
				if chunk:
					w.write(chunk)
		with open("user/sofplus/data/http_flist_finished", "w+") as f:
			f.write("AeO<3")

def cleanup():
	global spData
	print("glib glob blobby")
	for x in glob.glob(spData + "http_*"):
		os.remove(x)
		#print(x)
	for x in glob.glob("user/sofplus/addons/http_*"):
		os.remove(x)

def get_sp_sounds():
	#security?
	#check if dir exists /sofree/
	global sp_sounds
	global cookies
	#myAddTextWrapper("set http_busy 1\n",1)
	r = requests.get(sp_sounds, cookies=cookies)
	if r.status_code != 404:
		#myAddTextWrapper("set http_busy 0\n",1)
		for line in r.iter_lines():
			if line: 
				not_exec = line
				fpath = os.path.join('.',str(not_exec)[2:-1])
				if os.path.isfile(fpath):
					print(f"we have {fpath}")
				else:
					print(f"we need to dl {fpath}")
					checkFtp(str(not_exec)[7:-1],1)

			
def start_observer():
	print("hello world im the observer")
	global spData
	cleanup()
	#patterns not working for me
	patterns = "*"
	ignore_patterns = ""
	ignore_directories = True
	case_sensitive = True
	my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

	#my_event_handler.on_modified = on_modified
	my_event_handler.on_created = on_created

	path = spData
	go_recursively = True
	my_observer = Observer()
	my_observer.schedule(my_event_handler, path, recursive=go_recursively)

	my_observer.start()
	#myAddTextWrapper("http_print Activated!\n",1)
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		my_observer.stop()
		my_observer.join()

def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		#print(sys._MEIPASS)
		base_path = sys._MEIPASS
	except Exception:
		relative_path = "user/" + str(relative_path)
		base_path = os.getcwd()
	return os.path.join(base_path, relative_path)

func_http = "http.func"
loc_mm_inject_http = "str"
begin_wav = "str"
end_wav = "str"
ini_debug = "str"


def main():
	cleanup()
	#copy http.func to addons if we dont have it
	check_http()
	get_sp_sounds()
	#start observer thread
	x = threading.Thread(target=start_observer)
	x.start()

def check_http():
	global loc_mm_http
	global loc_mm_inject_http
	global func_http

	#check if http.func exists
	while True:
		if os.path.isfile(loc_mm_http):
			break
			pass
		else:
			print("SoFplus http func not found. Copying")
			try:
				copyfile(loc_mm_inject_http, loc_mm_http)
				pass
			except Exception as e:
				raise e
				break

def mayhem(tempDir,dbgsnd):
	global loc_mm_inject_http
	loc_mm_inject_http = os.path.join(tempDir,"http.func")

	main()

if __name__ == '__main__':
	#print('this script must be injected')
	ini_debug = __dbgsnd__
	mayhem(__temp_path__,ini_debug)
elif __name__ == '__mayhem__':
	ini_debug = __dbgsnd__
	mayhem(__temp_path__,ini_debug)
