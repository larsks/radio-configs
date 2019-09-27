bands_by_name = {}


class Band:
    def __init__(self, name, low, high,
                 offset=0, aliases=None, step=5.0):
        self.name = name
        self.low = float(low)
        self.high = float(high)
        self.offset = float(offset)
        self.step = float(step)

        bands_by_name[name] = self

        if aliases is not None:
            for alias in aliases:
                bands_by_name[alias] = self

    def __repr__(self):
        return '<Band {0.name} {0.low}-{0.high}>'.format(self)


band_list = [
    Band('2200m', 0.1357, 0.1378),
    Band('630m', 0.472, 0.479),
    Band('160m', 1.8, 2.0),
    Band('80m', 3.5, 4.0),
    Band('60m', 5.3305, 5.405),
    Band('40m', 7.0, 7.3),
    Band('30m', 10.1, 10.15),
    Band('20m', 14.0, 14.350),
    Band('17m', 18.068, 18.168),
    Band('15m', 21.0, 21.45),
    Band('12m', 24.89, 24.99),
    Band('10m', 28.0, 29.7),
    Band('6m', 50.0, 54.0, offset=0.600),
    Band('2m', 144.0, 148.0, offset=0.600, step=5.0),
    Band('1.25m', 219.0, 225.0, offset=1.6, step=25.0),
    Band('70cm', 420.0, 450.0, offset=5),
    Band('33cm', 902.0, 928.0, offset=12),
    Band('23cm', 1240.0, 1300.0),
]


def freq_to_band(freq):
    for band in band_list:
        if band.low <= float(freq) <= band.high:
            return band
