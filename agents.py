import agentpy as ap
from owlready2 import *
from flask import jsonify
import math


class SecurityModel(ap.Model):
    def setup(self):
        self.guard = ap.AgentList(self, 1, Guard)
        self.cameras = ap.AgentList(self, 4, Camera)
        self.drone = ap.AgentList(self, 1, Drone)

        self.guard.setup()
        self.cameras.setup()
        self.drone.setup()

        for idx, camera in enumerate(self.cameras):
            camera.id = idx
        self.channel = {
            "subject": [""],
            "content": "",
        }
        self.guard_orders = {
            "x": None,
            "y": None,
        }

    def step(self):
        self.guard.step()
        self.cameras.step()
        self.drone.step()


class Guard(ap.Agent):
    def setup(self):
        self.agentType = 1
        self.actions = [
            self.basic_analysis,
            self.panoramic_analysis,
            self.end_panoramic_analysis,
        ]
        self.rules = [
            self.rule_basic_analysis,
            self.rule_panoramic_analysis,
            self.rule_end_panoramic_analysis,
        ]
        self.alarm_count_begin = 0
        self.alarm_count_end = 0
        self.initialize_panoramic_view = False
        self.drone_override = False
        self.drone_override_timer = 0
        self.alert_checks = 0
        self.important_subjects = ["camera", "drone"]

    def see(self):
        subjects = self.model.channel["subject"]
        content = self.model.channel["content"]

        for subject in subjects:
            if subject in self.important_subjects:
                if content == "intruder final":
                    self.increase_alarm_count_end()
                elif content == "intruder begin":
                    self.increase_alarm_count_begin()

        self.alert_checks += 1

    def basic_analysis(self):
        self.drone_override = False
        self.initialize_panoramic_view = False

    def rule_basic_analysis(self, act):
        return self.alert_checks < 3 and act == self.basic_analysis

    def panoramic_analysis(self):
        self.initialize_panoramic_view = True
        self.drone_override = True
        self.drone_override_timer = 0

    def rule_panoramic_analysis(self, act):
        return self.alert_checks >= 3 and act == self.panoramic_analysis

    def end_panoramic_analysis(self):
        self.initialize_panoramic_view = False
        self.drone_override = False
        self.drone_override_timer = 0
        self.alert_checks = 0

    def rule_end_panoramic_analysis(self, act):
        return (
            self.initialize_panoramic_view == True
            and self.drone_override_timer >= 5  
            and act == self.end_panoramic_analysis
        )

    def increase_alarm_count_begin(self):
        self.alarm_count_begin += 1

    def increase_alarm_count_end(self):
        self.alarm_count_end += 1

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.see()
        if self.drone_override:
            self.drone_override_timer += 1
            if self.drone_override_timer >= 5: 
                self.drone_override_timer = 0
                self.drone_override = False
                self.initialize_panoramic_view = False
        self.next()

    def give_info(self):
        return {
            "drone_override": self.drone_override,
            "initialize_panoramic_view": self.initialize_panoramic_view,
            "drone_override_timer": self.drone_override_timer,
            "alarm_count_begin": self.alarm_count_begin,
            "alarm_count_end": self.alarm_count_end,
            "alert_checks": self.alert_checks,
        }


class Camera(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.alert_checks = 0
        self.rules = {self.rule_lock_in, self.rule_alert_guard}
        self.actions = {self.lock_in, self.alert_guard}
        self.id = None
        self.detection = None
        self.locked = False
        self.test = ""

    def see(self):
        subjects = self.model.channel["subject"]
        content = self.model.channel["content"]

        for subject in subjects:
            if subject == "drone":
                if content == "intruder begin":
                    self.increase_alert_checks()
        return

    def update_vision_result(self, result):
        self.detection = result

    def increase_alert_checks(self):
        self.alert_checks += 1

    def lock_in(self):
        self.locked = True

    def rule_lock_in(self, act):
        return (
            self.locked == False
            and (self.detection == "YES" or self.alert_checks > 0)
            and act == self.lock_in
        )

    def alert_guard(self):
        SecurityModel.guard[0].increase_alarm_count_begin()

    def rule_alert_guard(self, act):
        return (
            self.detection == "YES" and self.locked == True and act == self.alert_guard
        )

    def detect_intruder(self):
        print("Detect intruder")
        self.intruders.append(1)

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.see()
        self.next()

    def give_info(self):
        return jsonify(
            {
                "id": self.id,
                "test": self.model.channel,
                "locked": self.locked,
                "alert_checks": self.alert_checks,
            }
        )


class Drone(ap.Agent):
    def setup(self):
        self.agentType = 3
        self.actions = [self.alert_guard, self.alert_guard_final, self.move]
        self.rules = [self.rule_alert_guard, self.rule_alert_guard_final, self.rule_move]
        self.detection = None
        self.pos = [0, 0, 0]  # Starting position
        self.panoramic = False
        self.target_pos = None
        self.override_timer = 0
        self.radius = 10
        self.time_counter = 0
        self.position_history = []
        self.override_duration = 5  # 15 seconds / 3 seconds per step = 5 steps

    def rule_alert_guard(self, action):
        return self.detection == "YES" and not self.panoramic and action == self.alert_guard

    def rule_alert_guard_final(self, act):
        return self.detection == "YES" and self.panoramic and act == self.alert_guard_final

    def alert_guard(self):
        self.model.channel = {"subject": ["drone"], "content": "intruder begin"}

    def alert_guard_final(self):
        self.model.channel = {"subject": ["drone"], "content": "intruder final"}
        
    def update_vision_result(self, result):
        self.detection = result
    def move(self):
        if self.model.guard[0].drone_override:
            if self.target_pos is None:
                self.target_pos = [0, 0, 40]
                self.override_timer = 0

            self.override_timer += 1
            progress = min(self.override_timer / self.override_duration, 1)

            self.pos[0] = self.pos[0] + (self.target_pos[0] - self.pos[0]) * progress
            self.pos[1] = self.pos[1] + (self.target_pos[1] - self.pos[1]) * progress
            self.pos[2] = self.pos[2] + (self.target_pos[2] - self.pos[2]) * progress

            if self.override_timer >= self.override_duration:
                self.model.guard[0].drone_override = False
                self.target_pos = None
        else:
            angle = (self.time_counter * 3 % 360) * (math.pi / 180)
            self.pos[0] = self.radius * math.cos(angle)
            self.pos[1] = self.radius * math.sin(angle)
            self.pos[2] = 0

        # Record the position history
        self.position_history.append(self.pos.copy())
        if len(self.position_history) > 10:
            self.position_history.pop(0)

    def rule_move(self, act):
        return act == self.move

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.time_counter += 1
        self.next()
        self.move()

    def give_info(self):
        return {
            "position": self.pos,
            "detection": self.detection,
            "panoramic": self.panoramic,
            "position_history": self.position_history,
            "override_timer": self.override_timer,
            "time_counter": self.time_counter,
        }
