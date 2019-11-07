#    "class_commodity" (v1.0)
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

# This file contains the commodities class definition as used in 
# elite_trade_mission_optimizer.py


# A simple object that helps to handle several commodites.
class Commodity(object):
	def __init__(self, name):
		self.name = name
		# This is the quantity the ship has at a given location in the cargo.
		# If one commodity is bought, the total necessary amount will be bought.
		# However, it can be sold in smaller quantities.
		self.quantity = 0
		# This is a two-folded dict and the structure will be:
		# - system name as key
		# - station name as subkey
		# - total quantity of that commodity that needs to be delivered to 
		#   this station as value.
		self.sell_at = {}
		# This is a three-folded dict and the structure will be:
		# - system name as key
		# - station name as subkey
		# - "distance" (to the station) and "type" (of station) as final keys
		#   and suitable values as values.
		self.buy_at = {}


	# When mission data is parsed, the respective information needs to be 
	# stored properly. This method helps with that and considers all 
	# eventuallities that could trigger errors.
	# This function can be called for the same < system > and < station >
	# several times dependent on what kind of missions one takes.
	def update_sellpoint(self, system, station, quantity):
		if system not in self.sell_at:
			self.sell_at[system] = {}
		# I need to know how much I need to sell here.
		if station not in self.sell_at[system]:
			self.sell_at[system][station] = 0

		self.sell_at[system][station] += quantity


	# Dito.
	# Per commodity and < system > / < station > combination is this function
	# called just once.
	def update_buypoint(self, system, station, distance, this_type):
		if system not in self.buy_at:
			self.buy_at[system] = {}
		if station not in self.buy_at[system]:
			# For stations to buy at I need to know the distance to the 
			# point of arrival and what type it is.
			self.buy_at[system][station] = {'distance':distance, 'type':this_type}






















