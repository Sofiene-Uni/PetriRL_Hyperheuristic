import numpy as np
from gymnasium import Env
from gymnasium import spaces

from petrirl.envs.shu.simulator import Simulator
from petrirl.render.plot_shu import JSSPPlotter
from petrirl.utils.reward   import RewardCalculator
from typing import Optional
from gymnasium.utils import seeding


class ShuEnv(Env):
    
    """
    Custom Gym environment for Job Shop Scheduling using a Petri net simulator.
    """
    metadata = {"render_modes": ["solution" , "human"]}

    def __init__(self, 
                 
                 benchmark :str="Solax",
                 instance_id :str="sl00" ,
                 layout:int =1,
                 n_agv:int =0,
                 n_tt:int =0, 
                 
                 dynamic: bool=False,
                 size=(None,None,None,None),
                 
                 observation_depth:int = 1 , 
                 reward_f:str="G",
                 render_mode: str ="solution",
                 lookup: bool= False,
                 
                 random_arrival=False,
                 machine_down=False,
                 
                 commitment_length=5,
                 
                 
                 grid=False,
                 rank= False,
                 
                 
                 ):
        """
        Initializes the JsspetriEnv.
        if the JSSP is flexible a maximum number of machines and jobs if predefined regardless le instance size 

        Parameters:
            render_mode (str): Rendering mode ("human" or "solution").
            instance_id (str): Identifier for the JSSP instance.
            observation_depth (int): Depth of observations in future.
        """
        
        self.dynamic=dynamic
        self.instance_id=instance_id
        
        self.sim = Simulator(
                             benchmark=benchmark,
                             instance_id=self.instance_id,
                             layout=layout,
                             n_agv=n_agv,
                             n_tt=n_tt,
                             
                             dynamic=self.dynamic,
                             size=size,

                             observation_depth=observation_depth,
                             lookup=lookup,
                             
                             random_arrival=random_arrival,
                             machine_down=machine_down,
                             
                             commitment_length=commitment_length
                             )


        observation_size = 15 *len(self.sim.places.values()) 
      
        

        self.observation_space= spaces.Box(low=-1, high=self.sim.max_bound,shape=(observation_size,),dtype=np.int64)
        self.action_space = spaces.Discrete(len(self.sim.heuristics_algos))  
      
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.reward_f=reward_f
        
        self.plotter=JSSPPlotter(grid=grid, rank=rank, title_font_size=24, font_size=20,  format="pdf", dpi=300)
        self.reward = RewardCalculator (self)
        
        self.min_makespan=np.inf
        self.np_random = None
        
        


    def seed (self, seed: Optional[int] = None):
        """
        Sets the seed for the environment and its components.
        """
        self.np_random, seed = seeding.np_random(seed)
    
        # Optional: Sync NumPy for reproducibility if used directly
        np.random.seed(seed)
    
        # Optional: seed the simulator
        if hasattr(self.sim, "seed"):
            self.sim.seed(seed)
    
        # Optional: seed the reward calculator
        if hasattr(self.reward, "seed"):
            self.reward.seed(seed)
    
        return [seed]
        



 

    def reset(self, seed=None, options=None):
        """
        Reset the environment.
        Returns:
            tuple: Initial observation and info.
        """
        self.sim.petri_reset()
        observation=self.sim.get_state()
        info = self._get_info(0,False,False)
        return observation, info
    
    
    def reward(self,feed_back=None,terminal=False):
       """
       Calculate the reward.
       Parameters:
           terminal: if the episode reached termination.
       Returns:
           Any: Calculated reward .
       """ 
       return self.reward.calculate(self,feed_back,terminal)


    def action_masks(self):
        """
        Get the action masks.
        Returns:
            list: List of enabled actions.
        """ 
        return self.sim.guard_function()
    
    def step(self, action):
        """
        Take a step in the environment.
        Parameters:
            action: Action to be performed.
        Returns:
            tuple: New observation, reward, termination status, info.
            
        """

        screenshot= True if self.render_mode == "human" else False
        feedback = self.sim.interact(action,screenshot=screenshot)  
        observation = self.sim.get_state()
        terminated= self.sim.is_terminal()
        reward = self.reward.calculate(feedback,terminated)

        info = self._get_info()
        return observation, reward, terminated, False, info
        
        
    

    def render(self):
        """
        Render the environment.
        """
        if self.render_mode ==  "solution":
            self.plotter.plot_solution(self.sim)

        if self.render_mode == "human":
            self.plotter.plot_solution(self.sim)
            # lunch GUI to display imag sequence , TO DO 
 

    def close(self):
        """
        Close the environment.
        """

    def _get_info(self, reward=0,fired=False, terminated=False):
        """
        Get information dictionary.
        """
        return {"Reward": reward,"Fired":fired ,"Terminated": terminated ,"mask":self.sim.guard_function()}

if __name__ == "__main__":
    
    benchmark = "Raj"
    instance="ra03"
    
    n_agv =2 
    env=ShuEnv(benchmark = benchmark ,
               instance_id=instance,
               n_agv=n_agv,
               )
    
    
    #env.sim.graph.plot_net()
    
    env.seed(42)
    

    

    
    


    


    
