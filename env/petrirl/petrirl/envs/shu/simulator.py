import numpy as np
import random
from petrirl.envs.shu.petri_build import Petri_build
from petrirl. render.graph import  Graph
from petrirl. utils.obs import get_obs_basic
from petrirl. utils.twin import create_twin
from petrirl.envs.shu.algos import init_heuristics



import warnings
warnings.filterwarnings("ignore", message=".*env.action_masks to get variables from other wrappers is deprecated.*")



class Simulator(Petri_build):
    """
        Class representing the core logic of a Job Shop Scheduling Problem (JSSP) simulation using a Petri net.
        
        Attributes:
            clock (int): The internal clock of the simulation.
            interaction_counter (int): Counter for interactions in the simulation.
            delivery_history (dict): Dictionary storing the delivery history.
            action_map (dict): Mapping for actions in the simulation from discrete to multidiscrete.
    
        Methods:
            __init__(...): Initializes the JSSP simulator with optional parameters.
            petri_reset(): Resets the internal state of the Petri net, including places and tokens.
            action_mapping(): Maps multidiscrete actions to a dictionary for use with reinforcement learning.
            is_terminal(): Checks if the simulation has reached a terminal state.
            sort_tokens(): Processes tokens in sorting places based on their roles.
            refresh_state(): Updates the state of the Petri net after sorting tokens and checking transitions.
            fire_timed(): Advances simulation time and fires timed transitions based on elapsed times.
            action_masks(): Checks which transitions are enabled for action selection.
            fire_controlled(action): Fires a controlled transition based on the provided action.
            time_tick(): Increments the internal simulation clock and updates token logging.
            interact(action, screenshot=False): Performs Petri net interactions based on the action and updates internal state.
    """

    def __init__(self, 
                 label="main",
                 benchmark='Raj',
                 instance_id="ra01", 
                 layout=1,
                 n_agv=0,
                 n_tt=0,
                 
                 dynamic=False,
                 size=(None,None,None,None),
                 
                 observation_depth=1,
                 
                 lookup=False,
                 random_arrival= False,
                 machine_down=False,
                 commitment_length=1

                  ):
        """
    Initializes the JSSP simulator with the given parameters.

    Parameters:
        instance_id (str): Identifier for the JSSP instance.
        dynamic (bool): If True, allows appending new operations; termination condition is all queues empty.
        size (tuple): Size parameters for simulation, only if dynamic  (default: (None, None)).
        n_agv (int): Number of AGVs (default: 2).
        n_tt (int): Number of tool transports (default: 1).
    """
    
        super().__init__(instance_id, 
                         layout= layout,
                         benchmark=benchmark,
                         n_agv=n_agv,
                         n_tt=n_tt,
                         dynamic=dynamic,
                         size=size,
           

                         )
        
        self.label=label
        self.create_petri(show_flags=True,show_develop=False) 
        self.cache ={}
        self.cache_nodes()  

        
        
        self.clock = 0
        self.interaction_counter = 0
        self.observation_depth=observation_depth
        
        self.episode_nval=0
        self.nval_evolution=[]
        
        
        self.delivery_history = {}
        self.action_map = self.action_mapping()
        self.graph=Graph(self)
        

        self. lookup = lookup
        if self.lookup :
            self.twin=create_twin(self)
        

        self.heuristics_algos=init_heuristics()
        self.commitment_length = commitment_length
        self.commitment_counter = 0
        self.current_heuristic = None
        
        self.petri_reset()
        self.print_instance_info()

        
    


    def cache_nodes(self):
        " Cache places and transitions in the simulation."""
        
        places = list(self.places.values())
        transitions = list(self.transitions.values())
    
        self.cache = {
            "places": places,
            "transitions": transitions,
            "machine_processing": [p for p in places if p.role == "machine_processing"],
            "job_idle": [p for p in places if p.role == "job_idle"],
            "process_places": [p for p in places if p.type == "p"],
            "buffer_places": [p for p in places if p.type == "b"],
            "sorting_places": [p for p in places if p.type == "s"],
            "auto_transitions": [t for t in transitions if t.type == "a"],
            "machine_start": [t for t in transitions if t. uid in self.filter_nodes("machine_start", "t")],
            "job_feed": [t for t in transitions if t. uid in self.filter_nodes("job_feed", "t")]
        }


    def set_test_mode(self,model):  
        " Sets the lookup test mode for the simulator."""
        if self. lookup:  
            self.twin.policy=model.policy
    
        
    def print_instance_info (self): 
        if self.label=="main":
            print(f"{self.benchmark} Instance '{self.instance_id}' ,Layout: '{self.layout}' is loaded.")
            print(f"JSSP {self.instance_id}: {self.n_jobs} jobs X {self.n_machines} machines X  {self.n_tools} Tools, AGVs: {self.n_agv}, TT: {self.n_tt}, Dynamic Mode: {self.dynamic} , Lookup: {self.lookup}")
            print(f"Commitement steps pro heuristic: {self.commitment_length}")
            
    def get_state(self):
          """ Returns the current state of the simulation."""
          return get_obs_basic(self.cache ["places"],self.observation_depth)
     

    def  error_check(self): 
        """ Checks for any errors in the simulation."""
        ...

    def petri_reset(self):
        " Resets the internal state of the Petri net."""
        
        self.clock = 0
        for place in self. places.values():
            place.token_container = []
        self.add_tokens()
        
        
        self.episode_nval=0
        self.nval_evolution.append(self.episode_nval)
        
        
        
    def action_mapping(self):
         " Maps multidiscrete actions to a more versatile Discrete format for reinforcement learning."""
         return dict(enumerate([t for t in self.transitions.values() if t.type == "c"]))


    def is_terminal(self):
        """ Checks if the simulation has reached a terminal state."""


        return   np.all([len(p.token_container) == 0 
                         for p in self.cache["process_places"]+ self.cache["buffer_places"]])

    
    
    def job_arrival(self):
        """ job arrivals using a Poisson distribution."""

        arrival_lambda=0.05     # Exponential(λ) distribution, five high priority , two low priority, 0.5 rare       
        job_feed_transitions=self.cache["job_feed"]
        num_arrivals_this_step= [np.random.poisson(arrival_lambda) for transition in job_feed_transitions]
        
        for idx, transition in enumerate(job_feed_transitions):
            for token in range(num_arrivals_this_step[idx]):
                transition.fire()
                

    def machines_down(self):
        """Simulates machines going down based on failure times and repair durations."""

        machine_starts = self.cache["machine_start"]
        failure_times = np.array(self.t_lookup["failure_times"])
        repair_durations = np.array(self.t_lookup["repair_durations"])
    
        conditions = (self.clock >= failure_times) & (self.clock < repair_durations)
        forced_values = np.where(conditions, False, None)
    
        for machine, value in zip(machine_starts, forced_values):
            machine.forced = value
        

        
    def get_deadheading(self,place,role_dict):
        " Handles deadheading for certain places (e.g., transport)."

        pass
    

    def time_tick(self):
        " Advances the internal clock and updates token logging."""
        
        self.clock += 1
        process_places = self.cache["process_places"]

        
        for p in process_places:
            transition = next((parent for parent in p.parents if parent.type != "f"), None)
            if transition and transition.forced != False: 
                p.tick()
            
        #self.error_check()  #  useful in safe mode mode 
    
    
    def fire_auto(self):
        " Fires automatic transitions."""
        
        for transition in self.cache["auto_transitions"]: 
            if transition.check_state():
                transition.fire(self.clock)
            
            
    def sort_tokens(self):
        " Sorts tokens in sorting places based on their roles."""
        
        
        def process_tokens(place, color_criterion_index):
            tokens = place.token_container
            if not tokens:
                return
            
            for token in tokens.copy():
                for transition in place.children:
                    if token.color[color_criterion_index] == transition.color:
                        transition.fire(self.clock)
                        break
                else:
                    tokens.remove(token)
                    print(f"Token color: {token.color} destroyed in {place.role} - No compatible destination found!")
    
        role_to_index = {
            "job_sorting": 0,
            "machine_sorting": 1,
            "machine_sorting_T": 1,
            "request_sorting": 2,
            "tools_sorting": 2,
        }
    
        for place in self.cache.get("sorting_places", []):
                process_tokens(place, role_to_index[place.role])
                
           
      
    def refresh_state(self):
        " Refreshes the state of the Petri net after sorting tokens and checking enabled transitions."""


        if self.random_arrival:
            self.job_arrival()
            
        if self.machine_down:
            self.machines_down()
        
        self.sort_tokens()
        self.fire_auto()
        

    def guard_function(self):

        " Refreshes the state of the Petri net after sorting tokens and checking enabled transitions."""

        self.refresh_state()
        mask =[t. check_state ()  for t in self. transitions.values() if t.type == "c"]
        return mask  
     

    def fire_timed(self):
        " Advances the simulation time, fires timed transitions, and updates the state of the Petri net."""
       
        
        role_dict={"machine_processing":0,
                   "agv_transporting":1,
                   "agv_relocating":2,
                   "tt_transporting":3,
                   "tt_relocating":4,
                   }
       
        
        fired_transitions = []
        
        for place in self.cache["process_places"]: 
            if  place.token_container:
                transition = place.children[0]
                token = place.token_container[0]   
                
                elapsed_time = token.logging[place.uid][2]
                reference_time = token.time_features[role_dict[place.role]]

    
                if elapsed_time >= reference_time :
                    
                    if place. role in ["agv_transporting", "tt_transporting"]:
                        self.get_deadheading(place,role_dict)
                        
                    transition.fire(self.clock)
                    fired_transitions.append(transition.uid)
                

        self.refresh_state()
        self.delivery_history[self.clock] = [ token for place in self.places.values() if place.type == "d" for token in place.token_container]
           
        return fired_transitions

 

    def fire_controlled(self, action , screenshot=False):
        
        " Fires a controlled transition based on the action."""
        fired_transitions=[]  
        transition = self.action_map[int(action)] 
        
        if all(parent.token_container for parent in transition.parents):
            transition.fire(self.clock)
            fired_transitions.append(transition.uid)

        
        self.interaction_counter += 1 
        self.graph.plot_net(fired_transitions) if screenshot else None
        

    
    def get_utilization(self):
         
         utilization = 0
         busy_machines= np.array( [bool(machine.token_container) for machine in self.cache["machine_processing"]])
         utilization =  sum(busy_machines)/self.n_machines
         
         return utilization   
     
        
    def get_consumption(self):
        
        consumption = 0
        busy_machines= np.array( [bool(machine.token_container) for machine in self.cache["machine_processing"]])
        consumption =  np.dot(busy_machines , self.machines_powers)
        return consumption
    


    def interact(self, action, screenshot):
        """
        Executes a committed sequence of steps using the same heuristic (macro-step).
        Only returns once commitment is finished or the simulation terminates.
        """
        
  
        
        total_util= 0
        self.episode_nval=0
        
        feedbacks = {
            'valid_move': True,
            'machine_utilisation': 0.0,
        }

        self.current_heuristic = action
        heuristic_rule= self.heuristics_algos[action]
        #print(heuristic_rule)
        
        for _ in range(self.commitment_length):
            
            if self.is_terminal():
                break

            # --- Apply controlled transition (heuristic) ---
            move= heuristic_rule.decide(self)
            if move is not None:
                fired_controlled = self.fire_controlled( move)
                if screenshot:
                 self.graph.plot_net(fired_controlled)
                 
            else :
                feedbacks = {'valid_move': False}
                self.episode_nval+=1
               


            # --- Let automatic transitions fire -------------
            while sum(self.guard_function()) == 0:
                
                self.time_tick()
                fired_timed = self.fire_timed()
                if screenshot:
                    self.graph.plot_net(fired_timed)
                if self.is_terminal():
                    break
    
    
            total_util += self.get_utilization()
            self.nval_evolution.append(self.episode_nval)

        feedbacks['machine_utilisation'] = total_util /self.commitment_length
        return feedbacks
    
                   
               


if __name__ == "__main__":
    
    
    benchmark='Raj'
    instance = "ra01"
    layout =1
    n_agv=2
    n_tt=0
    
    dynamic=False
    # Job,machines,n_agvs,n_tools,ntt
    size=(100,20,10,0,0)
    
    petri = Simulator(benchmark=benchmark,
                      instance_id= instance,
                      layout=layout,
                      n_agv=n_agv,
                      n_tt=n_tt,
                      dynamic=dynamic , 
                      size= size)
    

    petri. graph.plot_net()

    
  

    

    

    
    
 
    
  
    
    

  
    
    
 
    
  
    
    

  
    
    
    

    
   
    
    
 

    
    
    
    
    
    
    
    
    
   
    
    

    
    

    
    
    

        


    