import numpy as np
import pandas as pd
import pdb
from scipy.stats.distributions import chi2


class Preceding_vehicles:
    def __init__(self):
        self._n = 0
        self._k = 1
        self._time = 0
        self._candidate = []

    def run_step(self, sensor_info):
        # hr: sensor measured  distance
        # vr: sensor measured  speed
        hr = sensor_info[-1][0]
        vr = sensor_info[-1][1]
        self._hr = hr
        self._vr = vr


class PVIS:
    def __init__(self, Nmax=53, Kmax=9, alphaD=0.0267, alphaV=0.0102, ehg=2.5, ehr=0.1, evg=0.2, evr=0.1,
                 stop_mark=1,l=0):
        # parameters
        self._stop = False
        self._stopMark = stop_mark
        self._count = 0
        self._l = l
        self._Nmax = Nmax
        self._Kmax = Kmax
        self._threD = chi2.ppf(1 - alphaD, df=1)
        self._threV = chi2.ppf(1 - alphaV, df=1)

        self._Eh = np.sqrt(ehg ** 2 + ehr ** 2)
        self._Ev = np.sqrt(evg ** 2 + evr ** 2)

        # preceding vehicles that sensor measure
        self._preceding = Preceding_vehicles()

    def run_step(self, dict_V2V, sensor_info):
        # dict_GPS with key port ID and value of three items shown as follows
        # dhg: GPS-measured longitudinal from connected vehicle
        # dvg: GPS-measured longitudinal speed from connected vehicle

        # sensore measurment
        self._preceding.run_step(sensor_info)
        print('n={}, k={}\nMatching sensor: d={} m, v={} m/s'.format(self._preceding._n,self._preceding._k,round(self._preceding._hr+self._l,2),round(self._preceding._vr,2)))

        # matching GPS and sensor
        temp_candidate = []
        # pdb.set_trace()
        for port in dict_V2V:
            if not isinstance(port,int):
                continue
            # check if it is candidate
            candididate_flag = self.matching(self._preceding, dict_V2V[port])
            print(f"Port:{port}, GPS signal d={dict_V2V[port][-1][0]:.2f} m, v={dict_V2V[port][-1][1]:.2f} m/s")

            # if it is
            if candididate_flag == True:
                if len(self._preceding._candidate) > 0:
                    temp_candidate.append(port)
                    self._preceding._candidate = np.intersect1d(self._preceding._candidate, temp_candidate)
                    self._preceding._candidate = self._preceding._candidate.tolist()
                else:
                    temp_candidate.append(port)
                    self._preceding._candidate.append(port)

            # if it it not
            elif candididate_flag == False and port in self._preceding._candidate:
                self._preceding._candidate.remove(port)
        print("\n")
        self._preceding._n = self._preceding._n + 1
        n = self._preceding._n
        k = self._preceding._k
        
        if self._preceding._n == self._Nmax and len(self._preceding._candidate) == 1:
            self._preceding._time = self._preceding._time + self._preceding._n
            self._count = self._count + 1
            print(
                '{} Identifcations Done.\nFirst preceding vehicle is connected and the port ID is {}.\nThe total step is {}\n'.format(self._count,self._preceding._candidate[0], self._preceding._time))
            self._preceding._k = 1
            self._preceding._n = 0
            self._preceding._time = 0
            self._preceding._candidate = []
            if self._count >= self._stopMark:
                self._stop = True
        elif self._preceding._n == self._Nmax and len(self._preceding._candidate) != 1:
            self._preceding._time = self._preceding._time + self._preceding._n 
            self._preceding._k = self._preceding._k + 1
            self._preceding._n = 0
            self._preceding._candidate = []
        elif len(self._preceding._candidate) == 0:
            self._preceding._time = self._preceding._time + self._preceding._n 
            self._preceding._k = self._preceding._k + 1
            self._preceding._n = 0

        if self._preceding._k == self._Kmax:
            self._preceding._time = self._preceding._time + self._preceding._n 
            self._count = self._count + 1
            print('{} Identifcations Done. First preceding vehicle is unconnected \nThe total step is {}\n'.format(self._count,self._preceding._time))
            self._preceding._k = 1
            self._preceding._n = 0
            self._time = 0
            self._preceding._candidate = []
            if self._count >= self._stopMark:
                self._stop = True 
        return self._stop, n, k

    def matching(self, target_vehicle, dict_V2V):
        hg, vg = dict_V2V[-1]
        candididate_flag = False
        #pdb.set_trace() 
        if ((hg - self._l - target_vehicle._hr) / self._Eh) ** 2 <= self._threD \
                and ((vg - target_vehicle._vr) / self._Ev) ** 2 <= self._threV:
            candididate_flag = True
        return candididate_flag


if __name__ == '__main__':

    np.random.seed(1)
    # errors settings
    er = 0.1
    evr = 0.1
    eg = 1
    evg = 0.2

    # example data load
    df = pd.read_csv('sample_A.csv', header=None)
    data = df.to_numpy()
    time = np.unique(data[:, 1])
    res, ind = np.unique(data[:, 0], return_index=True)
    ID = res[np.argsort(ind)]

    # PVIS initalization
    dict_V2V = {}
    for i in range(len(ID) - 1):
        dict_V2V.update({ID[i + 1]: []})
    sensor_info = []
    PVIS_example = PVIS()

    # PVIS Procedure
    sz = data.shape
    for i in range(len(time)):
        # ego info
        data_time = data[(data[:, 1] == time[i]), :]
        y, x = data_time[0, 2:4]

        # ego sensor
        temp_data = data_time[data_time[:, -1] == 2, :]
        temp_data[:, 3] = temp_data[:, 3] - x
        temp_data = temp_data[temp_data[:, 3] > 0, 2:5]
        yp, xp, vp = temp_data[temp_data[:, 1].argsort()][0]
        hr = np.sqrt((xp) ** 2 + (y - yp) ** 2) + np.random.normal(0, er)
        vr = vp + np.random.normal(0, evr)
        sensor_info.append([hr, vr])

        # V2V comminication
        for j in range(data_time.shape[0] - 1):
            yc, xc, vc = data_time[j + 1, 2:5]
            vg = vc + np.random.normal(0, evg)
            hg = np.sqrt((x - xc) ** 2 + (y - yc) ** 2) + np.random.normal(0, eg)

            dict_V2V[data_time[j + 1, 0]].append([hg, vg])

        status = PVIS_example.run_step(dict_V2V, sensor_info)
        if status == True:
            break











