import sys
import os
import shutil
import random
import time
import threading
import platform
import configparser
from zipfile import ZipFile
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import ntpath
import requests
import glob
import win32gui 
import win32con


from tqdm import tqdm

'''
if getattr(sys, 'frozen', False):
	application_path = os.path.dirname(sys.executable)
	os.chdir(application_path)
'''
__http_func__ = os.path.join(os.getcwd(),"http-client","exe.win32-3.8","http.func")
#path_parent = os.path.dirname(os.getcwd())
#path_parent = os.path.dirname(path_parent)
#os.chdir(path_parent)
#print(os.getcwd())

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
		tmpfile = f"user/maps/{mapname}.tmp"
		mapdir = f"user/maps/{mapname}.bsp"
		if os.path.isfile(tmpfile):
			os.remove(tmpfile)
		url = __gitbase__ + mapname + ".zip"
		print(url)
		if download(url,"http_tmp_mapfiles.zip"):
			#we can check if mapname.tmp exists after extraction
			#then we dont need to disconnect :)
			#extract/install files
			with ZipFile('http_tmp_mapfiles.zip', 'r') as zipObj:
			# Extract all the contents of zip file in different directory
				zipObj.extractall('user')
			#extraction finished. check if we need to reconnect
			if os.path.isfile(tmpfile):
				print("a temp file exists")
				#if modified time of tmpfile > mapname.bsp
				#then its another filetype e.g. mapname.eal + mapname.tmp
				timetmp = os.path.getmtime(tmpfile)
				timebsp = os.path.getmtime(mapdir)
				print(f"tmp: {timetmp} bsp: {timebsp}")
				if timetmp < timebsp:
					#trigger disconnect via SoFplus find file
					with open("user/sofplus/data/http_flist_exists", "w+") as f:
						f.write("AeO<3")
					time.sleep(0.260)
					#trigger reconnect via SoFplus find file
					with open("user/sofplus/data/http_flist_finished", "w+") as f:
						f.write("AeO<3")
					os.remove(tmpfile)
			else:
				print("no tmp file was created")
			

	elif fname == "http_done":
		cleanup()

def download(url: str, fname: str):
	resp = requests.get(url, stream=True)
	fdesc = url.split("/")[-1]
	if resp.status_code != 404:
		total = int(resp.headers.get('content-length', 0))
		with open(fname, 'wb') as file, tqdm(
			desc=fdesc,
			total=total,
			unit='iB',
			unit_scale=True,
			unit_divisor=1024,
		) as bar:
			for data in resp.iter_content(chunk_size=1024):
				size = file.write(data)
				bar.update(size)
		return True
	else:
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
	while True:
		try:
			for x in glob.glob(spData + "http_*"):
				os.remove(x)
			for x in glob.glob("user/sofplus/addons/http_*"):
				os.remove(x)
			break
			pass
		except Exception as e:
			print(e)
		time.sleep(0.1)


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

def sofWinEnumHandler( hwnd, ctx ):
	global sofId
	#C:\Users\Human\Desktop\Raven\SOF PLATINUM\http-client\exe.win32-3.8\SoF-http-cl.exe
	#if win32gui.IsWindowVisible( hwnd ):
	#print (hex(hwnd), win32gui.GetWindowText( hwnd ))
	fname = ntpath.basename(win32gui.GetWindowText( hwnd ))
	if fname == "SoF-http-cl.exe":
		sofId = hwnd
		win32gui.ShowWindow(sofId, win32con.SW_MINIMIZE)

def searchForSoFWindow():
	sofId = ""
	while sofId == "":
		print("cant find SoF,,, ill keep looking")
		try:
			win32gui.EnumWindows( sofWinEnumHandler, None )
		except Exception as e:
			print(e)
			if e == KeyboardInterrupt:
				
				raise
			pass
		if sofId == "":
			break
			#time.sleep(2)
	print("Found the SoF window")
	return sofId

def main():
	cleanup()
	#copy http.func to addons if we dont have it
	check_http()
	#get_sp_sounds()
	#start observer thread
	x = threading.Thread(target=start_observer)
	x.start()
	#minimise the terminal 
	searchForSoFWindow()

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
			print("SoFplus http func not found. Copying. Please restart SoF.exe")
			try:
				shutil.copyfile(loc_mm_inject_http, loc_mm_http)
				pass
			except Exception as e:
				raise e
				break

def mayhem(tempDir,dbgsnd):
	global loc_mm_inject_http, __http_func__
	loc_mm_inject_http = __http_func__
	main()

if __name__ == '__main__':
	#print('this script must be injected')
	ini_debug = __dbgsnd__
	mayhem(__temp_path__,ini_debug)
