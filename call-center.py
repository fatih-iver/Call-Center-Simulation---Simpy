import random
import numpy as np

callNumber = 10

interArrivalTimeMean = 14.3 # Exponential (min)

recordingTimeMean = 7.2 # Normal (min)

recordingTimeSTD = 2.7 # Normal (min)

serviceTimeMean = 10.2 # Exponential (min)

numberOfBreaksMean = 8 # Poisson

interArrivalTimes = [random.expovariate(interArrivalTimeMean) for _ in range(callNumber)]

recordingTimes = [random.normalvariate(recordingTimeMean, recordingTimeSTD) for _ in range(callNumber)]

serviceTimes = [random.expovariate(serviceTimeMean) for _ in range(callNumber)]

takeBreak = random.choice([True, False])

numberOfBreaks = np.random.poisson(numberOfBreaksMean)

print(numberOfBreaks)
