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
            self.start_drone_override,
            self.check_drone_detection,
            self.stop_controlling_drone,
            self.action_call_cops,
        ]
        self.rules = [
            self.rule_basic_analysis,
            self.rule_panoramic_analysis,
            self.rule_end_panoramic_analysis,
            self.rule_start_drone_override,
            self.rule_check_drone_detection,
            self.rule_stop_controlling_drone,
            self.rule_action_call_cops,
        ]
        self.alarm_count_begin = 0
        self.alarm_count_end = 0
        self.initialize_panoramic_view = False
        self.drone_override = False
        self.drone_override_timer = 0
        self.call_cops = False
        self.alert_checks = 0
        self.important_subjects = ["camera", "drone"]
        self.personal_time = 30  # 10 steps for when he controls the drone

    def see(self):
        if self.alarm_count_end >= 1:
            return

        subjects = self.model.channel["subject"]
        content = self.model.channel["content"]

        if subjects == ["vision"] and content == "intruder":
            self.alarm_count_begin += 1
            self.model.channel = {"subject": [""], "content": ""}
        if subjects == ["Drone"] and content == "intruder":
            self.alarm_count_end += 1

    def basic_analysis(self):
        self.drone_override = False
        self.initialize_panoramic_view = False

    def rule_action_call_cops(self,act):
        if self.personal_time == 3:
            return act==self.action_call_cops

    def action_call_cops(self):
        self.call_cops = True

    def rule_basic_analysis(self, act):
        return self.alarm_count_begin < 3 and act == self.basic_analysis

    def panoramic_analysis(self):
        self.initialize_panoramic_view = True
        self.drone_override = True
        self.drone_override_timer = 0

    def rule_panoramic_analysis(self, act):
        return self.alarm_count_begin >= 3 and act == self.panoramic_analysis

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

    def start_drone_override(self):
        self.drone_override = True
        self.model.channel = {"subject": ["Guard"], "content": "drone_override"}

    def rule_start_drone_override(self, act):
        return (
            self.alarm_count_begin >= 3
            and not self.drone_override
            and act == self.start_drone_override
        )

    def check_drone_detection(self):
        if (
            self.model.channel["subject"] == ["Drone"]
            and self.model.channel["content"] == "intruder"
        ):
            print("Intruder detected")

    def rule_check_drone_detection(self, act):
        return self.drone_override and act == self.check_drone_detection

    def stop_controlling_drone(self):
        self.drone_override = False
        self.initialize_panoramic_view = False
        self.personal_time = 30
        self.alarm_count_begin = 0
        self.alarm_count_end = 0

    def rule_stop_controlling_drone(self, act):
        return self.personal_time <= 0 and act == self.stop_controlling_drone



    def step(self):
        self.see()
        if self.drone_override:
            self.personal_time -= 1
        if self.drone_override:
            self.drone_override_timer += 1
            if self.drone_override_timer >= 5:
                self.drone_override_timer = 0
                self.drone_override = False
                self.initialize_panoramic_view = False
        self.next()

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def give_info(self):
        return {
            "drone_override": self.drone_override,
            "initialize_panoramic_view": self.initialize_panoramic_view,
            "drone_override_timer": self.drone_override_timer,
            "alarm_count_begin": self.alarm_count_begin,
            "alarm_count_end": self.alarm_count_end,
            "alert_checks": self.alert_checks,
            "personal_time": self.personal_time,
            "call_cops": self.call_cops,
        }


