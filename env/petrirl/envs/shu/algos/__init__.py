
from .fifo import Fifo
from .lifo import Lifo

from .spt import Spt
from .lpt import Lpt

from .lptn import Lptn
from .sptn import Sptn

from .mtwr import Mtwr
from .ltwr import Ltwr 

from .sps import Sps
from .lps import Lps


from .spsr import Spsr
from .lpsr import Lpsr

from .swt import Swt
from .lwt import Lwt

from .nll import Nll
from .spsd import Spsd
from .nlwr import Nlwr


def info(acronym):
    explanations = {
        "FIFO": "(First in first out)-Static: always returns the enabled job with the lowest index.",
        "LIFO": "(Last in first out)-Static: always returns the enabled job with the highest index.",
        
        "SPT": "(Shortest processing time)-Static: Prioritizes jobs with the initial shortest processing time.",
        "LPT": "(Longest processing time)-Static: Prioritizes jobs with the initial Longest processing time.",
        
        "SPS": "(Shortest Process Sequence)-Static: Prioritizes jobs with the least initial operations in the job queue.",
        "LPS": "(Longest Process Sequence)-Static: Prioritizes jobs with the most initial operations in the job queue.",
        
        "LTWR": "(Least Total Work remaining)-Dynamic: Prioritizes jobs with the least total work remaining (sequence * processing times) in the job queue.",
        "MTWR": "(Most Total Work remaining)-Dynamic: Prioritizes jobs with the most work remaining (sequence * processing_time) in the job queue.",
        
        "SPSR": "(Shortest Process Sequence remaining)-Dynamic: Prioritizes jobs with the least operations remaining in the job queue.",
        "LPSR": "(Longest Process Sequence Remaining)-Dynamic: Prioritizes jobs with the most operations remaining in the job queue.",
       
        "SPTN": "(Shortest Processing Time Next OP)-Dynamic: Selects the job with operation that is ready to be processed next and has the Shortest processing time.",
        "LPTN": "(Longest Processing Time Next OP)-Dynamic: Selects the job with operation that is ready to be processed next and has the Longest processing time.",
       
        "SWT" : "(Shortest Waiting Time)-Dynamic: Prioritize jobs with the lowest waiting time since last allocation",
        "LWT" : "(Longest Waiting Time)-Dynamic: Prioritize jobs with the higest waiting time since last allocation",
        
        #---------- AGvs heuristics  -------------------------------------------------------------
        
        "NLL" : "(Next Least loaded)-Dynamic: Prioritize resource with the least number of operations remaining in  queue.",
        "SPSD" : "(Shortest Process Sequence Done)-Dynamic: Prioritize resource with the least operations Done to equibrate the load.",
        "NLWR" : "(Next Least Work remaining)-Dynamic: Prioritize resource with the least  work remaining (sequence * transport times) in agv  queue.",
  
    }
    return explanations.get(acronym, "Explanation not available for the provided acronym.")
    
def init_heuristics():
    job_algos = {
        0: Fifo,
        1: Lifo,
        2: Spt,
        3: Lpt,
        4: Sps,
        5: Lps,
        6: Spsr,
        7: Lpsr,
        8: Sptn,
        9: Lptn,
        10: Ltwr,
        11: Mtwr,  
        12: Lwt,
        13: Swt, 
    }
    
    agv_algos = {
        14: Nll,
        15: Spsd,
        16: Nlwr,       
    }
    
    # Combine both dictionaries
    all_algos = {**job_algos, **agv_algos}
    
    # Instantiate each algorithm
    #heuristic_obj = [algo_class() for algo_class in all_algos.values()]
    heuristic_obj=[job_algos[idx]() for idx in job_algos ]
    
    return heuristic_obj

