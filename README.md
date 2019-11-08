# trade_mission_optimizer
You have a bunch of trading missions in Elite:Dangerous and want to finish them asap? This program helps you to find an optimal order of missions.

## Problem:
You are a trader in Elite:Dangerous and you have a bunch of trading missions. Several factions on different stations want you to source and return various commodities? You also need to deliver stuff to different stations? You would prefer picking up commodities at stations where you have to go to anyway? At the same time you want to visit as few stations as possible for commodities that can't be found at mission locations?

## Solution:
The awesome EDDB.io has a lot of the information needed for traders. However, you have to look up what you look for manually. That means that many manual comparisons have to be done to get the information you want. After all information is collected a route that requires visiting as few stations as possible needs to be figured out. The latter also has to be done manually and may take a lot of time. 

## What you'll get:
This python 3 program downloads the necessary databases from EDDB.io. It than automatically figures out which commodities can be found at mission locations or if several commodities can be bought at just one station to avoid flying around unnecessary. Afterwards one order of how the stations are to be visited is figured out so that (in the best case) no location needs to be visited twice.

# Usage
Preparations:
- State your origin-station and origin-system in the "000_missions.txt"-file. Directly in the line that starts with "I'm at. The database will be build "around" this home station! Thus it needs rebuilding if it changes significantly (see examples below). 
- State your mission-stations, -systems, -commodities and -quantities in the same file.
- New or completed missions? Just update the information in said file and run the program again. A better route may be found.
- See said file for more hints.

Once this is done …
```
python3 trade_mission_optimizer.py -h -r
usage: trade_mission_optimizer.py [-h] [--cargo free cargo space]
                                  [--jumprange ly] [--size padsize]
                                  [--max-jumps MAX_JUMPS] [--max-distance ls]
                                  [--minimum-supply MINIMUM_SUPPLY]
                                  [--path PATH] [--run]
                                  [--commodity-available commodity of interest]
                                  [--build-database] [--download-files]

optional arguments:
  -h, --help            show this help message and exit
  --cargo free cargo space, -c free cargo space
                        The maximum cargo space of your ship. Needs to be an
                        integer. Default will be 512.
  --jumprange ly, -j ly
                        The (laden) jumprange of your ship in ligthyears.
                        Default is 20 ly. A significant change requires
                        rebuilding of the database.
  --size padsize, -s padsize
                        The padsize your ship needs. Default is L. Use "M"
                        (without quotes) if you have a smaller ship. A change
                        requires rebuilding the database.
  --max-jumps MAX_JUMPS, -mj MAX_JUMPS
                        The maximum number of jumps you would perform (one
                        way) to get a commodity. Needs to be an integer.
                        Default is 8. A change requires rebuilding the
                        database.
  --max-distance ls, -md ls
                        The maximum distance (in lightseconds) a station shall
                        have from the point of entry into a system to be
                        considered. Default is 2500 ls. Needs to be an
                        integer. A change requires rebuilding the database.
  --minimum-supply MINIMUM_SUPPLY, -ms MINIMUM_SUPPLY
                        The minimum amount of (any) commodity that shall be
                        available at a station so that it will be considered
                        as to be relevant. Needs to be an integer. Default is
                        100.
  --path PATH, -p PATH  The path where the missions file can be found. Default
                        is the current directory. Needs to be stated ALWAYS if
                        it is NOT the current directory!
  --run, -r             Find ONE route that requires no revisiting of stations
                        or the fewest amount of revisiting. This will be the
                        default action and doesn't need to be stated.
  --commodity-available commodity of interest, -ca commodity of interest
                        Check if a commodity is available at relevant
                        stations. All other actions will be ignored if this is
                        set. < commodity > needs to be written as in the game.
  --build-database, -b  Force build the database. Needs to be done if the ship
                        or user parameters (e.g. the "home coordinates") have
                        changed significantly or if newer files were downloaded
                        manually. Will ignore < run >.
  --download-files, -d  Force download the necessary files from EDDB.io. Will
                        ignore < run >.
```

## Examples
If the necessary files are not present or older than 23 hours the following actions are always preceded by an automatic downloaded of said files and building of the database with the stated parameters. 
Also: short notation is used for most of the examples.

Basic usage after the database was build (see below if you have other values for the parameters than the default values).

    python3 trade_mission_optimizer.py

Basic usage if the database was build but your free cargo space is different to the default value (230 in this case).

    python3 trade_mission_optimizer.py -c 230

If the database is build and you want to know if a commodity (is available at relevant stations).  
ATTENTION: Use quotes if the commodity contains more than one word!    

    python3 trade_mission_optimizer.py -ca "Micro-Weave Cooling Hoses"

When the program is called for the first time that day the database needs to be build. Thus all parameters should be passed if the default values are not working for you. In this example the long notation is used.

    python3 trade_mission_optimizer.py --size M --max-jumps 4 --max-distance 5000
         --minumim-supply 500 --jumprange 23

If the database shall be rebuild with changed parameters. In this example the default values are used for max-distance, minimum-supply and max-jumps. When building the database, the exact cargo space of your ship is not of interest. To force the rebuilding of the database < -b > needs to be added to the parameters.  
ATTENTION: Re-building of the database is also required if the system of origin has changed significantly!

    python3 trade_mission_optimizer.py -s M -b

If you want to force download all files.  
ATTENTION: The database needs to be rebuild to consider the new data.

    python3 trade_mission_optimizer.py -d

# ATTENTION:
- The database can be up to a day old. Thus the availability of commodities is not guaranteed even if the file says so.
- The program neither determines the most profitable nor the shortest route (in ligthyears). It just finds a route that doesn't require visiting unnecessary stations or re-visiting any (mission) station. However since flying to a station, docking and undocking takes so much more time than jumping from system to system, the latter is of little importance. Dito, regarding the former since since missions usually pay well.
- It may be impossible to NOT visit some stations several times. In this case the the program determines the best run that requires the least amount of stations to be visited again. I've seen this happening just if the cargo hold is too small to finish all missions at once.
- The program will NOT consider commodities if the total amount needed for all missions is larger than the total cargo space.
- If two stations have the same commodity to be bought there, a station in orbit is ALWAYS preferred over planetary stations even if the former is much further away. The reason is that getting down to a planet (and up again) takes so much time.
- To consider a station as relevant it shall not be further away than the stated number for maximum jumps (from the origin location). Within the system its distance to arrival shall be less than the stated maximum distance. The default values (8 jumps and 2500 ls) are experience values that work well for me. However, if a commodity is rare, these may need to be different when the database is (re)build.
