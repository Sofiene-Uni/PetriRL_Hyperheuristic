class Lptn():
    def __init__(self):
        self.type_="dynamic"
        self.cat = "job"
        
    def __str__(self):
       return  "Longest Processing Time next (LPTX): Select  the job with operation that is ready  to be processed next and  have the Longest processing time."
   
    def decide(self, sim ,scope="job_select"):
        
        def get_results(enabled_actions_idx):
            
            results={}   
            for action in enabled_actions_idx: 
                parent_job= [p for p in sim.action_map[action].parents if  p.type!="f"][0]
                
                if parent_job.token_container:
                    results[action]=parent_job.token_container[0].time_features[0]

           # print(results)
            return results
                    
        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = max(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None
        
        
        