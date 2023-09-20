# Connected-Vehicle-Identification



How to run the code:

    1. Download the whole package for all jetson nanos
    2. Set up all jetson nanos(wirless hotspots, GPS unit, TOF sensor)
    3. Run server.py on eagle vehicle first
    4. Then run client .py on all other jetsons
    5. If it does not crush and you can see some output the code is running successfully

Problems might encounter:
1. If error mentioned cannot find a serial port: check the connection of the hardware
2. If error occur with some serial port denied: use sudo chmod 777 /dev/ttyACM0 to authorize

Hardware used for connection:

1. Jeston nanos
2. SparkFun GPS sensor, can refer to there website and github for further usage
3. Terabee TOF sensor, can refer to there website and github for further usage
