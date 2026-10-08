import  os
import time
import gymnasium as gym
from datetime import datetime
import petrirl
from stable_baselines3 import PPO
import matplotlib.pyplot as plt
import torch



def train_jssp( render_mode="solution",
                benchmark="Solax",
                instance_id="sl01",
                timesteps=1e5,
                reward_f= "G",
                commitment_length=1

               ):
    
    env = gym.make("petrirl-shu-v0",
                   render_mode=render_mode,
                   benchmark=benchmark,
                   instance_id=instance_id,
                   reward_f=reward_f,
                   commitment_length=commitment_length
                   
    ).unwrapped
    
    train_steps= timesteps/commitment_length
    
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_file = f"logs/Log_{instance_id}_{timesteps}_{current_datetime}_{commitment_length}.zip"
    
    policy_kwargs = dict(
    net_arch=dict(pi=[256, 256], vf=[256, 256]),
    activation_fn=torch.nn.ReLU
    )
    
    model = PPO ( policy="MlpPolicy",
                  env=env,  
                  learning_rate=3e-4,
                  gamma = 1,
                  clip_range=0.2,
                  ent_coef = 0.1, 
                  n_steps=4096,
                  batch_size=1024,
                  n_epochs=10,
                  seed=101,
                  policy_kwargs=policy_kwargs,
                  verbose=1,
                  tensorboard_log=log_file
              )


    start_time = time.time()  
    model.learn(total_timesteps=train_steps)
    
    end_time = time.time()  
    elapsed_time = end_time - start_time  
  
        
    # Check if the 'info' file exists
    if os.path.exists('0-info.txt'):
        with open('0-info.txt', 'a') as info_file:
            info_file.write(f" {current_datetime} -The total {instance_id} training time (seconds): {elapsed_time}\n")
    else:
        with open('0-info.txt', 'w') as info_file:
            info_file.write(f" {current_datetime} -The total {instance_id} training time (seconds): {elapsed_time}\n")
      
    print(f"Training took {elapsed_time} seconds")
    model.save(f"agents/Agent_{instance_id}_{timesteps}_{reward_f}_{commitment_length}.zip")
    

    
    
def main():

    render_mode="solution"
    
    benchmark="Solax"
    instances= ["sl00"]


    reward_f="G"
    timesteps =25e6
    
    commitment_length=1
    

    for instance_id  in  instances :
        train_jssp(render_mode=render_mode,
                   benchmark=benchmark,
                   instance_id=instance_id,
                   timesteps=timesteps,
                   reward_f=reward_f,
                   commitment_length=commitment_length
                   )

if __name__ == "__main__":
    main()