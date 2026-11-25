import numpy as np 
from sb3_contrib.common.maskable.utils import get_action_masks

def evaluate_policy(model, n_episodes=5):
    env = model.get_env()
    total_rewards = []

    for _ in range(n_episodes):
        obs = env.reset()
        done = False
        ep_reward = 0
        step = 0

        while not done:
            
            env_masks = get_action_masks(env)[0]
            action, _ = model.predict(obs, deterministic=False, action_masks=env_masks )
            obs, reward, done, info = env.step(action)
            ep_reward += reward
            step += 1
            
            if step > 1000:  # Safety break to avoid infinite loops
                print("⚠️ Step limit exceeded, breaking...")
                break
            

        total_rewards.append(ep_reward)

    print(f"🧪 Evaluation over {n_episodes} episodes:")
    print(f"  → Mean reward: {np.mean(total_rewards):.2f}")
    print(f"  → Max reward : {np.max(total_rewards):.2f}")
    print(f"  → Min reward : {np.min(total_rewards):.2f}")