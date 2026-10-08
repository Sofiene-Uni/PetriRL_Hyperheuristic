import numpy as np

def get_utilization(sim):
     utilization = 0
     busy_machines= np.array( [bool(machine.token_container) for machine in sim.cache["machine_processing"]])
     utilization =  sum(busy_machines)/sim.n_machines
     
     return utilization   
 
def get_consumption(sim):
    consumption = 0
    busy_machines= np.array( [bool(machine.token_container) for machine in sim.cache["machine_processing"]])
    consumption =  np.dot(busy_machines , sim.machines_powers)
    return consumption


def get_buffer(sim):
   
    buffer_places=sim.cache["machine_buffer"]
    buffer_tokens = sum(len(b.token_container) for b in buffer_places)

    return  buffer_tokens