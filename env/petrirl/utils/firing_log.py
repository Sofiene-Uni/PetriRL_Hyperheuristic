import pickle


NEG_INF = -1

class FiringLogger:
    def __init__(self, sim):
        self.sim = sim
        self.n_jobs = sim.n_jobs
        self.observed_roles = ["job_select", "agv_finish", "machine_finish"]
        self.observed_transitions = [
            transition for transition in self.sim.transitions.values()
            if transition.role in self.observed_roles
        ]
        self.logs = {}
        self.dater=None
        self.sim.episodes = getattr(self.sim, "episodes", 0)

    def collect_logs(self):
        episode = self.sim.episodes

        # Initialize log containers per job per episode
        for job_id in range(1, self.n_jobs + 1):
            job_key = f"job{job_id}"
            if job_key not in self.logs:
                self.logs[job_key] = {}
            if episode not in self.logs[job_key]:
                self.logs[job_key][episode] = {role: [] for role in self.observed_roles}

        # Collect logs from transitions
        for transition in self.observed_transitions:
            role = transition.role
            for job_id, job_log in transition.local_logs.items():
                if job_id in self.logs:
                    if episode not in self.logs[job_id]:
                        self.logs[job_id][episode] = {role: [] for role in self.observed_roles}
                    self.logs[job_id][episode][role].extend(job_log)
                    self.logs[job_id][episode][role].sort()

        # Clear logs for next episode
        for transition in self.sim.transitions.values():
            transition.local_logs = {}

        self.sim.episodes += 1




    def convert_to_dater(self):
        result = {}
        for job_id, episodes in self.logs.items():
            job_result = {}
            for episode_id, transitions in episodes.items():
                js = transitions.get('job_select', [])
                af = transitions.get('agv_finish', [])
                mf = transitions.get('machine_finish', [])
                # Align by index
                zipped = list(zip(js, af, mf))
                # Prepend the initial state
                sequence = [[0, 0, 0]] + [list(step) for step in zipped]
                job_result[episode_id] = sequence
            result[job_id] = job_result
            
        self.dater=result
            
        return result



    # Save dataset to pickle file
    def save_dataset(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.dater, f)
        print(f"Dataset saved to {filename}")

  