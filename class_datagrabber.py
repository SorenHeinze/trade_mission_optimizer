#    "class_datagrabber" (v1.0)
#    Copyright 2019 Soren Heinze
#    soerenheinze (at) gmx (dot) de
#    5B1C 1897 560A EF50 F1EB 2579 2297 FAE4 D9B5 2A35
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This file contains the class definition for the object that does everything
# to get (and structure) the data so that the latter can be worked with without
# further ado in class Trader().
# 
# All of what happens here takes place automatically. However, download_files(), 
# build_database() and find_commodity() are written in a way that they can be
# called from outside. Once this class was instantiated that is.
# 
# ATTENTION: Path's to files are hardcoded!

from time import time
import os
import requests
import pickle
import json
from math import sqrt


# This class is doing all the staff to get and structure the rawdata.
# It is instantiated in class Trader(). 
# download_files(), build_database() and find_commodity() are called in 
# elite_trade_mission_optimizer.py if the respective arguments are stated when
# calling the latter.
class DataGrabber(object):
	# < path > is the path to the (raw)data files.
	# < trader > is the instance of class Trader(). It contains certain 
	# attributes that I need here.
	def __init__(self, path, trader):
		self.path = path
		self.systems_file = self.path + 'systems_populated.json'
		self.stations_file = self.path + 'stations.json'
		self.commodities_file = self.path + 'commodities.json'
		self.listings_file = self.path + 'listings.csv'
		self.data_file = path + '111_data_for_today'

		self.trader = trader

		# Is set to True if the necessary files were download. This way it is 
		# taken care of the case that I don't want to rebuild the database if 
		# the data isn't new.
		self.grab_data_from_raw = False

		# This is what I'm actually interested in. It will contain JUST the 
		# stations that a relevant to consider given the parameters given
		# by the user. The structure of this dict
		# will be:
		# - a station id as key (this is necessary because a station name is 
		#   NOT unique!)
		# - station name as subkey
		# - 'name' (of the station), type' (of the station), 'distance' (of the
		#   station to the point of arrival), 'system' (the name of the system 
		#   in which the station is) and 'warez' (a list that contains all commodities 
		#   available at that station) are the sub-subkeys with the respective
		#   values as values.
		self.data = {}

		# These are needed to determine how far another station is away from
		# the origin to be able to determine relevant stations. They are
		# determined from the start_system attribute of < self.trader >
		self.home_coordinates = {'x': 0, 'y':0, 'z': 0}

		# In the station data the system is encoded just with an id-number.
		# Since station data and system data are separate do I need to 
		# remember the id's of the valid systems to be able to connect the
		# stations with the correct systems. Thus in this dict the system-id
		# is the key and the system name the value.
		self.relevant_systems = {}

		self.download_files()

		self.build_database()


	# The user shall NOT provide the coordinates to its home station but just 
	# the system and station name. Thus I need to figure the former out to find 
	# the stations that are within the maximum amount of allowed jumps.
	# For this I need to go through the the systems data once.
	def _find_home_coordinates(self):
		print("Determining home coordinates ...")

		with open(self.systems_file, 'r', encoding = 'utf-8-sig') as f:
			systems = json.load(f)

		for system in systems:
			if self.trader.start_system == system['name']:
				self.home_coordinates['x'] = system['x']
				self.home_coordinates['y'] = system['y']
				self.home_coordinates['z'] = system['z']

				return


	# This method checks if a stations is within the maximum number of jumps 
	# to my home station.
	# < x_2, y_2, z_2 > are the coordinates of the system for which it shall be 
	# figured out if it is within the allowed number of jumps.
	def _within_maximum_distance(self, x_2, y_2, z_2):
		x_1 = self.home_coordinates['x']
		y_1 = self.home_coordinates['y']
		z_1 = self.home_coordinates['z']

		distance = sqrt((x_1 - x_2)**2 + (y_1 - y_2)**2 + (z_1 - z_2)**2)

		return distance / self.trader.jumprange <= self.trader.max_jumps


	# This method finds in the systems rawdata all systems that are within
	# the allowed maximum number of jumps with a given jumprange.
	def _find_relevant_systems(self):
		print("Determining relevant systems ...")

		with open(self.systems_file, 'r', encoding = 'utf-8-sig') as f:
			systems = json.load(f)

		for system in systems:
			x_2 = system['x']
			y_2 = system['y']
			z_2 = system['z']

			if self._within_maximum_distance(x_2, y_2, z_2):
				self.relevant_systems[system['id']] = system['name']


	# A number of parameters make stations not eligible for going there.
	# This method checks all of these and returns True just if everything 
	# is alright.
	# This method exists mainly to keep _find_relevant_stations() more tidy.
	def _fitting_station_parameters(self, station):
		# This information may be None or not exist at all in the data.
		if not station['distance_to_star'] or \
					self.trader.max_distance < station['distance_to_star']:
			return False

		# Yes, MO elif here because all of these conditions need to be 
		# checked separately.
		# 
		# Some stations have no pads at all. I think the only padsize I have to 
		# look out for is 'L'. Stations seem always to have small and medium 
		# sized landing pads.
		first = self.trader.padsize.lower() == 'l'
		second = station['max_landing_pad_size'].lower() != 'l'
		too_large = first and second

		if not station['max_landing_pad_size'] or too_large:
			return False

		if not station['has_market'] or not station['has_commodities']:
			return False

		return True


	# Once the relevant systems are found find the relevant stations in 
	# these systems. This method fills up self.data.
	def _find_relevant_stations(self):
		print("Determining relevant stations ...")

		with open(self.stations_file, 'r', encoding = 'utf-8-sig') as f:
			stations = json.load(f)

			for station in stations:
				if station['system_id'] not in self.relevant_systems:
					continue
				elif not self._fitting_station_parameters(station):
					continue

				this = {'type':station['type'], 'name':station['name'], \
						'system':self.relevant_systems[station['system_id']], \
						'distance':station['distance_to_star'], 'warez':[]}

				self.data[station['id']] = this


	# The available commodities may change in the game, thus I can't hard-code 
	# them. Hence, this method exists to keep _find_relevant_warez() more tidy.
	def _get_commodities(self):
		relevant_information = {}

		with open(self.commodities_file, 'r', encoding = 'utf-8-sig') as f:
			commodities = json.load(f)

		# After I load the commodities from the respective file I have 
		# them in a list. What I actually want is a dict with the 
		# commodities-id's as keys and their names as values.
		for commodity in commodities:
			relevant_information[commodity['id']] = commodity['name']

		return relevant_information


	# As for stations exist some conditions regarding the relevancy of 
	# a commodity. This method checks all of them to keep _find_relevant_warez()
	# more tidy.
	# < line > is a line from the listings csv-file.
	def _fitting_commodity_parameters(self, line):
		# ATTENTION: The positions of the relevant information in the csv-file
		# is hardcoded. I hope that never changes.
		station_id = int(line.strip().split(',')[1])
		supply = int(line.strip().split(',')[3])

		if station_id not in self.data:
			return False

		if supply < self.trader.minimum_supply:
			return False

		return True


	# This method finds the relevant commodities at the relevant stations
	# in the relevant systems. It fills the 'warez'-list for the respective in the station data
	# of self.data.
	def _find_relevant_warez(self):
		print("Determining relevant commodities ...")

		commodities = self._get_commodities()

		with open(self.listings_file, 'r', encoding = 'utf-8-sig') as f:
			# The first line is the header of the table.
			f.readline()

			for line in f:
				if self._fitting_commodity_parameters(line):
					station_id = int(line.strip().split(',')[1])
					commodity_id = int(line.strip().split(',')[2])

					self.data[station_id]['warez'].append(commodities[commodity_id])


	# This method checks for a given < this_file > if it exists at all and
	# if it exists if it is older than a day.
	# This method exists mainly to keep download_files() more tidy.
	def _file_ok(self, this_file):
		# First, check if the file exists.
		if not os.path.isfile(this_file):
			# Since a download will be triggered in download_files() if False 
			# is returned, the database needs to be rebuild.
			self.grab_data_from_raw = True
			return False

		# Second, check if the file is older than 23 hours.
		# getmtime() gets the unix time when the file was created.
		# ATTENTION: The order of operations is important and I need two 
		# separate if-conditions. The reason is that if the file doesn't exist
		# checking how old it is would lead to errors.
		if time() - os.path.getmtime(this_file) > 82800:
			self.grab_data_from_raw = True
			return False

		return True


	# This method exists solely to keep download_files() more tidy.
	# < this_file > is the path to where the file shall be stored.
	# < url > is the url to the file of interest.
	# < what > is a string that tells the user what's been downloaded.
	def _do_the_download(self, this_file, url, what):
		print("Downloading the {} file. This may take a while ...".format(what))
		this = requests.get(url)

		# Save everything.
		with open(this_file, 'wb') as f:
			# < this > is NOT the file!
			f.write(this.content)


	# This method downloads the necessary files that are updated once per day.
	# < force_download > is for the case that I want to force download the 
	# files ... who would have thought that ;) .
	def download_files(self, force_download = False):
		if not self._file_ok(self.systems_file) or force_download:
			url = 'https://eddb.io/archive/v6/systems_populated.json'
			self._do_the_download(self.systems_file, url, 'SYSTEMS')

		if not self._file_ok(self.stations_file) or force_download:
			url = 'https://eddb.io/archive/v6/stations.json'
			self._do_the_download(self.stations_file, url, 'STATIONS')

		if not self._file_ok(self.commodities_file) or force_download:
			url = 'https://eddb.io/archive/v6/commodities.json'
			self._do_the_download(self.commodities_file, url, 'COMMODITIES')

		if not self._file_ok(self.listings_file) or force_download:
			url = 'https://eddb.io/archive/v6/listings.csv'
			self._do_the_download(self.listings_file, url, 'LISTINGS')


	# This method get's all the relevant data from the rawdata.
	# < rebuild > is for the case that the database shall be rebuild manually
	# e.g., with the same files but with changed parameters. 
	def build_database(self, rebuild = False):
		# In case the database-file doesn't exist, this is caught in _file_ok()
		# and there self.grab_data_from_raw is set to True.
		self._file_ok(self.data_file)

		if self.grab_data_from_raw or rebuild:
			self._find_home_coordinates()
			self._find_relevant_systems()
			self._find_relevant_stations()
			self._find_relevant_warez()

			# When all is done, save the data.
			with open(self.data_file, 'wb') as f:
				pickle.dump(self.data, f)

		# In case that the data is fresh and I just do a rerun it is much less 
		# time consuming to open the file that contains the correct data for 
		# the given rawdata.
		else:
			with open(self.data_file, 'rb') as f:
				self.data = pickle.load(f)


	# It is handy to be able to check if a commodity is available at the
	# relevant stations BEFORE a trading mission is accepted. Thus, this 
	# method exists to check exactly that.
	def find_commodity(self, commodity):
		for station_id, information in self.data.items():
			# The available commodities are upper case. However, it may be 
			# beneficial if I account for lower case input.
			warez = [x.lower() for x in information['warez']]

			if commodity.lower() in warez:
				print('\n{} is available.\n'.format(commodity))
				# I just want to know if it is available at all. For that just
				# one station that has the commodity in question needs to be 
				# found.
				return

		print('\n{} is NOT available.\n'.format(commodity))






