class Camera(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.actions = [self.lock_in, self.alert_guard, self.update_vision_result]
        self.rules = [
            self.rule_lock_in,
            self.rule_alert_guard,
            self.rule_update_vision_result,
        ]
        self.id = None
        self.detection = None
        self.locked = False
        self.alert_checks = 0

    def see(self):
        subjects = self.model.channel["subject"]
        content = self.model.channel["content"]

        if subjects == ["drone"] and content == "intruder begin":
            self.alert_checks += 1

    def update_vision_result(self):
        if (
            self.model.channel["subject"] == ["vision_result"]
            and self.model.channel["content"].get("id") == self.id
        ):
            self.detection = self.model.channel["content"].get("result")

    def rule_update_vision_result(self, act):
        return act == self.update_vision_result

    def lock_in(self):
        self.locked = True

    def rule_lock_in(self, act):
        return (
            not self.locked
            and (self.detection == "YES" or self.alert_checks > 0)
            and act == self.lock_in
        )

    def alert_guard(self):
        self.model.channel = {"subject": ["vision"], "content": "intruder"}

    def rule_alert_guard(self, act):
        return self.detection == "YES" and self.locked and act == self.alert_guard

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.see()
        self.next()

    def give_info(self):
        return {
            "id": self.id,
            "locked": self.locked,
            "alert_checks": self.alert_checks,
            "detection": self.detection,
        }


class Drone(ap.Agent):
    def setup(self):
        self.agentType = 3
        self.actions = [
            self.alert_guard,
            self.alert_guard_final,
            self.move,
            self.check_guard_orders,
        ]
        self.rules = [
            self.rule_alert_guard,
            self.rule_alert_guard_final,
            self.rule_move,
            self.rule_check_guard_orders,
        ]
        self.detection = None
        self.pos = [0, 0, 0]  # Starting position
        self.panoramic = False
        self.target_pos = None
        self.override_timer = 0
        self.radius = 10
        self.time_counter = 0
        self.position_history = []
        self.override_duration = 20  # 15 seconds / 3 seconds per step = 5 steps
        self.guard_override = False

    def rule_alert_guard(self, action):
        return (
            self.detection == "YES"
            and not self.panoramic
            and action == self.alert_guard
        )

    def rule_alert_guard_final(self, act):
        return (
            self.detection == "YES" and act == self.alert_guard_final
        )

    def alert_guard(self):
        self.model.channel = {"subject": ["vision"], "content": "intruder"}

    def alert_guard_final(self):
        self.model.channel = {"subject": ["Drone"], "content": "intruder"}

    def move(self):
        if self.guard_override:  # Move to the center if guard_override is True
            if self.target_pos is None:
                self.target_pos = [0, 40, 0]  # Move to the center
                self.override_timer = 0

            self.override_timer += 1
            progress = min(self.override_timer / self.override_duration, 1)

            # Move towards the target position
            self.pos[0] = self.pos[0] + (self.target_pos[0] - self.pos[0]) * progress
            self.pos[1] = self.pos[1] + (self.target_pos[1] - self.pos[1]) * progress
            self.pos[2] = self.pos[2] + (self.target_pos[2] - self.pos[2]) * progress

            # Reset override after reaching the target
            if self.override_timer >= self.override_duration:
                self.guard_override = False
                self.target_pos = None

        else:  # Patrol movement
            waypoints = [
                [-50, 40, -50],  # Corner 1
                [50, 40, -50],  # Corner 2
                [50, 40, 50],  # Corner 3
                [-50, 40, 50],  # Corner 4
            ]
            segment_time = 100
            total_time = len(waypoints) * segment_time
            current_time_in_route = self.time_counter % total_time

            # Segment the route and progress between waypoints
            segment_index = current_time_in_route // segment_time
            next_segment_index = (segment_index + 1) % len(waypoints)
            current_waypoint = waypoints[segment_index]
            next_waypoint = waypoints[next_segment_index]

            # Move between waypoints
            progress_in_segment = (current_time_in_route % segment_time) / segment_time
            self.pos[0] = (
                current_waypoint[0]
                + (next_waypoint[0] - current_waypoint[0]) * progress_in_segment
            )
            self.pos[1] = current_waypoint[1]
            self.pos[2] = (
                current_waypoint[2]
                + (next_waypoint[2] - current_waypoint[2]) * progress_in_segment
            )

        # Update position history
        self.position_history.append(self.pos.copy())
        if len(self.position_history) > 10:
            self.position_history.pop(0)

    def rule_move(self, act):
        return act == self.move

    def rule_check_guard_orders(self, act):
        return act == self.check_guard_orders

    def check_guard_orders(self):
        if (
            self.model.guard[0].drone_override == True
        ):
            self.guard_override = True


    def step(self):
        self.time_counter += 1
        self.check_guard_orders()
        self.move()

    def give_info(self):
        return {
            "position": self.pos,
            "detection": self.detection,
            "panoramic": self.panoramic,
            "position_history": self.position_history,
            "override_timer": self.override_timer,
            "time_counter": self.time_counter,
            "guard_override": self.guard_override,
        }