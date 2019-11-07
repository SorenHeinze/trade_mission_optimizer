#    "trade_mission_optimizer" (v1.0)
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

# This program is meant to be used to find one possible route for trade or 
# delivery missions in Elite Dangerous so that as few as possible stations
# need to be visited twice.
# 
# Finding this route is dependent on several parameters which need to be 
# provided by the user below.
# 
# The route is NOT necessarily the only nor the shortest route. Flying
# to a station, docking and undocking takes more time than jumping between 
# systems. Thus highest priority was set to find a stations that have more than
# one commodity needed for mission(s) even if that may require more jumps to 
# the system with that station. 
# 
# The program needs to download certain files from eddb.io to work and build
# a database of relevant stations (with the given parameters). This may take a 
# while.
# 
# Some of the needed throughout the program is stored several times. Strictly
# speaking this is not necessary. But the information is often in several 
# level deep nested dicts. Thus storing specific information in certain 
# attributes helps very much with clearer code structure.
# 
# ATTENTION: The mission data needs to be provided in a separate file 
# called "000_missions.txt". 
# The order of information in there is 
# Station nameme	System name	Commodity	Amount
# < Commodity > needs to be "Delivery" if something just needs to be delivered
# 
# ATTENTION: Filenamesare hardcoded!


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
## ## ## ## ##                            ## ## ## ## ##
## ## ## ## ##   Input information below  ## ## ## ## ##
## ## ## ## ##                            ## ## ## ## ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import class_trader as ct
import class_routefinder as cf
import additional_functions as af

if __name__ == '__main__':
	args = af.get_args()

	path = args.path
	jumprange = args.jumprange
	cargo = args.cargo
	padsize = args.size
	max_jumps = args.max_jumps
	max_distance = args.max_distance
	minimum_supply = args.minimum_supply

	# Yes, my trading ship is called Chicken of Doom :) ... because it's yellow.
	chicken_of_doom = ct.Trader(path, jumprange, cargo, padsize, max_jumps, \
														max_distance, minimum_supply)

	if args.commodity_available:
		commodity = args.commodity_available
		chicken_of_doom.datagrabber.find_commodity(commodity)

	if args.download_files:
		chicken_of_doom.datagrabber.download_files(True)

	if args.build_database:
		chicken_of_doom.datagrabber.build_database(True)

	if args.run:
		this_route = cf.RouteFinder(chicken_of_doom)
		af.print_results(this_route)






















