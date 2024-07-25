#!/usr/bin/env python
# coding: utf-8

# In[ ]:


pip install simpy


# In[2]:


import simpy
import random

class ContainerTerminal:
    no_of_crane=2
    no_of_truck=3
    no_of_berth=2
    no_of_container = 150

class Vessel:
    # Similar to constructor overloading in Java. If container count is passed then it uses the passed value or else default value
    def __init__(self, vessel_id, container_count=ContainerTerminal.no_of_container):
        self.vessel_id=vessel_id
        self.container_count=container_count
        
class Equipment:
    def __init__(self, env, capacity):
        self.env=env
        self.resource=simpy.Resource(env, capacity)
    
    def request(self):
        return self.resource.request()

    def release(self, request):
        self.resource.release(request)

class Crane(Equipment):
    def __init__(self, env, capacity):
        super().__init__(env, capacity)

    def lift_container(self, vessel_id, container_id):
        print(f"Time {self.env.now:.2f}: Crane starts lifting container {container_id} from vessel {vessel_id}.")
        yield self.env.timeout(3)  # Time taken by a crane to lift one container is 3 minutes

class Truck(Equipment):
    def __init__(self, env, capacity):
        super().__init__(env, capacity)

    def transport_container(self, vessel_id, container_id):
        print(f"Time {self.env.now:.2f}: Truck starts transporting container {container_id} from vessel {vessel_id} to yard block.")
        yield self.env.timeout(6)  # Time for truck to transport container and return
        print(f"Time {self.env.now:.2f}: Truck returned after dropping container {container_id} from vessel {vessel_id}.")

class ContainerTerminalWorking:
    def __init__(self, env):
        self.env=env
        self.berths=simpy.Resource(env, ContainerTerminal.no_of_berth)
        self.cranes=Crane(env, ContainerTerminal.no_of_crane)
        self.trucks=Truck(env, ContainerTerminal.no_of_truck)

    def unload_vessel(self, vessel):
        print(f"Time {self.env.now:.2f}: Vessel {vessel.vessel_id} enters waiting queue.")
        # Requesting berth for the vessel
        with self.berths.request() as berth:
            yield berth
            print(f"Time {self.env.now:.2f}: Vessel {vessel.vessel_id} berths.")
            # Requesting cranes if available and ensuring that a single crane is allocated to entire containers from a vessel by releasing the resource manually
            crane_request = self.cranes.request()
            yield crane_request
            try:
                for i in range(vessel.container_count):
                    yield self.env.process(self.cranes.lift_container(vessel.vessel_id, i + 1))
                    self.env.process(self.move_container(vessel.vessel_id, i + 1))
                    # Time taken by crane to look for a free truck
                    yield self.env.timeout(1)
            finally:
                # Releasing the Crane resource manually
                self.cranes.release(crane_request)
                print(f"Time {self.env.now:.2f}: Vessel {vessel.vessel_id} finishes unloading and leaves.")
                self.berths.release(berth)

    def move_container(self, vessel_id, container_id):
        with self.trucks.request() as truck_request:
            yield truck_request
            yield self.env.process(self.trucks.transport_container(vessel_id, container_id))

    def vessel_arrival(self):
        vessel_id=1
        while True:
            vessel=Vessel(vessel_id)
            self.env.process(self.unload_vessel(vessel))
            vessel_id+=1
            inter_arrival_time=random.expovariate(1 / 300)  # Average of 5 hours (300 minutes)
            yield self.env.timeout(inter_arrival_time)

# Initialize environment
env=simpy.Environment()

# Create the container_terminal_working obj
simulation = ContainerTerminalWorking(env)

# Start vessel arrival process
env.process(simulation.vessel_arrival())

# Run the simulation for 1440 minutes (24 hours)
env.run(until=1440)


# In[ ]:




