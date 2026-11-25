# PetriRL Hyper-Heuristic

A policy-based deep reinforcement learning hyper-heuristic for the **Job Shop Scheduling Problem (JSSP)**, built on a
colored timed Petri net. Instead of choosing job-machine assignments directly, the agent learns which dispatching rule
to apply in the current state of the shop floor. Part of the [PetriRL framework](https://github.com/Sofiene-Uni/PetriRL-Framework).

![PetriRL hyper-heuristic framework](assets/framework.png)

The policy network (left) observes the state of the Petri net and selects a low-level heuristic. The heuristic picks
the next operation to dispatch among the actions enabled by the net (right), and stays in charge for the next k
decisions before the agent chooses again.

## Key Ideas

- **Action prefiltering**: the guard functions of the Petri net remove infeasible actions before the heuristics see
  them, so every heuristic is evaluated only on valid decisions.
- **Commitment**: a selected heuristic is applied for k consecutive decisions (temporal abstraction, as in options).
  This shortens the decision horizon, improves credit assignment and stabilizes training; k = 5 is the default.
- **Convergence**: with deterministic Petri net dynamics and a fixed commitment length, the resulting semi-Markov
  decision process reduces to a finite MDP, which allows a convergence argument through Mirror Learning.
- **Explainability**: every decision is made by a readable rule (for example, MTWR: the job with the most work
  remaining) and can be followed as token flow in the net.

## Low-Level Heuristics

| Rule | Selects the job with | Rule | Selects the job with |
|---|---|---|---|
| FIFO | lowest job index | LIFO | highest job index |
| SPT | shortest total processing time | LPT | longest total processing time |
| SPS | fewest operations | LPS | most operations |
| LTWR | least total work remaining | MTWR | most total work remaining |
| SPSR | fewest operations remaining | LPSR | most operations remaining |
| SPTN | shortest next operation | LPTN | longest next operation |
| SWT | shortest waiting time since its last operation | LWT | longest waiting time since its last operation |

## Results

Makespan on the first instance of each Taillard size group (from the paper; DGERD, GIN and GAM are learning-based
methods from the literature, MPPO is the masked-PPO PetriRL agent acting on primitive actions):

| Instance | Size | DGERD | GIN | GAM | MPPO | Best heuristic | **Ours** |
|---|---|---|---|---|---|---|---|
| ta01 | 15×15 | 1711 | 1547 | 1530 | **1436** | 1454 | 1454 |
| ta11 | 20×15 | 1833 | 1775 | 1798 | **1568** | 1671 | 1648 |
| ta21 | 20×20 | 2146 | 2128 | 2086 | 2064 | 2016 | **1977** |
| ta31 | 30×15 | 2383 | 2379 | 2342 | **2166** | 2260 | 2219 |
| ta41 | 30×20 | **2541** | 2604 | 2604 | 2576 | 2543 | 2543 |
| ta51 | 50×15 | 3763 | 3394 | 3344 | **3272** | 3561 | 3433 |
| ta61 | 50×20 | 3633 | 3594 | 3534 | 3505 | 3572 | **3427** |
| ta71 | 100×20 | 6321 | 6098 | **6027** | 6366 | 6270 | 6150 |
| **Average** | | 3041 | 2940 | 2908 | 2869 | 2918 | **2856** |

The hyper-heuristic matches or improves the best single rule on every instance (2.1% lower average makespan) and has
the lowest average makespan of all compared methods. Commitment length matters: the average makespan is 2915 with
1-step switching, **2856 with 5 steps**, and 2901, 2886 and 2918 with 50, 100 and 1000 steps.

## Repository Structure

```
env/petrirl/      PetriRL package; the hyper-heuristic environment is envs/shu (gym id "petrirl-shu-v0")
  common/         Petri net building blocks and instance loader; instances/ holds the benchmarks
  envs/shu/       hyper-heuristic simulator, gym environment and low-level heuristics (algos/)
rl_agent/         train.py, test.py and trained agents (agents/)
results/          benchmark and ablation results (Excel)
```

The Solax instances `sl00`-`sl79` have the same operations as Taillard `ta01`-`ta80` (with an extra tool column), so
the paper's ta01, ta11, ..., ta71 are `sl00`, `sl10`, ..., `sl70` here.

## Getting Started

Python 3.9 to 3.11 is recommended (the render modules use `distutils`, removed in Python 3.12).

```bash
pip install gymnasium stable-baselines3 sb3-contrib torch numpy pandas matplotlib graphviz ipython tqdm
export PYTHONPATH=$PWD/env/petrirl        # Windows: set PYTHONPATH=%CD%\env\petrirl
cd rl_agent
python train.py                           # trains on the instances set in main()
python test.py                            # select instances and evaluate the trained agents
```

```python
import gymnasium as gym
import petrirl

env = gym.make("petrirl-shu-v0", benchmark="Solax", instance_id="sl00",
               reward_f="G", commitment_length=5).unwrapped
```

To try the hyper-heuristic interactively (train, solve the Taillard benchmarks and replay the decisions on the Petri
net), see [PetriRL Studio](https://github.com/Sofiene-Uni/PetriRL-Studio).

## Citation and Credit

Developed by Sofiene Lassoued during his PhD at South Westphalia University of Applied Sciences (Fachhochschule
Südwestfalen, FH SWF). You are welcome to use and extend this work; please keep this credit and cite:

```bibtex
@unpublished{lassoued2026hyperheuristic,
  title  = {Policy-Based Deep Reinforcement Learning Hyper-heuristics with Temporal Actions Abstraction for Job-Shop Scheduling Problems},
  author = {Lassoued, Sofiene and Gobachew, Asrat and Lier, Stefan and Schwung, Andreas},
  note   = {Preprint submitted to Knowledge-Based Systems},
  year   = {2026}
}

@article{lassoued2024petrirl,
  title   = {Introducing PetriRL: An innovative framework for JSSP resolution integrating Petri nets and event-based reinforcement learning},
  author  = {Lassoued, Sofiene and Schwung, Andreas},
  journal = {Journal of Manufacturing Systems},
  volume  = {74},
  pages   = {690--702},
  year    = {2024},
  doi     = {10.1016/j.jmsy.2024.04.028}
}
```
