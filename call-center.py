import random
import numpy
import simpy

RANDOM_SEED = 978

INTERARRIVAL_RATE = 14.3
MEAN_RENEGE =  60

MEAN_FRONT_DESK = 7.2
STD_FRONT_DEKS = 2.7

MEAN_EXPERT= 10.2

MEAN_BREAK = 60

BREAK_DURATION = 3

SERVICE_RANGE = [50, 90]
random.seed(RANDOM_SEED)

service_times_front_desk = [] 
service_times_expert = []

queue_w_times_front_desk = []
queue_w_times_expert = []

HIGH = 1
LOW = 2

CUSTOMER_NUMBER = 1000

class Customer(object):

    total_customer = 0

    def __init__(self, name, env, front_desk_operator, expert_operator, action_break_generator):
        self.env = env
        self.name = name
        self.arrival_to_front_desk = None
        self.arrival_to_expert = None
        self.action = env.process(self.call())
        self.action_break_generator = action_break_generator
    
    def call(self):

        Customer.total_customer += 1
        
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

        with expert_operator.request(priority = HIGH) as req:
            
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

        if Customer.total_customer == CUSTOMER_NUMBER and self.action_break_generator.is_alive:
          self.action_break_generator.interrupt()

    def get_front_desk_service(self):
        #duration = numpy.random.lognormal(MEAN_FRONT_DESK, STD_FRONT_DEKS)
        duration = random.expovariate(MEAN_EXPERT)
        yield self.env.timeout(duration)
        service_times_front_desk.append(duration)

    def get_expert_service(self):
        duration = random.expovariate(MEAN_EXPERT)
        yield self.env.timeout(duration)
        service_times_expert.append(duration)

def customer_generator(env, front_desk_operator, expert_operator, action_break_generator):
    for i in range(CUSTOMER_NUMBER):
        yield env.timeout(random.expovariate(INTERARRIVAL_RATE))
        Customer('Cust %s' % (i+1), env, front_desk_operator, expert_operator, action_break_generator)  

def break_generator(env, front_desk_operator, expert_operator):
    try:
        while True:
            duration = numpy.random.poisson(MEAN_BREAK)
            yield env.timeout(duration)
            print("Expert operator has dediced to give break at", env.now)
            with expert_operator.request(priority = LOW) as req:
                yield req
                print("Expert operator has started to the break at", env.now)
                yield env.timeout(BREAK_DURATION)
                print("Expert operator has finished the break at", env.now)
    except simpy.Interrupt:
        print('Expert will no longer give breaks')

env = simpy.Environment()
front_desk_operator = simpy.Resource(env, capacity = 1)
expert_operator = simpy.PriorityResource(env, capacity = 1)
action_break_generator = env.process(break_generator(env, front_desk_operator, expert_operator))
env.process(customer_generator(env, front_desk_operator, expert_operator, action_break_generator))

env.run() 
