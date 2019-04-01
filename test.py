import simpy
import random
import numpy as np
import math

# CONSTANTS
PATIENCE_MEAN = 60
INTER_ARRIVAL_TIME_MEAN = 14.3
FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN = 7.2
FRONT_DESK_OPERATOR_SERVICE_TIME_STD = 2.7
EXPERT_OPERATOR_SERVICE_TIME_MEAN = 10.2
EXPERT_OPERATOR_BREAK_RATE = 60
EXPERT_OPERATOR_BREAK_TIME = 3
SHIFT_DURATION = 480
HIGH_PRIORITY = 0
LOW_PRIORITY = 1
CUSTOMER_COUNT = 1000

FRONT_OPERATOR_SIGMA = (math.log((FRONT_DESK_OPERATOR_SERVICE_TIME_STD / FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN)**2 + 1))**0.5

FRONT_OPERATOR_MU = math.log(FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN) - 0.5 * math.log((FRONT_DESK_OPERATOR_SERVICE_TIME_STD / FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN)**2 + 1)


print(FRONT_OPERATOR_MU, FRONT_OPERATOR_SIGMA)
# TODO STATS
front_desk_operator_busy_time = 0
expert_operator_busy_time = 0
front_desk_operator_waiting_times = [0] * CUSTOMER_COUNT
expert_operator_waiting_times = [0] * CUSTOMER_COUNT
total_system_times = [0] * CUSTOMER_COUNT
total_shift_time = 0


class Customer:
    customers_served_or_reneged = CUSTOMER_COUNT

    def __init__(self, id, environment, front_desk_operator, expert_operator):
        self.id = id
        self.name = f'Customer {self.id}'
        self.environment = environment
        self.front_desk_operator = front_desk_operator
        self.expert_operator = expert_operator
        self.action = self.environment.process(self.call())

    def call(self):
        global front_desk_operator_busy_time, expert_operator_busy_time, \
            front_desk_operator_waiting_times, expert_operator_waiting_times, total_system_times

        print(f'{self.name} initiated call at {self.environment.now}')
        total_system_time_start = self.environment.now
        front_desk_operator_wait_start = self.environment.now
        with self.front_desk_operator.request() as request:
            yield request 
            front_desk_operator_wait_end = self.environment.now
            front_desk_operator_waiting_times[self.id] = front_desk_operator_wait_end - front_desk_operator_wait_start

            front_desk_operator_busy_time_start = self.environment.now
            print(f'{self.name} started talking to the front desk operator at {self.environment.now}')
            # TODO lognormal random variable
            yield self.environment.timeout(abs(random.lognormvariate(FRONT_OPERATOR_MU,
                                                                    FRONT_OPERATOR_SIGMA)))

            front_desk_operator_busy_time_end = self.environment.now
            front_desk_operator_busy_time += front_desk_operator_busy_time_end - front_desk_operator_busy_time_start
            print(f'{self.name} finished talking to the front desk operator at {self.environment.now}')

        expert_operator_wait_start = self.environment.now
        with self.expert_operator.request(HIGH_PRIORITY) as request:
            patience = random.expovariate(1 / PATIENCE_MEAN)
            results = yield request | self.environment.timeout(patience)

            expert_operator_wait_end = self.environment.now
            expert_operator_waiting_times[self.id] = expert_operator_wait_end - expert_operator_wait_start

            if request not in results:
                print(f'{self.name} reneged at {self.environment.now} after waiting '
                      f'for {patience} minutes on the expert operator\'s queue')
                total_system_time_end = self.environment.now
                total_system_times[self.id] = total_system_time_end - total_system_time_start
                Customer.customers_served_or_reneged -= 1
                self.environment.exit()

            expert_operator_busy_time_start = self.environment.now
            print(f'{self.name} started talking to the expert operator at {self.environment.now}')
            yield self.environment.timeout(random.expovariate(1 / EXPERT_OPERATOR_SERVICE_TIME_MEAN))

            expert_operator_busy_time_end = self.environment.now
            expert_operator_busy_time += expert_operator_busy_time_end - expert_operator_busy_time_start

            print(f'{self.name} finished talking to the expert operator at {self.environment.now}')

        total_system_time_end = self.environment.now
        total_system_times[self.id] = total_system_time_end - total_system_time_start
        Customer.customers_served_or_reneged -= 1


def generate_customers(environment, front_desk_operator, expert_operator):
    for i in range(CUSTOMER_COUNT):
        Customer(i, environment, front_desk_operator, expert_operator)
        yield environment.timeout(random.expovariate(1 / INTER_ARRIVAL_TIME_MEAN))


def generate_expert_breaks(environment, expert_operator):
    while True:
        # TODO poisson random number without numpy
        next_break_time = np.random.poisson(EXPERT_OPERATOR_BREAK_RATE)
        try:
            yield environment.timeout(next_break_time)
        except simpy.Interrupt:
            print('timeout break')
            environment.exit()

        with expert_operator.request(LOW_PRIORITY) as request:
            print(f'Expert operator requested break at {environment.now} after {next_break_time} minutes')
            try:
                yield request
            except simpy.Interrupt:
                print('request')
                environment.exit()

            print(f'Expert operator started break at {environment.now}')
            try:
                yield environment.timeout(EXPERT_OPERATOR_BREAK_TIME)
            except simpy.Interrupt:
                print('break')
                environment.exit()

            print(f'Expert operator finished break at {environment.now}')


def generate_shifts(environment, expert_break_process):
    shift_count = 1
    while Customer.customers_served_or_reneged != 0:
        print(f'Shift {shift_count} started at {environment.now}')
        yield environment.timeout(SHIFT_DURATION)
        print(f'Shift {shift_count} ended at {environment.now}')
        shift_count += 1
    expert_break_process.interrupt()

    global total_shift_time
    total_shift_time = SHIFT_DURATION * (shift_count - 1)


environment = simpy.Environment()
front_desk_operator = simpy.Resource(environment, capacity=1)
expert_operator = simpy.PriorityResource(environment, capacity=1)
customer_process = environment.process(generate_customers(environment, front_desk_operator, expert_operator))
expert_break_process = environment.process(generate_expert_breaks(environment, expert_operator))
shift_process = environment.process(generate_shifts(environment, expert_break_process))
environment.run()

total_waiting_times = [front_desk_operator_waiting_times[i] + expert_operator_waiting_times[i] for i in range(CUSTOMER_COUNT)]

front_desk_operator_utilization = front_desk_operator_busy_time / total_shift_time
expert_operator_utilization = expert_operator_busy_time / total_shift_time
avg_total_waiting_time = (sum(total_waiting_times)) / CUSTOMER_COUNT
max_waiting_to_system_time_ratio = max([total_waiting_times[i]/total_system_times[i] for i in range(CUSTOMER_COUNT)])


print(front_desk_operator_utilization)
print(expert_operator_utilization)
print(avg_total_waiting_time)
print(max_waiting_to_system_time_ratio)
