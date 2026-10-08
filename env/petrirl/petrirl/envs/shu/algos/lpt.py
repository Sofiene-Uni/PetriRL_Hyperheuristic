class Lpt():
    def __init__(self):
        self.type_="static"
        self.cat = "job"
        
    def __str__(self):
       return  "Longest processing time (LPT): Prioritize jobs with the initial Longest processing time."
   
    def decide(self, sim ,scope="job_select"):


        def get_results(enabled_actions_idx):
            
            results={}
            
            for action in enabled_actions_idx:
                parent_job= [p for p in sim.action_map[action].parents if  p.type!="f"][0]   
            
                total_process_time=0
                job_sequence = sim.instance.job_sequences[parent_job.color-1]   # correct for list indx start from 0 unlike job colors
                
                for op in job_sequence :
                    _,_,time=op
                    total_process_time+=time
                results[action]=total_process_time
                
                
            #print(results)    
            return results
                    
        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = max(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None
        


        