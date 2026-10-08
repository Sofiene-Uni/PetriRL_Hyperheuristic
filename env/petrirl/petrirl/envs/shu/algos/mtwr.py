class Mtwr():

    def __init__(self):
        self.type_="dynamic" 
        self.cat = "job"
        
    def __str__(self):
       return  "Most Total Work remaining (MTWR): Prioritize jobs with the Most total work remaining (sequence * processing times) in the job queue."
    

    def decide(self, sim ,scope="job_select"):
        
        def get_results(enabled_actions_idx):
            
            results={}   
            
            for action in enabled_actions_idx:
                parent_job= [p for p in sim.action_map[action].parents if  p.type!="f"][0]
                
                total_work_remaining=0

                if parent_job.token_container:
                    for token in  parent_job.token_container:
                        total_work_remaining+=token.time_features[0]


                    results[action]=total_work_remaining
                
            #print(results)        
            return results
                    
        enabled_actions_idx = [idx for idx, value in enumerate(sim.guard_function()) if value and sim.action_map[idx].role == scope]  
        actions_reults= get_results(enabled_actions_idx)

   
        if actions_reults:
            index, value = max(actions_reults.items(), key=lambda item: item[1])
            return index
        else:
            return None
        