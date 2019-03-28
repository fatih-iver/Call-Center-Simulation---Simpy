import simpy
import random
import numpy as np

# CONSTANTS
PATIENCE_MEAN = 60
INTER_ARRIVAL_TIME_MEAN = 14.3
FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN = 7.2
FRONT_DESK_OPERATOR_SERVICE_TIME_STD = 2.7
EXPERT_OPERATOR_SERVICE_TIME_MEAN = 10.2
EXPERT_OPERATOR_BREAK_RATE = 60
EXPERT_OPERATOR_BREAK_TIME = 3
SHIFT_DURATION = 480
HIGH_PROBABILITY = 0
LOW_PROBABILITY = 1
CUSTOMER_COUNT = 150


# TODO STATS
front_desk_operator_busy_time = 0
expert_operator_busy_time = 0
front_desk_operator_waiting_times = {}
expert_operator_waiting_times = {}




class Customer:
    def __init__(self, name, environment, front_desk_operator, expert_operator):
        self.name = name
        self.environment = environment
        self.front_desk_operator = front_desk_operator
        self.expert_operator = expert_operator
        self.action = self.environment.process(self.call())

    def call(self):
        print(f'{self.name} initiated call at {self.environment.now}')

        with self.front_desk_operator.request() as request:
            patience = random.expovariate(1 / PATIENCE_MEAN)
            results = yield request | self.environment.timeout(patience)

            if request not in results:
                print(f'{self.name} reneged at {self.environment.now} after waiting '
                      f'for {patience} minutes on the front desk operator\'s queue')
                self.environment.exit()

            print(f'{self.name} started talking to the front desk operator at {self.environment.now}')
            # TODO lognormal random variable
            yield self.environment.timeout(abs(random.normalvariate(FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN,
                                                                FRONT_DESK_OPERATOR_SERVICE_TIME_STD)))
            print(f'{self.name} finished talking to the front desk operator at {self.environment.now}')

        with self.expert_operator.request(HIGH_PROBABILITY) as request:
            patience = random.expovariate(1 / PATIENCE_MEAN)
            
            results = yield request | self.environment.timeout(patience)

            if request not in results:
                print(f'{self.name} reneged at {self.environment.now} after waiting '
                      f'for {patience} minutes on the expert operator\'s queue')
                self.environment.exit()

            print(f'{self.name} started talking to the expert operator at {self.environment.now}')
            yield self.environment.timeout(random.expovariate(1 / EXPERT_OPERATOR_SERVICE_TIME_MEAN))
            print(f'{self.name} finished talking to the expert operator at {self.environment.now}')


def generate_customers(environment, front_desk_operator, expert_operator):
    for i in range(CUSTOMER_COUNT):
        Customer(f'Customer {i+1}', environment, front_desk_operator, expert_operator)
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

        with expert_operator.request(LOW_PROBABILITY) as request:
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


def generate_shifts(environment, customer_process, expert_break_process):
    shift_count = 1
    while customer_process.is_alive:
        print(f'Shift {shift_count} started at {environment.now}')
        yield environment.timeout(SHIFT_DURATION)
        print(f'Shift {shift_count} ended at {environment.now}')
        shift_count += 1
    expert_break_process.interrupt()
    


environment = simpy.Environment()
front_desk_operator = simpy.Resource(environment, capacity=1)
expert_operator = simpy.PriorityResource(environment, capacity=1)
customer_process = environment.process(generate_customers(environment, front_desk_operator, expert_operator))
expert_break_process = environment.process(generate_expert_breaks(environment, expert_operator))
shift_process = environment.process(generate_shifts(environment, customer_process, expert_break_process))
environment.run()
