For collecting data from an AirGradient O-1PST air quality monitor over wifi using an Android phone running termux. Also logs GPS location.
Based on AG's demo python code.
This will also run on Windows for testing -- no GPS logging.

Setup
1) install termux and python on an Android phone.
2) Determine the O-1PST IP address. If using a router you can easily set this. For the phone's Hot-Spot wifi -- TBD (not tested.)
3) run this python script in a termux command window, see its Help for options.
4) a logfile "agdata_xxx.csv" is created.
5) ^C to stop logging/exit.
