
class Nll():
    def __init__(self):
        self.label = "NLL"
        self.type_ = "Dynamic"
        self.cat="agv"
        
    def __str__(self):
        return "Next Least loaded (NLL): Prioritize resource with the least operations remaining in  queue."
   
    def decide(self, sim ,scope="agv_select"):
        
        
        def get_results ( enabled_agvs_idx):
            
            results={}
            for action in  enabled_agvs_idx:    
                resources= [p for p in sim.action_map[action].children if  p.type!="f"]
                
                for resource in resources:
                    results[action] =  len(resource.token_container) 
                    
                    
            #print(results)        
            return results
        

        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = min(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None
