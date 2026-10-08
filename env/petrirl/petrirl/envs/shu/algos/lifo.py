class Lifo():  
    "Remark : for a static jssp it empty the queue in decending order one by one.In Dynamic JSSP Last in first out "

    def __init__(self):
        self.type_="static"
        self.cat = "job"
        
    def __str__(self):
       return  "Lifo: Last in first out , always return the enabled job with the higest index."
   
    def decide(self, sim, scope="job_select"):
        
        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) 
                               if value and sim.action_map[idx].role == scope]  
        
 
        actions_results = {action: i for i, action in enumerate(enabled_actions_idx)}
    
        if actions_results:
            index, value = min(actions_results.items(), key=lambda item: item[1])
            return index
        else:
            return None
            
        
        
    
    
    
    