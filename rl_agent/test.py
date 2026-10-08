import time
import gymnasium as gym
from stable_baselines3 import PPO
import petrirl.envs.shu.gym_env
import os

# Registry: agent_id -> (timesteps, instance_ids)
AGENT_REGISTRY = {
    "sl00": (5e6,  [f"sl{i:02d}" for i in range(0, 10)]),
    "sl10": (5e6,  [f"sl{i:02d}" for i in range(10, 20)]),
    "sl20": (5e6,  [f"sl{i:02d}" for i in range(20, 30)]),
    "sl30": (5e6,  [f"sl{i:02d}" for i in range(30, 40)]),
    "sl40": (5e6,  [f"sl{i:02d}" for i in range(40, 50)]),
    "sl50": (25e6, [f"sl{i:02d}" for i in range(50, 60)]),
    "sl60": (25e6, [f"sl{i:02d}" for i in range(60, 70)]),
    "sl70": (25e6, [f"sl{i:02d}" for i in range(70, 80)]),
}

# Reverse lookup: instance_id -> (agent_id, timesteps)
INSTANCE_TO_AGENT = {
    instance: (agent_id, timesteps)
    for agent_id, (timesteps, instances) in AGENT_REGISTRY.items()
    for instance in instances
}

ALL_INSTANCES = sorted(INSTANCE_TO_AGENT.keys())


def select_instances() -> list[str]:
    print("\nAvailable instances:")
    for i, inst in enumerate(ALL_INSTANCES):
        agent_id, ts = INSTANCE_TO_AGENT[inst]
        steps = f"{int(ts/1e6)}M"
        print(f"  [{i:2d}] {inst}  (agent: {agent_id}, {steps} steps)")

    print("\nEnter selection (examples):")
    print("  all          → run all instances")
    print("  sl05         → single instance by name")
    print("  sl00 sl05 sl72  → space-separated list")
    print("  0 3 7        → space-separated indices")
    print("  0-9          → index range (inclusive)")

    raw = input("\nYour selection: ").strip()

    if raw.lower() == "all":
        return ALL_INSTANCES

    tokens = raw.split()
    selected = []

    for token in tokens:
        # Named instance (e.g. sl05)
        if token in INSTANCE_TO_AGENT:
            selected.append(token)
        # Index range (e.g. 0-9)
        elif "-" in token and not token.startswith("sl"):
            parts = token.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                selected.extend(ALL_INSTANCES[start:end + 1])
            else:
                print(f"  Warning: could not parse range '{token}', skipping.")
        # Numeric index (e.g. 5)
        elif token.isdigit():
            idx = int(token)
            if 0 <= idx < len(ALL_INSTANCES):
                selected.append(ALL_INSTANCES[idx])
            else:
                print(f"  Warning: index {idx} out of range, skipping.")
        else:
            print(f"  Warning: unknown token '{token}', skipping.")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for inst in selected:
        if inst not in seen:
            seen.add(inst)
            unique.append(inst)

    return unique


def agent_test(
        benchmark: str = "Solax",
        instance_id: str = "sl00",
        reward_f: str = "G",
        render_mode: str = "solution",
        commitment_length: int = 1,
):
    agent_id, timesteps = INSTANCE_TO_AGENT[instance_id]
    agent_path = os.path.join("agents", f"Agent_{agent_id}_{int(timesteps)}.0_{reward_f}_{commitment_length}")

    env = gym.make(
        "petrirl-shu-v0",
        render_mode=render_mode,
        benchmark=benchmark,
        instance_id=instance_id,
        reward_f=reward_f,
        commitment_length=commitment_length,
    ).unwrapped

    model = PPO.load(agent_path, device="cpu")
    obs, info = env.reset()

    start_time = time.time()
    steps = 0
    terminated = False
    while not terminated:
        action, _ = model.predict(obs, deterministic=False)
        obs, reward, terminated, truncated, info = env.step(action)
        steps += 1

    elapsed_time = time.time() - start_time
    print(f"\nInference finished in {elapsed_time:.3f} s  |  Steps: {steps}")
    print(f"Makespan: {env.sim.clock}")
    return env.sim.clock


def main():
    benchmark = "Solax"
    render_mode = "solution"
    reward_f = "G"
    commitment_length = 50

    instances = select_instances()

    if not instances:
        print("No valid instances selected. Exiting.")
        return

    print(f"\nRunning {len(instances)} instance(s): {', '.join(instances)}\n")

    results = {}
    for instance_id in instances:
        print(f"--- {instance_id} ---")
        makespan = agent_test(
            benchmark=benchmark,
            instance_id=instance_id,
            reward_f=reward_f,
            render_mode=render_mode,
            commitment_length=commitment_length,
        )
        results[instance_id] = makespan
        print(f"{instance_id}: {makespan}")

    print("\n=== Summary ===")
    for instance_id, makespan in results.items():
        print(f"  {instance_id}: {makespan}")


if __name__ == "__main__":
    main()