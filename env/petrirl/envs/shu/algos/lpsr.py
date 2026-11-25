class Lpsr():
    def __init__(self):
        self.type_="Dynamic"
        self.cat = "job"
        
    def __str__(self):
       return  "Longest Process Sequence Remaining (LPSR): Prioritize jobs with the most operations remaining in the job queue."
   
    def decide(self, sim ,scope="job_select"):
        
        def get_results(enabled_actions_idx):   
            results={}   
            
            for action in enabled_actions_idx:    
                parent_job= [p for p in sim.action_map[action].parents if  p.type!="f"][0]   
                if parent_job.token_container:
                    results[action]=len(parent_job.token_container)
                
            #print(results)
                
                
            return results
                    
        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = max(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None