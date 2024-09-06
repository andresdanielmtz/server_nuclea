import agentpy as ap
import random

class Guard(ap.Agent):
    def setup(self):
        self.agentType = 1

    def info_receptor(self, message):
        print(f"Guard received message: {message}")

    def step(self):
        pass

class Drone(ap.Agent):
    def setup(self):
        self.intruders = []
        self.agentType = 0

    def detect_intruder(self):
        print("Detect intruder")
        self.intruders.append(1)

    def talk_to_guard(self):
        guard = random.choice(self.model.guard)
        guard.info_receptor("Intruder detected!")

    def step(self):
        pass

class SimulationModel(ap.Model):
    def setup(self):
        print("Running simulation!!!")
        self.drone = ap.AgentList(self, 1, Drone)
        self.guard = ap.AgentList(self, 1, Guard)
        self.message_queue = self.p.message_queue

    def step(self):
        while not self.message_queue.empty():
            camera_id, intruder_detected = self.message_queue.get()
            for drone in self.drone:
                if intruder_detected:
                    drone.detect_intruder()
                else:
                    drone.talk_to_guard()
        
        self.drone.step()
        self.guard.step()

    def end(self):
        # print(f"Simulation ended. There were {sum(drone.intruders for drone in self.drone)} intruders detected.")
        pass

# No need for if __name__ == "__main__" block as the simulation is controlled by the Flask server