#    "additional_functions" (v1.1)
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

# This file contains functions used in trade_mission_optimizer.py which did not 
# fit into any of the other files or the classes.


import argparse

# This function gets the command line arguments. It exists mainly to keep the 
# the main file more tidy.
def get_args():
	parser = argparse.ArgumentParser()

	# The maximum cargo space of your ship. The only argument that is required
	# each time the program is called.
	keyword = '--cargo'
	short = '-c'
	metavar = 'free cargo space'
	this = 'The maximum cargo space of your ship. Needs to be an integer. '
	that = 'Default will be 512.'
	parser.add_argument(keyword, short, metavar = metavar, type = int, \
											default = 512, help = this + that)

	# The (laden) jumprange of your ship.
	keyword = '--jumprange'
	short = '-j'
	this = 'The (laden) jumprange of your ship in ligthyears. Default is '
	that = '20 ly. A significant change requires rebuilding of the database.'
	parser.add_argument(keyword, short, metavar = 'ly', type = float, \
											default = 20.0, help = this + that)

	# The padsize your ship needs.
	keyword = '--size'
	short = '-s'
	this = 'The padsize your ship needs. Default is L. Use "M" '
	that = '(without quotes) if you have a smaller ship. A change requires '
	siht = 'rebuilding the database.'
	parser.add_argument(keyword, short, type = str, metavar = 'padsize', \
									default = 'L', help = this + that + siht)

	# The maximum number of jumps you intend to do for one commodity.
	# 8 seems to be a good number since doing eight jumps needs approx. the same 
	# time like flying to one station, docking, buying a commodity and undocking 
	# again. Thus if at the 8-jumps-away station two commodities can be picked up
	# doing more jumps paid off. Also, some commodities may not be available in the
	# direct vicinity of the starting point.
	# fly to a station, and dock
	keyword = '--max-jumps'
	short = '-mj'
	default = 8
	metavar = 'foo'
	this = 'The maximum number of jumps you would perform (one way) to get a '
	that = 'commodity. Needs to be an integer. Default is 8. A change '
	siht = 'requires rebuilding the database.'
	parser.add_argument(keyword, short, type = int, default = 8,\
													help = this + that + siht)

	# The maximum distance (in lightseconds) a station shall have from the point 
	# of entry into a system to be considered. This is to not include stations 
	# that are very far away since this increases the chance to be interdicted 
	# by pirates and shortening the time to finish missions is the whole point 
	# of this program!
	# From own experience 2500 s seems to be an value. Personally I may go as 
	# high as ca. 5000 ls
	keyword = '--max-distance'
	short = '-md'
	this = 'The maximum distance (in lightseconds) a station shall have from '
	that = 'the point of entry into a system to be considered. Default is '
	siht = '2500 ls. Needs to be an integer. A change requires rebuilding '
	taht = 'the database.'
	parser.add_argument(keyword, short, metavar = 'ls', type = int, \
							default = 2500, help = this + that + siht + taht)

	# The minimum amount of (any) commodity that shall be available at a station
	# so that it will be considered as to be relevant (for this commodity).
	# Since the data is up to a day old too small numbers may lead 
	keyword = '--minimum-supply'
	short = '-ms'
	this = 'The minimum amount of (any) commodity that shall be available at '
	that = 'a station so that it will be considered as to be relevant. '
	siht = 'Needs to be an integer. Default is 100.'
	parser.add_argument(keyword, short, type = int, default = 100, \
													help = this + that + siht)

	# The path to where all the downloaded files shall be.
	keyword = '--path'
	short = '-p'
	this = 'The path where the missions file can be found. Default is '
	that = 'the current directory. Needs to be stated ALWAYS if it is NOT the '
	siht = 'current directory!'
	parser.add_argument(keyword, short, type = str, default = './', \
													help = this + that + siht)

	# Below follow the arguments that determine what to actually do.
	# 
	# The default behaviour to find a suitable route.
	# The user does not really need to specifiy this since it is set to True
	# by default. It's just convenient to have in the args.
	keyword = '--run'
	short = '-r'
	this = 'Find ONE route that requires no revisiting of stations or the '
	that = 'fewest amount of revisiting. This will be the default action '
	siht = "and doesn't need to be stated."
	parser.add_argument(keyword, short, action = 'store_true', default = True, \
													help = this + that + siht)

	# To check if a commodity is available at all within the given parameters.
	# Because there is no point in taking a mission that requires a commodity
	# that isn't available close by.
	keyword = '--commodity-available'
	short = '-ca'
	this = 'Check if a commodity is available at relevant stations. All other '
	that = 'actions will be ignored if this is set. < commodity > needs to be '
	siht = 'written as in the game.'
	parser.add_argument(keyword, short, metavar = 'commodity of interest', \
										type = str, help = this + that + siht)

	# If the database shall be rebuild. Necessary if the parameters changed
	# or if newer files were downloaded manually.
	keyword = '--build-database'
	short = '-b'
	this = 'Force build the database. Needs to be done if the ship or user '
	that = 'parameters (e.g. the "home coordinates") have change significantly '
	siht = 'or if newer files were downloaded manually. Will ignore < run >.'
	parser.add_argument(keyword, short, action = 'store_true', \
													help = this + that + siht)

	# If the necessary files shall be downloaded again from EDDB.io.
	keyword = '--download-files'
	short = '-d'
	this = 'Force download the necessary files from EDDB.io. Will ignore < run >.'
	parser.add_argument(keyword, short, action = 'store_true', help = this)

	args = parser.parse_args()

	# The program shall run automatically without further input in all cases
	# EXCEPT if I just want to know if a commodity is available.
	if args.commodity_available:
		args.run = False
		args.build_database = False
		args.download_files = False
	elif args.build_database or args.download_files:
		args.run = False

	return args


# This function simply prints the result.
# < route > is the instance of class Routefinder(). 
def print_results(route):
	print("\nThis is a route that requires visiting all locations just once:")

	for message in route.best_run_messages:
		print(message)

	if route.best_remaining_missions > 0:
		this = "\n\nThe following commodities could not be bought or "
		that = "delivered without visiting the respective stations twice:\n"
		print(this + that)

		for ware in route.best_trader.warez:
			if ware.sell_at:
				print("commodity:", ware.name)
				print("in cargo (of that commodity):", ware.quantity)
				print("needs to be delivered to (and so much of it per station):")
				for system, stations in ware.sell_at.items():
					print("    ", system)
					for station, quantity in stations.items():
						print("        ", station, "->", quantity)
				print("---")






















