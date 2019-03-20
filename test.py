import simpy
import random

PATIENCE_MEAN = 60
INTER_ARRIVAL_TIME_MEAN = 14.3
FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN = 7.2
FRONT_DESK_OPERATOR_SERVICE_TIME_STD = 2.7
EXPERT_OPERATOR_SERVICE_TIME_MEAN = 10.2


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
            yield self.environment.timeout(random.normalvariate(FRONT_DESK_OPERATOR_SERVICE_TIME_MEAN,
                                                                FRONT_DESK_OPERATOR_SERVICE_TIME_STD))
            print(f'{self.name} finished talking to the front desk operator at {self.environment.now}')

        with self.expert_operator.request() as request:
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
    for i in range(10):
        Customer(f'Customer {i+1}', environment, front_desk_operator, expert_operator)
        yield environment.timeout(random.expovariate(1 / INTER_ARRIVAL_TIME_MEAN))


environment = simpy.Environment()
front_desk_operator = simpy.Resource(environment, capacity=1)
expert_operator = simpy.Resource(environment, capacity=1)
environment.process(generate_customers(environment, front_desk_operator, expert_operator))
environment.run()
