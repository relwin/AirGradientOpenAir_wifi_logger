"""
ag_gps.py

For running on LG phone w/termux.

Pull data from O1PST, assigned IP already on the router.
Write/append data as CSV to a file.
Reading GPS data from "termux-location" may take a few seconds, which limits sample rate.

https://github.com/airgradienthq/arduino/blob/master/docs/local-server.md

"""

import asyncio
import time
import subprocess
import json
import platform
import getopt, sys

from airgradient import AirGradientClient

AG_O1PST_IP = "192.168.0.134"  # my default test IP
CSV_OUTFILE_BASE = "agdata_"
# fake GPS for PC testing
gps_lat = 33.1
gps_long = -117.3
gps_lats = "33.1"
gps_longs = "-117.3"
gps_speed = 0
gps_speeds = "0"
Records_written = 0
O1PST_timeouts = 0


# returns str lat,long (not for PC, so stub)
def get_gps_location(stub=True):
    global gps_lat, gps_lats, gps_long, gps_longs, gps_speed, gps_speeds

    try:
        """
        {
            latitude": 33.1,
            "longitude": -117.3,
            "altitude": 23.4219970703125,
            "accuracy": 8.576000213623047,
            "vertical_accuracy": 24.0,
            "bearing": 0.0,
            "speed": 0.0,
            "elapsedMs": 7,
            "provider": "gps"
        }
        """
        if stub == False:
            location = subprocess.check_output(["termux-location", "-p", "gps"])
            location_data = json.loads(location)

            gps_lats = str(location_data['latitude'])
            gps_longs = str(location_data['longitude'])
            gps_speeds = str(location_data['speed'])
            gps_lat = location_data['latitude']
            gps_long = location_data['longitude']
            gps_speed = location_data['speed']
        else:
            # stubbed
            pass

    except Exception as e:
        print(f"Error while getting GPS coordinates: {e}")
    return gps_lat, gps_long


def fmt_header():
    csvout = 'time' + ','
    csvout = csvout + 'lat' + ','
    csvout = csvout + 'long' + ','
    csvout = csvout + 'speed' + ','
    csvout = csvout + "rco2" + ','
    csvout = csvout + "pm01" + ','
    csvout = csvout + "pm02" + ','
    csvout = csvout + "compensated_pm02" + ','
    csvout = csvout + "pm10" + ','
    csvout = csvout + "total_volatile_organic_component_index" + ','
    csvout = csvout + "pm003_count" + ','
    csvout = csvout + "nitrogen_index" + ','
    csvout = csvout + "compensated_ambient_temperature" + ','
    csvout = csvout + "compensated_relative_humidity" + '\n'
    # print(csvout)
    return csvout


def fmt_data(current):
    global gps_lat, gps_lats, gps_long, gps_longs, gps_speed, gps_speeds

    """
    print(current.rco2)
    print(current.pm01)
    print(current.pm02)
    print(current.raw_pm02)
    print(current.compensated_pm02)
    print(current.pm10)
    print(current.total_volatile_organic_component_index)
    print(current.raw_total_volatile_organic_component)
    print(current.pm003_count)
    print(current.nitrogen_index)
    print(current.raw_nitrogen)
    print(current.ambient_temperature)
    print(current.raw_ambient_temperature)
    print(current.compensated_ambient_temperature)
    print(current.raw_relative_humidity)
    print(current.relative_humidity)
    print(current.compensated_relative_humidity)
    """
    csvout = time.strftime("%H:%M:%S", time.localtime()) + ','
    csvout = csvout + gps_lats + ','
    csvout = csvout + gps_longs + ','
    csvout = csvout + gps_speeds + ','
    csvout = csvout + str(current.rco2) + ','
    csvout = csvout + str(current.pm01) + ','
    csvout = csvout + str(current.pm02) + ','
    csvout = csvout + str(current.compensated_pm02) + ','
    csvout = csvout + str(current.pm10) + ','
    csvout = csvout + str(current.total_volatile_organic_component_index) + ','
    csvout = csvout + str(current.pm003_count) + ','
    csvout = csvout + str(current.nitrogen_index) + ','
    csvout = csvout + str(current.compensated_ambient_temperature) + ','
    csvout = csvout + str(current.compensated_relative_humidity) + '\n'
    # print(csvout)
    return csvout


# show a few sampled items
def show_data(current):
    global gps_lat
    global gps_long
    print(time.strftime("%H:%M:%S", time.localtime()), f'{gps_lat:.2f}', f'{gps_long:.2f}', "CO2:", current.rco2,
          "PM02:", current.compensated_pm02, "NOx:", current.nitrogen_index)


# GET data from O1PST, returns False if unavailable (usually timeout)
async def ag_get(csv_file) -> bool:
    global Records_written, O1PST_timeouts
    try:
        async with AirGradientClient(AG_O1PST_IP) as client:
            measurements = await client.get_current_measures()
            # print(measurements)
            show_data(measurements)
            # don't write if timeout, otherwise "None" appears in the file
            if measurements.rco2 is not None:
                csv_file.write(fmt_data(measurements))
                Records_written += 1
            else:
                O1PST_timeouts += 1
            # config = await client.get_config()
            # print(config)
            return True
    except Exception as e:
        print(f"Error communicating with O1PST: {e}")
        return False


if __name__ == "__main__":
    samplerate = 1

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:s:", ["help", "addr=", "samprate="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)
    for o, a in opts:
        if o in ("-a", "--addr"):
            AG_O1PST_IP = a
        elif o in ("-s", "--samprate"):
            samplerate = float(a)
        elif o in ("-h", "--help"):
            print("AirGradient mobile data collection Help:\n-a IPaddr of AG\n-s sample rate in sec,typically >2")
            sys.exit()
        else:
            assert False, "unhandled option"
    # can't access phone items on PC
    if platform.system() == 'Windows':
        stub = True
    else:
        stub = False
    print("Connecting to O1PST:", AG_O1PST_IP)
    print("Ctrl-C to exit")
    # want date/ts appended to file
    fname = CSV_OUTFILE_BASE + time.strftime("%y_%m_%d_%H_%M_%S", time.localtime()) + ".csv"
    csv_file = open(fname, 'w')
    csv_file.write(fmt_header())
    print("Creating", fname)
    print("Sampling rate of", samplerate, 'seconds')

    while True:
        t0 = time.perf_counter()
        try:
            get_gps_location(stub)
            asyncio.run(ag_get(csv_file))
            csv_file.flush()
            elapset = time.perf_counter() - t0
            sleeptime = samplerate - elapset
            if sleeptime < 0.01:
                sleeptime = 0.01
            time.sleep(sleeptime)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    csv_file.close()
    print("Wrote", Records_written, "samples with", O1PST_timeouts, "timeouts")
