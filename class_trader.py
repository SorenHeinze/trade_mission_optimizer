#    "class_trader" (v1.0)
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

# This file contains the class definition for the object that represents 
# the trading ship and all the necessary information. Mission data and data
# about what commodities can be found where are considered to be trading vessel
# attributes.
# These attributes will than later be used to find the optimal route.

import class_commodity as cc
import class_datagrabber as cd


# The object that contains all methods that are necessary to get all the
# information to figure out one route that require the least amount of 
# revisiting any stations (optimally zero).
class Trader(object):
	# < path > is the path to the files that contain the data.
	# < jumprange > is the (laden) jumprange and 
	# < cargo > is the available cargo space of the ship.
	# < padsize > is the size of pad the ship needs.
	# < max_jumps > is the maximum number of jumps I'm willing to do to 
	# get a commodity and 
	# < max_distance > is the maximum distance I'm willing to travel to reach 
	# a station after arriving in a system.
	# < minimum_supply > is the minimum suply of a commodity that needs to be 
	# available at a station so that this station is considered a relevant
	# location.
	def __init__(self, path, jumprange, cargo, padsize, max_jumps, \
												max_distance, minimum_supply):
		print("Creating the starship ...")
		self.missions_file = path + '000_missions.txt'
		# This will hold all class Commodity() objects for all mission
		# commodities.
		self.warez = []
		# See comments above for what all of that means.
		self.jumprange = jumprange
		self.free_cargo = cargo
		self.padsize = padsize
		self.max_jumps = max_jumps
		self.max_distance = max_distance
		self.minimum_supply = minimum_supply

		# Some information about the system I start in. Will be filled in 
		# _collect_mission_data()
		self.start_system = None
		self.start_station = None
		self.start_commodities = set()
		# These are the locations that need to be visited. It's a double
		# nested dict with the system names as keys and the station names as 
		# sub-keys. The value is a set with the commodities available at the 
		# given location.
		self.locations = {}
		# All commodities I'll need to buy somewhere and how much I need.
		self.needed_commodities = {}
		# Commodities that can NOT be found at mission locations.
		self.detour_commodities = set()
		# Due to how things are handled is it convenient to know the system
		# to which a regular delivery has to be made (so NOT source and return
		# missions but just hauling stuff out there).
		self.deliveries = {}
		# This is just an intermediate container. All the relevant information 
		# that will be stored in here will finally be in self.locations. But it 
		# is convenient to have.
		self.warez_per_location = {}
		# More container to hold temporary information.
		self.check_these = set()
		self.to_be_deleted = set()

		print("Collecting the data ...")
		# 1. collect mission and commodity data.
		# This sets
		# - self.needed_commodities
		# - and the mission locations into self.locations
		self._collect_mission_data()

		# 2. Get the necessary trading data.
		# For when I want to rebuild the database or just check if a commodity
		# is available at the relevant stations I need to be able to have 
		# access to the instance of class DataGrabber() that was instantiated
		# with the correct trading ship parameters.
		self.datagrabber = cd.DataGrabber(path, self)
		self.data = self.datagrabber.data

		# 3. Find the stations that sell the needed commodities.
		self._find_stations_to_buy_from()

		# 4. Find the stations to which just a delivery has to be made.
		self._set_deliveries()

		# 5. Find the commodities that can NOT be found at mission locations, ...
		self._find_detour_warez()

		# 6. ... figure out where I can get them, ...
		self._set_warez_per_location()

		# 7. ... but keep just the stations that are best (usually closest to 
		# point of entry that is or NOT a planetary base), ...
		self._keep_closest()

		# 8. ... and just the locations that have unique commodities (see 
		# comment to _keep_unique() for what that means.)
		# Afterwards I have all the information I need to optimize my route.
		self._keep_unique()


	# This method does all the stuff so that everything is in order if sth.
	# is bought or sold. It also updates the necessary entries regarding
	# locations where to buy stuff when this information is collected.
	# 
	# < quantity > is always to be positive!
	# < action > can be:
	# - 'sellpoint' for creating a sellpoint; buypoints are created differenly 
	#   in _find_stations_to_buy_from().
	# - 'selling' for selling at a sellpoint
	# - 'buying' for buying at a buypoint
	def _update_ware(self, ware, system, station, quantity, action):
		if action == 'sellpoint':
			ware.update_sellpoint(system, station, quantity)
		elif action == 'buying':
			# Once created, buypoints (or sellpoints) don't need to be updated 
			# but how much of that commodity is in my hold and ...
			ware.quantity += quantity
			# ... the cargo space needs to be adjusted.
			self.free_cargo -= quantity
		elif action == 'selling':
			# Since I'm selling, < quantity > needs to be negative.
			ware.update_sellpoint(system, station, -quantity)
			ware.quantity -= quantity
			self.free_cargo += quantity


	# I can have several missions concerning one commodity. Thus I need to 
	# check first if I already have it in self.warez to not overwrite it 
	# in _get_data_from_line() with a newly created entry.
	# This method does the check and returns the repsective < ware > if it 
	# already exists.
	def _commodity_in_inventory(self, commodity):
		for ware in self.warez:
			if ware.name == commodity:
				# ATTENTION: THIS returns the pointer to the object and NOT a
				# copy of the object. Thus I can manipulate it further 
				# afterwards.
				return ware

		return None


	# This method reads each line from the mission file and determines the
	# commodity that is needed, how much of it and where. It exists mainly to 
	# keep _collect_mission_data() more tidy.
	def _get_data_from_line(self, line):
		data = line.split('\t')
		# While I work in the order system -> station is the order the other
		# way around in the data. Somehow that made more sense.
		station = data[0]
		system = data[1]
		commodity = data[2]
		quantity = int(data[3])

		# I need to travel to all mission location.
		if system not in self.locations:
			self.locations[system] = {}
		if station not in self.locations[system]:
			self.locations[system][station] = set()

		# Remember which and how many commodities I need. However, the 
		# commodity "delivery" shall NOT appear in self.needed_commodities
		# since this would lead to "confusion" in later steps.
		if commodity.lower() != 'delivery' and commodity not in self.needed_commodities:
			self.needed_commodities[commodity] = 0

		# Yes, this needs to be separate, since several missions may require 
		# the same commodity but just the first mission would trigger the above.
		if commodity.lower() != 'delivery':
			self.needed_commodities[commodity] += quantity

		ware = self._commodity_in_inventory(commodity)

		if not ware:
			ware = cc.Commodity(commodity)
			self.warez.append(ware)

		self._update_ware(ware, system, station, quantity, 'sellpoint')

		# 'delivery' is in the missions file the keyword for stuff that needs
		# to be delivered. That means, I already have it in my cargo and the
		# space needs to be adjusted accordingly!
		# It doesn't matter WHAT I have to deliver since I can't sell this 
		# for any other mission.
		if commodity.lower() == 'delivery':
			self._update_ware(ware, system, station, quantity, 'buying')


	# The mission data and starting location are provided manually in a 
	# specific file. This method gets this information from said file.
	def _collect_mission_data(self):
		with open(self.missions_file, 'r', errors = 'ignore') as f:
			for line in f:
				if "I'm at" in line:
					self.start_system = line.split('\t')[2].strip()
					self.start_station = line.split('\t')[1]
					continue

				# The length check is for the case that I leave empty lines
				# in the mission data to separate for different missions.
				if len(line.split('\t')) != 4:
					continue

				self._get_data_from_line(line)


	# self.data contains ALL stations within the maximum allowed number of 
	# jumps. That doesn't mean that these stations sell what I need.
	# Thus, this function checks this and includes just the relevant 
	# information into self.warez
	def _find_stations_to_buy_from(self):
		needed_commodities = set(self.needed_commodities.keys())

		for station_id, information in self.data.items():
			offered_commodities = set(information['warez'])
			buy_here = offered_commodities.intersection(needed_commodities)

			# A station may not have anything I need. In that case I don't need
			# to go further.
			if not buy_here:
				continue

			for commodity in buy_here:
				system = information['system']
				station = information['name']
				distance = information['distance']
				this_type = information['type']

				# When this method is called self.warez contains all 
				# commodities and calling _commodity_in_inventory() is the 
				# most convenient way to get < ware >.
				ware = self._commodity_in_inventory(commodity)

				ware.update_buypoint(system, station, distance, this_type)

				# If the station is also a mission location, I add here the 
				# information that I can buy a commodity of interest there.
				try:
					self.locations[system][station].update([commodity])
				except KeyError:
					pass

				# Since I'm already at it I can also set the commodities at
				# the origin location. It's handy to have it later.
				if system == self.start_system and station == self.start_station:
					self.start_commodities.update([commodity])


	# Due to how the data and self.warez are structured and defined I would need 
	# always an additional loop over self.warez if I want to know if I actually 
	# have delivery-missions (NOT source and return missions!) and where these 
	# go to. Thus, it is handy to know where these delivery missions go to and 
	# make this knowledge an attribute.
	def _set_deliveries(self):
		for ware in self.warez:
			if ware.name.lower() == 'delivery':
				self.deliveries = ware.sell_at

		return


	# This function exists just to reduce the indentation-depth in 
	# _find_detour_warez().
	def _mission_has_commodity(self, ware):
		for system, stations in ware.buy_at.items():
			for station, quantity in stations.items():
				try:
					# At this point JUST the mission locations can be found in
					# self.locations and the sub-dicts contain the commodities
					# that can be bought there.
					if ware.name in self.locations[system][station]:
						return True
				except KeyError:
					pass

		return False


	# This function figures out which commodities can NOT be found at one of 
	# the stations for which I have a mission.
	def _find_detour_warez(self):
		for ware in self.warez:
			if ware.name.lower() == 'delivery':
				continue

			if self._mission_has_commodity(ware):
				continue
			else:
				self.detour_commodities.update([ware.name])


	# It turned out that it is handy to order (and store) the information in 
	# a different way if stations with more than one commodity shall be handled.
	# This function does that.
	def _set_warez_per_location(self):
		for ware in self.warez:
			commodity = ware.name

			# Don't consider commodities that can be found at mission locations.
			if commodity not in self.detour_commodities:
				continue

			for system, stations in ware.buy_at.items():
				if system not in self.warez_per_location:
					self.warez_per_location[system] = {}

				for station in stations:
					if station not in self.warez_per_location[system]:
						self.warez_per_location[system][station] = set()

					self.warez_per_location[system][station].update([commodity])


	# This function exists just to have fewer indentations in _keep_closest().
	# It figures out if two stations have the same type and amount of different 
	# available commodities.
	def _find_equal_commodities(self, commodities):
		self.check_these = set()

		for system, stations in self.warez_per_location.items():
			for station, these_commodities in stations.items():
				if commodities == these_commodities:
					self.check_these.update([(system, station)])


	# Dito.
	# This method figures out which stations of the stations that have the 
	# same available commodities are further away from the point of arrival 
	# into the system. OR if a station is NOT planetary while another is.
	def _find_furthest(self, commodities):
		# self.check_these is set in _find_equal_commodities() just if 
		# equal commodities have been found.
		if not self.check_these:
			return

		best_distance = 999999999999.9
		best_system = None
		best_station = None
		best_station_landable = None

		# Get the dict that contains the distances.
		for ware in self.warez:
			if ware.name in commodities:
				information = ware.buy_at
				# Since I have in self.check_these stations that have the same 
				# commodities I can break after I found just one.
				break

		# Find the station that is closest to the point of arrival ...
		for (system, station) in self.check_these:
			distance = information[system][station]['distance']
			this_type = information[system][station]['type']

			# If a NON-planetary station is further away from the point of 
			# entry than a planetary station, the former is ALWAYS preferred.
			# The reason is, that getting down to and up from a planet is 
			# so time consuming that it is worth many minutes flight time
			# to a non-planetary station.
			# However, that assumes that self.max_distance has a reasonable 
			# value. My gut-feeling tells me that this is justified for 
			# stations up to 5,000 ls away.
			# 
			# ATTENTION: It is important to compare here the specific values
			# and observe that None and False can have sligthly different 
			# meanings!
			on_planet = 'planetary' in this_type.lower()
			to_orbit = best_station_landable == True and not on_planet
			closer = distance < best_distance

			if to_orbit or closer:
				# Don't take a planetary station if the system has a relevant
				# non-planetary station! Not even if the former is closer!
				if best_station_landable == False and on_planet:
					continue

				best_distance = distance
				best_system = system
				best_station = station
				best_station_landable = on_planet

		# ... all others can be scheduled for deletion. That however, has to 
		# take place AFTER the loops in _keep_closest() are finished because 
		# otherwise I would change stuff while still iterating over it.
		# Thus, I need to save the information about what has to be deleted.
		for system, station in self.check_these:
			if system != best_system and station != best_station:
				self.to_be_deleted.update([(system, station)])


	# This function exists just so that keep _keep_closest() is more tidy.
	def _already_checked(self, commodities, checked_these):
		if sorted(list(commodities)) in checked_these:
			return True
		else:
			checked_these.append(sorted(commodities))
			return False


	# If there are stations that have the same type and amount of commodities 
	# I just want the one which is closest to the point of entry or which is 
	# further away but NOT on a planet.
	def _keep_closest(self):
		# This is filled in _find_furthest(). However, since i will re-use 
		# _keep_closest() in _keep_unique() I need to set it to an empty set 
		# here because otherwise self.to_be_deleted will contain old elements.
		self.to_be_deleted = set()

		checked_these = []

		for system, stations in self.warez_per_location.items():
			for station, commodities in stations.items():
				if self._already_checked(commodities, checked_these):
					continue

				self._find_equal_commodities(commodities)
				self._find_furthest(commodities)

		empty_systems = set()
		for system, station in self.to_be_deleted:
			del self.warez_per_location[system][station]

			# I want to delete any empty entries. But I should not do this 
			# while iterating over it ;).
			if not self.warez_per_location[system]:
				empty_systems.update([system])

		for system in empty_systems:
			del self.warez_per_location[system]


	# This method exists just so that _keep_unique() is more tidy. It 
	# basically just checks the number of commodities available at all
	# stations after these have been cleaned for commodities that are already
	# available at other stations. The station with the most available and not
	# yet bought commodities "wins".
	def _best_station(self, max_warez_at_location):
		best_system = None
		best_station = None
		best_commodities = None
		for system, stations in self.warez_per_location.items():
			for station, commodities in stations.items():
				if len(commodities) > max_warez_at_location:
					max_warez_at_location = len(commodities)
					best_system = system
					best_station = station
					best_commodities = commodities

		# All of this is needed for the next loop in _keep_unique()
		return best_system, best_station, best_commodities, max_warez_at_location


	# Dito.
	# < best_commodities > is the list with the commodities found at the
	# station that has the most commodities during the given loop in 
	# _keep_unique().
	def _delete_fetched_commodities(self, best_commodities):
		delete_these = []
		for system, stations in self.warez_per_location.items():
			delete_those = []
			for station in stations:
				for commodity in best_commodities:
					# A station may not have a given commodity.
					try:
						self.warez_per_location[system][station].remove(commodity)
					except KeyError:
						pass

				# Don't delete while iterating over it.
				if not self.warez_per_location[system][station]:
					delete_those.append(station)

			for station in delete_those:
				del self.warez_per_location[system][station]

			if not self.warez_per_location[system]:
				delete_these.append(system)

		for system in delete_these:
			del self.warez_per_location[system]


	# After calling _keep_closest() contains self.warez_per_location the best 
	# stations that have one or two or three etc. pp. commodities that can not 
	# be found at mission locations.
	# ATTENTION: This is an _excluding_ "or" in the sentence above!
	# Hence, self.warez_per_location likely still contains locations at which 
	# one commodity can be found that can also be found at another location
	# but the other location has also another commodity of interest. 
	# Example: location 1 has ['Fish'], location 2 has ['Fish', 'Germanium']
	# Thus, it is better to fly just to the location 2 since I can pick 
	# up several commodities at the latter. Consequently, I want the former to 
	# be deleted from self.warez_per_location. 
	# This however is a bit more complicated since keeping a certain location
	# means that I get certain commodities. If these can be found in another
	# "multiple-commodities-location" the latter may become a 
	# "single-commodity-location" which is worse than a possible other 
	# "single-commodity-location" that has the same commodity. Thus I need to 
	# iterate over this as long as everything is optimal. 
	def _keep_unique(self):
		keep_these = []

		# If JUST "single-commodity-locations" are left after a loop no further
		# optimalization can take place.
		max_warez_at_location = 99
		while max_warez_at_location > 0:
			max_warez_at_location = 0
			# 1. Find the location that has the most commodities.
			best_system, best_station, best_commodities, \
				max_warez_at_location = self._best_station(max_warez_at_location)

			if not best_system:
				break

			# 2. Keep the best ...
			# None of these systems/stations should be in self.locations
			# since the latter should contain just mission locations at this 
			# point while self.warez_per_location contains just none-mission
			# locations.
			self.locations[best_system] = {}
			self.locations[best_system][best_station] = best_commodities

			# 3. ... and clean up self.warez_per_location for the next loop.
			del self.warez_per_location[best_system]

			self._delete_fetched_commodities(best_commodities)

			# 4. Cleaning up includes calling _keep_closest() again, due to 
			# the situation I described in the lengthy comment above.
			self._keep_closest()






















