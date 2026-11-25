from petrirl.envs.fms.petri_build import Petri_build
from petrirl.render.graph import  Graph
from petrirl.utils.obs import get_obs_basic
from petrirl.utils.twin import create_twin
from petrirl.utils.feedbacks import get_consumption,get_utilization,get_buffer
import copy


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
                 standby=False

                  ):
        """
    Initializes the JSSP simulator with the given parameters.

    Parameters:
        instance_id (str): Identifier for the JSSP instance.
        dynamic (bool): If True, allows appending new operations; termination condition is all queues empty.
        size (tuple): Size parameters for simulation only if dynamic  (default: (None, None)).
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
                         stand_by= standby
                         )
        
        self.label=label
        self.create_petri(show_flags=True,show_develop=False) 
        self.cache =self.cache_nodes()

        self.clock = 0
        self.episodes=0
        self.interaction_counter = 0
        self.observation_depth=observation_depth
        
        self.action_map = self.action_mapping()
        self.graph=Graph(self)
        
        self.lookup=lookup
        if self.lookup :
            self.twin=create_twin(self)
            
        self.delivery_history = {}
        self.print_instance_info()
        self.petri_reset()
        
        self.graph.plot_net()
        
        self.buffer_time=0
        

    def set_seeds(self,seeds=None):  
        self.seeds= seeds
        if seeds :
           print(f"seeds loaded numbre of samples seeds :{len (self.seeds)}")
        else :
            print ("No seeds provided  , a random seed will be utilized !")
        

    def print_instance_info (self):  
        if self.label=="main":
            print(f"{self.benchmark} Instance '{self.instance_id}' ,Layout: '{self.layout}' is loaded.")
            print(f"Random Job Arrival : {self.random_arrival} ,  Random Machines Down : {self.machine_down} ")
            print(f"JSSP {self.instance_id}: {self.n_jobs} jobs X {self.n_machines} machines X  {self.n_tools} Tools, AGVs: {self.n_agv}, TT: {self.n_tt}, Dynamic Mode: {self.dynamic} , Lookup: {self.lookup}")
            
    def get_state(self):
         """Returns the current state of the simulation."""
         return get_obs_basic(self.cache ["places"],self.observation_depth)
     

    def  error_check(self): 
        """Checks for any errors in the simulation."""
        ...

    def petri_reset(self):
        """Resets the internal state of the Petri net."""

        self.clock = 0
        self.clear_petri()    
        self.add_tokens()

        
    def save_state(self):
        """Save the full Petri net state."""
        return {
            "tokens": self.save_token_state(),
            "clock": copy.deepcopy(self.clock)
        }

    def load_state(self, saved_state):
        """Restore the full Petri net state."""
        self.load_token_state(saved_state["tokens"])
        self.clock = saved_state["clock"]
        
        

    def action_mapping(self):
         """Maps multidiscrete actions to a more versatile Discrete format for reinforcement learning."""
         return dict(enumerate([t for t in self.transitions.values() if t.type == "c"]))


    def is_terminal(self):
        """Checks if the simulation has reached a terminal state."""
        done = sum(len(p.token_container) for p in self.cache["delivery_places"]) >= self.number_of_ops
        #done = np.all([len(p.token_container) == 0 for p in self.cache["flow_places"]])
        return  done 

         
    def get_deadheadings(self,place,role_dict):
         
        queue = [p for p in self.cache["op_queue"] if p.token_container]
        if not queue :
            return

        time_criterion=role_dict[place.role]
        buffer = place.parents[0].parents[0]
        token = place.token_container[0]

        previous_location = place.history[-1]
        next_location=None

        if buffer.token_container:
            next_location = buffer.token_container[0].machine_sequence[0]
  
        else:
            pass 
            if self.lookup:
                self.twin.sync_state(self)
                next_location = self.twin.run_lookahead(buffer)

        dead_heading = self.instance.get_time(previous_location, next_location, time_type=time_criterion)
        
        if dead_heading > 0 :
            place.history[-1] = next_location
            token.time_features[time_criterion+1] = dead_heading
            
            token.deadheadings[place.role].append((place.color, previous_location, next_location, self.clock, dead_heading))
            
            
    
    def time_tick(self):
        """Advances the internal clock and updates token logging."""
    
        self.clock += 1
        process_places = self.cache["process_places"]
        for p in process_places:
            
            transition = next((parent for parent in p.parents if parent.type != "f"), None)
            if transition is None:
                continue
        
            if transition.forced is False:
                p.tick(faulty=True)
            else:
                p.tick()
                
        self.buffer_time+= get_buffer(self)
                
        #self.error_check()  #  useful in safe mode mode 
        
    def fire_auto(self):
        """Fires automatic transitions."""
        
        for transition in self.cache["auto_transitions"]: 
            if transition.check_state():
                transition.fire(self.clock)
            
            
    def sort_tokens(self):
        """Sorts tokens in sorting places based on their roles."""
        
        
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
        """Refreshes the state of the Petri net after sorting tokens and checking enabled transitions."""
        if self.random_arrival:
            self.job_arrival()
            
        if self.machine_down:
            self.machines_down()
        
        self.sort_tokens()
        self.fire_auto()
        
        
    def is_valid(self,action):
        """
        checks if an action is valid to fire 
        """
        transition = self.action_map[int(action)] 
        return  transition.check_state()
        
        
    def guard_function(self):
        """Refreshes the state of the Petri net after sorting tokens and checking enabled transitions."""

        self.refresh_state()
        mask =[t.check_state()  for t in self.transitions.values() if t.type == "c"]
        return mask  
     

    def fire_timed(self):
        """Advances the simulation time, fires timed transitions, and updates the state of the Petri net."""
        
        completed_ops=0
        role_dict={"machine_processing":0,
                   "agv_transporting":1,
                   "agv_relocating":2,
                   "tt_transporting":3,
                   "tt_relocating":4,
                   }
       
        fired_transitions = []
        for place in  self.cache["process_places"]: 
            if place.token_container:
                transition = place.children[0]
                token = place.token_container[0]   
                
                elapsed_time = token.logging[place.uid][2]
                reference_time = token.time_features[role_dict[place.role]]

                if elapsed_time >= reference_time :
                    
                    if place.role in ["agv_transporting", "tt_transporting"]:
                        self.get_deadheadings(place,role_dict)
                        
                    transition.fire(self.clock)
                    fired_transitions.append(transition.uid)
           
                    if transition.role=="machine_finish":
                        completed_ops+=1
            
        self.refresh_state()
        self.delivery_history[self.clock] = [ token for place in self.places.values() if place.type == "d" for token in place.token_container]
           
        return fired_transitions,completed_ops


    def fire_controlled(self, action):
        
        """Fires a controlled transition based on the action."""
        fired_transitions=[]  
        transition = self.action_map[int(action)] 
        
        if transition.role=="standby":
            self.time_tick()
        
        if all(parent.token_container for parent in transition.parents):
            transition.fire(self.clock)
            fired_transitions.append(transition.uid)

        
        self.interaction_counter += 1 
        return fired_transitions
    

    def interact(self, action ,screenshot):
        """Handles the interaction logic for each step in the simulation."""
        
        feedbacks={}

        fired_controlled = self.fire_controlled(action)  
        self.graph.plot_net(fired_controlled) if screenshot else None


        while sum(self.guard_function()) == self.standby: 
            fired_time,completed_ops_1 = self.fire_timed()
            fired_timed,completed_ops_2 = self.fire_timed()
            self.time_tick()
            
            self.graph.plot_net(fired_timed) if screenshot else None
            if self.is_terminal():
               break
        
        # feedbacks['energy_consumption']=get_consumption(self)
        # feedbacks['machine_utilisation']=get_utilization(self)

        feedbacks['buffer_time']=self.buffer_time
        
        return feedbacks
           

if __name__ == "__main__":
    
    benchmark='Solax'
    instance = "sl00"
    layout =1
    n_agv=2
    n_tt=0
    
    dynamic=False
    # Job,machines,n_agvs,n_tools,ntt
    size=(100,20,10,0,0)
    
    petri = Simulator(benchmark=benchmark,
                      instance_id= instance ,
                      layout=layout,
                      n_agv=n_agv,
                      n_tt=n_tt,
                      dynamic=dynamic , 
                      size= size,
                      ) 
                
    petri.graph.plot_net()
    petri.print_instance_info()
  



    
    
 
    
  
    
    

  
    
    
 
    
  
    
    

  
    
    
    

    
   
    
    
 

    
    
    
    
    
    
    
    
    
   
    
    

    
    

    
    
    

        


    