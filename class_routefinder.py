#    "class_routefinder" (v1.0)
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

# This file contains the class definition for the object that actually finds 
# a route that requires as few as possible re-visiting of (mission) stations
# for the parameters given by the user.

from itertools import permutations
from copy import deepcopy
from math import factorial
import random


# The object that contains all methods that are necessary to determine a
# route.
class RouteFinder(object):
	# < trader > is the class Trader() instance that contains the information
	# necessary to calculate the route.
	def __init__(self, trader):
		print("Initiating route finder ...")
		# Many routes exist that are not optimal. Since I don't know beforehand 
		# what's a good route and what's not a good route I need to check all 
		# possible permutations of station ordering.
		# However, during the search process certain attributes of self.trader
		# are changed. Thus I need to keep the original trader object.
		self.original_trader = trader
		# All methods work with this object, NOT the self.original_trader!
		self.trader = deepcopy(self.original_trader)
		# This will be set in _permutate_locations() and it will contain 
		# simplified information about the locations that need to be visited.
		self.location_permutations = None
		# This acts as a temporary storage to determine the best route.
		# In the best case it equals zero after all possible routes where 
		# tried.
		self.best_remaining_missions = self._count_missions()
		# This acts as a temporary storage for information the user needs to
		# know while each route is checked. If it turns out that this route
		# is the best (so far), this will be more permanentely stored ...
		self.messages = []
		# ... in here and presented at the end to the user.
		self.best_run_messages = []
		# If a good (but not yet optimal) route was found, the information
		# is stored in here in _fly_this_route() so that the good route can 
		# be compared to find an even better route.
		self.best_trader = deepcopy(self.original_trader)
		# This is simplified information about the location where I start so 
		# that I can access it easier in several places below.
		self.origin_location = (trader.start_system, trader.start_station, \
														trader.start_commodities)

		self._permutate_locations()

		self._find_route()


	# Each commodity that needs to be delivered to a specific station is seen
	# as a mission. The actual in-game missions could be more, e.g., if the same
	# material needs to be delivered to different factions at the same stations.
	# For what this program shall do this doesn't matter. This is the reason
	# why I'm not already counting the missions when instantiating the Trader().
	def _count_missions(self):
		counter = 0
		for ware in self.trader.warez:
			for system, stations in ware.sell_at.items():
				counter += len(stations)

		return counter


	# This mehtod simplifies the information that one needs to know for 
	# each location and than generates all permutations for all locations.
	def _permutate_locations(self):
		simplified_locations = []

		for system, stations in self.trader.locations.items():
			for station, commodities in stations.items():
				simplified_locations.append((system, station, commodities))

		self.location_permutations = permutations(simplified_locations)

		# I didn't know where else to put this.
		print("\nYOU ARE AT:", self.origin_location[1], "in", self.origin_location[0])
		print("Here you can find:", list(self.origin_location[2]))
		print("It will be checked if something can already be bought here.\n")


	# This method does everything if a commodity can be sold at a given 
	# location.
	# < location > is a tuple with the system-name, station-name and available
	# commodities. The latter is not needed here.
	def _sell_at_location(self, location):
		system = location[0]
		station = location[1]

		for ware in self.trader.warez:
			commodity = ware.name

			sell_here = system in ware.sell_at and station in ware.sell_at[system]

			if sell_here:
				quantity = ware.sell_at[system][station]

				# Don't sell anything if not enough of this commodity is in 
				# the cargo bay.
				if quantity > ware.quantity:
					continue

				# The user needs to be told what and how much to sell where.
				this = "SELL < {} > of < {} > ".format(quantity, commodity)
				that = "at < {} > in < {} >".format(station, system)
				self.messages.append(this + that)

				# The information about this commodity needs to be updated ...
				self.trader._update_ware(ware, system, station, quantity, 'selling')

				# ... and the current location shall be removed from the list 
				# of stations that need to be visited since this specific 
				# mission is finished.
				del ware.sell_at[system][station]

				if not ware.sell_at[system]:
					del ware.sell_at[system]


	# More or less the same like _sell_at_location() just for buying a 
	# commodity.
	# < location > is a tuple with the system-name, station-name and available
	# commodities.
	def _buy_at_location(self, location):
		system = location[0]
		station = location[1]
		commodities = location[2]

		for ware in self.trader.warez:
			commodity = ware.name

			is_needed = commodity in self.trader.needed_commodities

			if is_needed:
				quantity_needed = self.trader.needed_commodities[commodity]
				# Yes, this condition means that I buy just wholesale.
				enough_space = self.trader.free_cargo >= quantity_needed
				is_available = commodity in commodities
			else:
				enough_space = False
				is_available = False

			if is_needed and enough_space and is_available:
				# The user needs to be told what and how much to buy where.
				this = "BUY < {} > of < {} > ".format(quantity_needed, commodity)
				that = "at < {} > in < {} >".format(station, system)
				self.messages.append(this + that)

				# Update the commodity ...
				self.trader._update_ware(ware, system, station, quantity_needed, 'buying')

				# ... and delete it from the list of needed commodities.
				del self.trader.needed_commodities[commodity]


	# This method basically does the selling / buying for each location in a 
	# given permutation of locations and checks if this route is better than 
	# the so far best route.
	# This method exists mainly to keep _compute_all_permutations() and 
	# _compute_random_routes() more tidy.
	# < locations > is a given order of locations to visit.
	def _fly_this_route(self, locations):
		# First I need to deepcopy the original information so that it is 
		# available for the next permutation!
		self.trader = deepcopy(self.original_trader)

		# It doesn't hurt to check if there is something to be bought at the 
		# origin location. One never knows!
		# 
		# I need to do this here (and thus every time and for each permutation)
		# instead of in _find_route() before I compute the route(s) because 
		# _sell_at_location() and _buy_at_location() operate on self.trader.
		# however, self.trader will for each permutation be written over with 
		# the original information. 
		# I could change the original information after the origin location 
		# was checked BUT there is a point why the original information is
		# stored ... I'm also too lazy to do that and since the routes are 
		# found rather fast despite these additional operations am I not 
		# having any incentive to do so.
		# 
		# An origin location may not have been declared by the user.
		if self.origin_location[0]:
			self._sell_at_location(self.origin_location)
			self._buy_at_location(self.origin_location)

		# Do the same for each location in the given permutation of locations.
		for location in locations:
			self._sell_at_location(location)
			self._buy_at_location(location)

		remaining_missions = self._count_missions()

		# If less missions remain after being once at every station 
		# that is a sign for a better route. However ...
		first = remaining_missions < self.best_remaining_missions
		# ... it is possible that this will be a route for which for one
		# or several missions the commodities still need to be bought.
		# That however would result in going to two addtional stations 
		# per commodity/mission. 
		# The above may be confusing. Thus an example: transport of Germanium 
		# to two different stations counts as TWO missions. However, just ONE 
		# commodity is needed. Thus it is possible that one has "solved" more 
		# missions (e.g., because one commodity is needed at many sations) and 
		# can still have more needed commodities (the ones that are different 
		# from the commodity everybody wants).
		# Hence, the second condition that the number of things that still have 
		# to be picked up needs to be at least equal to the previous route.
		second = len(self.trader.needed_commodities) <= len(self.best_trader.needed_commodities)

		# This is a variation of the above two conditions. However, it can't
		# be caught in the above.
		third = remaining_missions == self.best_remaining_missions
		fourth = len(self.trader.needed_commodities) < len(self.best_trader.needed_commodities)

		if (first and second) or (third and fourth):
			self.best_remaining_missions = remaining_missions
			self.best_trader = deepcopy(self.trader)
			self.best_run_messages = deepcopy(self.messages)

		# Don't forget to delete the messages generated in _buy_at_location()
		# and _sell_at_location() for the next permutation.
		self.messages = []



	# Finding the optimal route is basically a combinatorial problem. That 
	# means the number of possibilities grows factorial!
	# Testing has shown that performing the calculations for all possible
	# routes with 9 possible locations takes a bearable amount if time. 
	# Not so with 10. Hence, up to 9 locations the "exact solution" is 
	# calculated. That is what this function does.
	# < stations_to_visit > is just the number of stations to be visited.
	# It is computed in _find_route().
	def _compute_all_permutations(self, stations_to_visit):
		number_of_combinations = factorial(stations_to_visit)

		for i, locations in enumerate(self.location_permutations):
			if (i + 1) % 1000 == 0:
				this = "Went through {} of {} ".format(i + 1, number_of_combinations)
				that = "possible routes. Best run so far left "
				siht = "{} mission(s) open".format(self.best_remaining_missions)
				print(this + that + siht)

			self._fly_this_route(locations)

			# Once _a_ route is found that doesn't require me to visit any
			# of the given stations several times I do not need to search
			# for another route that would lead to the same result.
			if self.best_remaining_missions == 0:
				break


	# 9! is approx. 400,000. In the worst case the program needs to go through 
	# all possible routes and it would need ca. 5 minutes. I consider this 
	# bearable. Thus, _compute_all_permutations() will be used in the above case.
	# With just one location more to visit the time to calculate all possible
	# routes becomes UNbearable. However, permutations() (as used in 
	# _permutate_locations()) generates lists of locations which are NOT too 
	# different from one element to the next since just the position of two
	# elements are switched. Hence, if the first permutation is a worst case
	# the computations will take very much time. Also, radical changes in the
	# permutation take place just over many permutations. This however can be 
	# considered as randomizing the order of the elements in a list of locations.
	# 
	# Thus, I will NOT take the risk of running the program for very long but 
	# the function at hand does rather this -- randomizing.
	# 
	# If the number of locations to be visited is larger than nine, the order
	# of these locations is shuffled 400,023 times and than it is checked which
	# one the best is.
	# Yes, that does certainly NOT explore the whole space of possible routes.
	# But since that would take so much time I wouldn't have done that anyway.
	# Yes, that may lead to checking a possible route twice. So what? the 
	# chances for that are really slim and if it happens a couple of times I can 
	# live with it.
	# But it is also very likely that I hit a route that is good enough.
	# 
	# Otherwise this method is the same as _compute_all_permutations().
	def _compute_random_routes(self):
		# A permutations() object is a generator which is not subscriptable.
		# However, _permutate_locations() does not just generate this, but
		# also structures the data in a convenient way. Hence, I would like 
		# to have one element from that object and this is how I can get it.
		for locations in self.location_permutations:
			# As I said: I need just one!
			break

		# I can't shuffle tuples.
		locations = list(locations)

		i = 0
		while i < 400023:
			# Here the random order is created. ... *lol* ...  a nice way of 
			# saying bring this list deliberately into disorder :P
			random.shuffle(locations)

			if (i + 1) % 1000 == 0:
				this = "Went through {} of 400,0023 random ".format(i + 1)
				that = "possible routes. Best run so far left "
				siht = "{} mission(s) open".format(self.best_remaining_missions)
				print(this + that + siht)

			self._fly_this_route(locations)

			if self.best_remaining_missions == 0:
				break

			i += 1


	# This is the main method that calls methods which call other methods
	# and so on and in the end the best route is found.
	def _find_route(self):
		# trader.locations contains ALL locations that need to be visited, 
		# including stations from which i just pick up stuff but don't have a 
		# mission to.
		stations_to_visit = sum([len(values) for values in self.trader.locations.values()])

		print("{} stations need to be visited.".format(stations_to_visit))
		print("Optimizing the route (this will take a while!) ...")

		if stations_to_visit <= 9:
			self._compute_all_permutations(stations_to_visit)
		else:
			self._compute_random_routes()






















