class Nlwr():
    def __init__(self):
        self.label = "NLWR"
        self.type_ = "Dynamic"
        self.cat="agv"
        
    def __str__(self):
        return "Next Least Work remaining (NLWR): Prioritize resource with the least  work remaining (sequence * transport times) in agv  queue."
    
    def decide(self, sim ,scope="agv_select"):
        
        
        def get_results ( enabled_agvs_idx):
            
            results={}
            for action in  enabled_agvs_idx:    
                resources= [p for p in sim.action_map[action].children if  p.type!="f"]
                
                for resource in resources:
                    work_remaining=0
                    if resource.token_container:
                        for token in  resource.token_container:
                            work_remaining+= token.time_features[0]

                        results[action] =  work_remaining
   
            #print(results)        
            return results
        

        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = min(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None
        
                    
