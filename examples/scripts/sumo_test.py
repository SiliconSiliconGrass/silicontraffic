import os
import sys
import random
import time
from tqdm import tqdm

curr_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(curr_dir, "../data")
root_dir = os.path.join(curr_dir, "../..")
sys.path.insert(0, root_dir)

from silicontraffic import ssumo
from silicontraffic.monitor import GlobalMonitor, MovementsMonitor

sumocfg_path = os.path.join(data_dir, "sumo/MoST/most.sumocfg")

# create engine
engine = ssumo.Engine(sumocfg_path, use_gui=False)

# create data monitors
global_monitor = GlobalMonitor()
movements_monitor = MovementsMonitor()

# # attach monitors to engine
global_monitor.attach_to(engine) # TODO: this monitor is TOO SLOW!!!
movements_monitor.attach_to(engine)

def choose_phases():
    # this is a random example of phase determination
    return {
        traffic_light.id: random.randint(0, len(traffic_light.phases) - 1)
        for traffic_light in engine.road_net.traffic_lights
    }

num_steps = 600
min_phase_duration = 30

# perform one simple episode
engine.reset()
start_time = time.time()
for step in tqdm(range(int(num_steps / min_phase_duration)), desc="Simulating"):
    actions = choose_phases()

    for traffic_light_id, phase_index in actions.items():
        engine.set_traffic_light_phase(traffic_light_id, phase_index)

    engine.step(step_num=min_phase_duration)

# terminate the engine
engine.terminate()

avg_queue_length = global_monitor.get_avg_queue_length()
avg_waiting_time = global_monitor.get_avg_waiting_time()
avg_travel_time = global_monitor.get_avg_travel_time()

print(f"Avg Queue Length: {avg_queue_length}")
print(f"Avg Waiting Time: {avg_waiting_time}")
print(f"Avg Travel Time: {avg_travel_time}")

print(f"Simulation Time: {time.time() - start_time}")