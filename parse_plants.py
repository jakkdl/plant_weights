"""do fancy math on my plant weights"""
import datetime
import re
from typing import TypeAlias, Iterable
from collections import defaultdict

#import numpy as np
#fit = np.polynomial.polynomial.Polynomial.fit

FILE = "foo2.csv"

PlantLabel : TypeAlias = tuple[str, int]
PlantInfo : TypeAlias = defaultdict[datetime.date, list[int]]
Plants : TypeAlias = dict[PlantLabel, PlantInfo]

def read_plants(filename: str='plants.csv') -> Plants:
    with open(filename, encoding="utf-8") as file:
        labelline = file.readline().strip().split(",")
        datalines = [l.strip().split(",") for l in file.readlines()]
    labels : list[PlantLabel] = []

    for strlabel in labelline[1:]:
        if strlabel == '':
            continue
        reg = re.search(r'\d', strlabel)
        if not reg:
            labels.append((strlabel, 1))
        else:
            numindex = reg.start()
            labels.append((strlabel[:numindex].strip(), int(strlabel[numindex:])))
    data : Plants = {label: defaultdict(list) for label in labels}

    lastdate : datetime.date|None = None
    for line in datalines:
        date: datetime.date
        if line[0] == "":
            assert lastdate is not None
            date = lastdate
        else:
            lastdate = date = todate(line[0])

        for label, weight in zip(labels, line[1:], strict=False):
            if not weight.strip():
                continue
            data[label][date].append(int(weight.strip()))

    return data

def write_plants(data: Plants, filename='plants.csv') -> None:
    sortedkeys = sorted(data.keys())
    lines = ['date,' + ','.join(map(lambda x:' '.join(map(str, x)), sortedkeys))]
    dates = sorted(set(k for d in data.values() for k in d.keys()))
    for date in dates:
        newlines: tuple[list[str], list[str]] = ([], [])
        for key in sortedkeys:
            plant: PlantInfo = data[key]
            weights: list[int] = plant[date]
            newlines[0].append(' '*4)
            newlines[1].append(' '*4)
            for weight, line in zip(weights, newlines):
                line[-1] = f'{str(weight):>4}'
        lines.append(','.join((str(date), *newlines[0])))
        lines.append(','.join((' '*len(str(date)), *newlines[1])))
        if not re.search(r'\d', lines[-1]):
            del lines[-1]

    with open(filename, 'w', encoding='utf-8') as file:
        file.write('\n'.join(lines) + '\n')



def todate(datestr: str) -> datetime.date:
    """convert a YYYY/MM/DD string into a datetime.date"""
    if re.match(r'\d\d/\d\d/\d\d\d\d', datestr):
        month, day, year = map(int, datestr.split('/'))
    else:
        year, month, day = map(int, datestr.split('-'))
    return datetime.date(year, month, day)

def dayround(stamp: datetime.datetime) -> int:
    return int(stamp.timestamp() // 86400 * 86400)

def unixdate(date: datetime.date) -> int:
    return dayround(datetime.datetime(date.year, date.month, date.day))

def get_last_watering(data: Plants) -> list[int]:
    sortedlabels = sorted(data)
    last_watering: list[int] = []

    for label in sortedlabels:
        plantdata = data[label]
        sorted_dates = sorted(plantdata.keys())
        if not sorted_dates:
            last_watering.append(dayround(datetime.datetime.now()))
            continue
        lastdate = sorted_dates[0]
        lastweight = plantdata[sorted_dates[0]][0]
        for date in sorted_dates:
            vals = plantdata[date]
            weight = plantdata[date][0]
            if len(vals) > 1:
                lastdate = date
                lastweight = plantdata[date][1]
                continue
            if weight > lastweight:
                lastdate = date
            lastweight = weight
        last_watering.append(unixdate(lastdate))
    return last_watering

def tasker_helper(filename='output.csv'):
    data = read_plants()
    names: list[str] = sorted({l[0] for l in data})
    sortedlabels = sorted(data)

    offset: list[int] = [0] * len(names)
    nums: list[list[int]] = [[] for _ in names]

    # build nums
    for i, label in enumerate(sortedlabels):
        nums[names.index(label[0])].append(label[1])

    # build offset
    sorted_not_unique_names = [l[0] for l in sorted(data)]
    for i, name in enumerate(names):
        offset[i] = sorted_not_unique_names.index(name)

    # build max & minvals
    maxvals: list[int] = []
    minvals: list[int] = []

    for label in sortedlabels:
        weights: Iterable[list[int]] = data[label].values()
        if not weights:
            maxvals.append(0)
            minvals.append(0)
            continue
        maxvals.append(max(max(weights, key=max)))
        #maxvals.append(max(map(max, weights))) #type: ignore
        #maxvals.append(np.max(weights)) #type: ignore
        minvals.append(min(min(weights, key=min)))

    last_watering = get_last_watering(data)

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(','.join(names)+'\n')
        for values in (offset,maxvals, minvals, last_watering, *nums):
            file.write(','.join(map(str, values))+'\n')

# create datasets
# each dataset consists of a plant and a start date,
# and then a list of tuples of X (days since watering) and Y (weight).
#def do_fancy_numpy_stuff(): #pylint: disable=too-many-locals
#    """do the stuff"""
#    with open(FILE, encoding="utf-8") as file:
#        header = file.readline().strip().split(",")
#        datalines = [l.strip().split(",") for l in file.readlines()]
#
#    data: dict[tuple[str, datetime.date], list[tuple[int, int]]] = {}
#    for line in datalines:
#        label = ""
#        lastdate: datetime.date | None = None
#        lastval = 0
#        points: list[tuple[int, int]]
#        startdate: datetime.date | None = None
#        for field, value in zip(header, line):
#            match field:
#                case "min" | "max" | "last cell" | "current" | "wetness":
#                    continue
#                case "label":
#                    label = value
#                    continue
#                case "":
#                    assert lastdate is not None
#                    date = lastdate
#                case _:
#                    lastdate = date = todate(field)
#            if not value:
#                continue
#            intval = int(value)
#            if intval > lastval:
#                points = [(0, intval)]
#                data[(label, date)] = points
#                startdate = date
#            else:
#                assert startdate is not None
#                days_passed = int((date - startdate).total_seconds() / 86400)
#                points.append((days_passed, intval))
#            lastval = intval
#    long_data = {k: v for k,v in data.items() if len(v) > 5}
#    for key,val in long_data.items():
#        days, weights = zip(*val)
#        res = fit(days, weights, deg=2).coef
#
#        print(key, res)

def main():
    print(read_plants())
    #tasker_helper()

if __name__ == "__main__":
    main()
