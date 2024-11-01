import simpy
import random
import matplotlib.pyplot as plt

# Simulation parameters
RANDOM_SEED = 42
SIM_TIME = 500      
LAMBDA = 1 / 4      
MU = 1 / 5          
NUM_MACHINES = 2    
REPAIR_DURATION = 30 
REPAIR_INTERVAL_MIN = 40 
REPAIR_INTERVAL_MAX = 60 

# Tracking variables
wait_times = []
queue_lengths = []
queue_time = []
processed_cars = 0
busy_time = 0

class CarwashMM2:
    """A carwash with two washing machines (M/M/2 system)."""
    def __init__(self, env, num_machines):
        self.env = env
        self.machine = simpy.Resource(env, num_machines)  # Two machines for M/M/2

    def wash(self, car):
        """Simulate the carwash process with exponential service time."""
        service_time = random.expovariate(MU)
        yield self.env.timeout(service_time)
        print(f"Car {car} washed in {service_time:.2f} minutes.")

def car(env, carwash, name):
    """A car arrives at the carwash and waits if necessary to be washed."""
    global busy_time, processed_cars

    arrival_time = env.now
    print(f'Car {name} arrives at {env.now:.2f}.')
    
    with carwash.machine.request() as request:
        yield request  # Wait for one of the machines to be available
        
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)
        
        start_busy_time = env.now
        yield env.process(carwash.wash(name))  # Car is being washed
        end_busy_time = env.now
        
        busy_time += end_busy_time - start_busy_time
        processed_cars += 1

def setup(env, carwash):
    """Generate cars arriving according to a Poisson process (M/M/2 arrival)."""
    car_count = 0
    while True:
        interarrival_time = random.expovariate(LAMBDA)  # Poisson arrivals
        yield env.timeout(interarrival_time)
        car_count += 1
        env.process(car(env, carwash, car_count))

def track_queue_length(env, carwash):
    """Track queue length over time."""
    while True:
        queue_lengths.append(len(carwash.machine.queue))
        queue_time.append(env.now)
        yield env.timeout(1)  # Check the queue length every minute

def staggered_repair_person(env, carwash):
    """Simulate a repair person who repairs one machine at a time, leaving at least one operational."""
    while True:
        # Wait for a random time before the repair person arrives
        repair_interval = random.randint(REPAIR_INTERVAL_MIN, REPAIR_INTERVAL_MAX)
        yield env.timeout(repair_interval)
        
        print(f'Repair person arrives at {env.now:.2f} to repair one machine.')

        # Take the first machine offline for repair
        with carwash.machine.request() as req1:
            print(f'One machine taken offline at {env.now:.2f} for repairs.')
            yield req1  # One machine is offline
            yield env.timeout(REPAIR_DURATION // 2)  # Staggered repair duration for first machine
            
        print(f'First machine repaired at {env.now:.2f}. Now repairing second machine.')

        # Take the second machine offline for repair after the first one is back online
        with carwash.machine.request() as req2:
            print(f'Second machine taken offline at {env.now:.2f} for repairs.')
            yield req2  # The second machine is offline now
            yield env.timeout(REPAIR_DURATION // 2)  # Staggered repair duration for second machine

        print(f'Both machines back online at {env.now:.2f}.')

def calculate_metrics():
    """Calculate and display M/M/2 queuing metrics."""
    avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
    avg_queue_length = sum(queue_lengths) / len(queue_lengths) if queue_lengths else 0

    # Correct utilization for M/M/2 system
    utilization = busy_time / (SIM_TIME * NUM_MACHINES)  # Adjusted for 2 machines

    # Throughput: how many cars processed per unit time
    throughput = processed_cars / SIM_TIME

    # Display results
    print(f"\n--- Metrics ---")
    print(f"Average wait time: {avg_wait_time:.2f} minutes")
    print(f"Average queue length: {avg_queue_length:.2f} cars")
    print(f"Utilization (fraction of time machines were busy): {utilization:.2f}")
    print(f"Throughput: {throughput:.2f} cars per minute")
    print(f"Total cars processed: {processed_cars}")
    print(f"Total simulation time: {SIM_TIME} minutes")

def plot_graphs():
    """Plot queue lengths and wait times."""
    plt.figure(figsize=(10, 5))
    
    # Plot queue length over time
    plt.subplot(1, 2, 1)
    plt.plot(queue_time, queue_lengths, label='Queue Length')
    plt.title('Queue Length Over Time')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Cars in Queue')
    plt.legend()
    
    # Plot wait times for each car
    plt.subplot(1, 2, 2)
    plt.plot(range(len(wait_times)), wait_times, label='Wait Time', color='orange')
    plt.title('Wait Time for Each Car')
    plt.xlabel('Car Number')
    plt.ylabel('Wait Time (minutes)')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

# Setup and run the simulation
print("Carwash M/M/2 Simulation with Two Machines and Staggered Repairs")
random.seed(RANDOM_SEED)

env = simpy.Environment()
carwash = CarwashMM2(env, NUM_MACHINES)
env.process(setup(env, carwash))
env.process(track_queue_length(env, carwash))
env.process(staggered_repair_person(env, carwash))  # Add the staggered repair process
env.run(until=SIM_TIME)

# Calculate and print the metrics
calculate_metrics()

# Plot the graphs
plot_graphs()