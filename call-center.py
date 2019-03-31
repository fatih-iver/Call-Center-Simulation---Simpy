import random
import numpy
import simpy

RANDOM_SEED = 978
random.seed(RANDOM_SEED)

INTERARRIVAL_RATE = 14.3
MEAN_RENEGE =  60

MEAN_FRONT_DESK = 7.2
STD_FRONT_DEKS = 2.7

MEAN_EXPERT= 10.2

service_times_front_desk = [] 
service_times_expert = []

queue_w_times_front_desk = []
queue_w_times_expert = []

class Customer(object):
    def __init__(self, name, env, front_desk_operator, expert_operator):
        self.env = env
        self.name = name
        self.arrival_to_front_desk = None
        self.arrival_to_expert = None
        self.action = env.process(self.call())
    
    def call(self):
        print('%s initiated a call at %g' % (self.name, self.env.now))

        self.arrival_to_front_desk = self.env.now

        with front_desk_operator.request() as req:

            patience = random.expovariate(MEAN_RENEGE)

            results = yield req | env.timeout(patience)

            if req in results: 
                print('%s is assigned to the front desk operator at %g' % (self.name, self.env.now))
                queue_w_times_front_desk.append(self.env.now - self.arrival_to_front_desk)
                yield self.env.process(self.get_front_desk_service())
                print('%s is done with front desk operator at %g' % (self.name, self.env.now))
            else:
                print('%s is reneged from the queue of the front desk operator at %g' % (self.name, self.env.now))
                env.exit()

        self.arrival_to_expert = self.env.now

        with expert_operator.request() as req:
            
            patience = random.expovariate(MEAN_RENEGE)

            results = yield req | env.timeout(patience)

            if req in results: 
                print('%s is assigned to the expert operator at %g' % (self.name, self.env.now))
                queue_w_times_expert.append(self.env.now - self.arrival_to_expert)
                yield self.env.process(self.get_expert_service())
                print('%s is done with expert operator at %g' % (self.name, self.env.now))
            else:
                print('%s is reneged from the queue of the expert operator at %g' % (self.name, self.env.now))
                env.exit()

    def get_front_desk_service(self):
        #duration = numpy.random.lognormal(MEAN_FRONT_DESK, STD_FRONT_DEKS)
        duration = random.expovariate(MEAN_EXPERT)
        yield self.env.timeout(duration)
        service_times_front_desk.append(duration)

    def get_expert_service(self):
        duration = random.expovariate(MEAN_EXPERT)
        yield self.env.timeout(duration)
        service_times_expert.append(duration)

def customer_generator(env, front_desk_operator, expert_operator):
    for i in range(10):
        yield env.timeout(random.expovariate(INTERARRIVAL_RATE))
        Customer('Cust %s' % (i+1), env, front_desk_operator, expert_operator)  

env = simpy.Environment()
front_desk_operator = simpy.Resource(env, capacity = 1)
expert_operator = simpy.Resource(env, capacity = 1)
env.process(customer_generator(env, front_desk_operator, expert_operator))
env.run() 
