import agentpy as ap
from owlready2 import *
from flask import jsonify


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

    def step(self):
        self.guard.step()
        self.cameras.step()
        self.drone.step()


class Guard(ap.Agent):
    def setup(self):
        self.agentType = 1
        self.alert_checks = 0
        self.actions = [
            self.basic_analysis,
            self.panoramic_analysis,
            self.final_alert,
            self.drone_control,
            self.drone_end_control,
        ]
        self.rules = [
            self.rule_basic_check,
            self.rule_panoramic_check,
            self.rule_final_alert,
            self.rule_drone_end_control,
            self.rule_drone_control,
        ]
        self.alarmCount_begin = 0
        self.drone_override = False
        self.alarmCount_end = 0
        self.call_the_cops = False
        self.drone_control_timer = 0
        self.initialize_panoramic_view = False

    def info_receptor(self, message):
        print(f"Guard received message: {message}")

    def drone_control(self):
        self.model.drone[0].pos = [0, 50, 0]
        self.drone_control_timer += 1
        self.drone_override = True

    def rule_drone_control(self, act):
        return (
            self.drone_override == False
            and self.initialize_panoramic_view == True
            and self.drone_control_timer < 15
            and act == self.drone_control
        )

    def drone_end_control(self):
        self.model.drone[0].pos = None
        self.drone_override = False
        self.initialize_panoramic_view = False
        self.drone_control_timer = 0

    def rule_drone_end_control(self, act):
        return (
            self.drone_override == True
            and self.drone_control_timer > 15
            and act == self.drone_end_control
        )

    def panoramic_analysis(self):
        self.initialize_panoramic_view = True
        self.drone_override = True

    def basic_analysis(self):
        self.drone_override = False
        self.initialize_panoramic_view = False

    def rule_basic_check(self, act):
        return self.alert_checks < 3 and act == self.basic_analysis

    def rule_panoramic_check(self, act):
        return self.alert_checks >= 3 and act == self.panoramic_analysis

    def final_alert(self):
        print("Alerta Final !!!!!")
        self.call_the_cops = True
        return

    def rule_final_alert(self, act):
        return self.alarmCount_end > 0 and act == self.final_alert

    def increase_alarm_count_begin(self):
        self.alarmCount_begin += 1

    def increase_alarm_count_end(self):
        self.alarmCount_end += 1

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.next()

    def give_info(self):
        return jsonify(
            {
                "countAlarm_begin": self.alarmCount_begin,
                "countAlarm_end": self.alarmCount_end,
                "droneOverride": self.drone_override,
                "callTheCops": self.call_the_cops,
                "alert_checks": self.alert_checks,
                "drone_timer": self.drone_control_timer,
                "initialize_panoramic_view": self.initialize_panoramic_view,
            }
        )


class Camera(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.alert_checks = 0
        self.rules = {self.rule_lock_in, self.rule_alert_guard}
        self.actions = {self.lock_in, self.alert_guard}
        self.id = None
        self.detection = None
        self.locked = False

    def lock_in(self):
        self.locked = True

    def rule_lock_in(self, act):
        return self.locked == False and self.detection == "YES" and act == self.lock_in

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
        self.next()

    def give_info(self):
        return jsonify(
            {"id": self.id, "detection": self.detection, "locked": self.locked}
        )


class Drone(ap.Agent):
    def setup(self):
        self.agentType = 3
        self.actions = [self.alert_guard, self.alert_guard_final]
        self.rules = [self.rule_alert_guard, self.rule_alert_guard_final]
        self.detection = None
        self.pos = None
        self.panoramic = False

    def rule_alert_guard(self, action):
        return (
            self.detection == "YES"
            and self.panoramic == False
            and action == self.alert_guard
        )

    def rule_alert_guard_final(self, act):
        return (
            self.detection == "YES"
            and self.panoramic == True
            and act == self.alert_guard_final
        )

    def alert_guard_final(self):
        SecurityModel.guard[0].increase_alarm_count_end()

    def alert_guard(self):
        SecurityModel.guard[0].increase_alarm_count_begin()

    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    action()

    def step(self):
        self.next()

    def give_info(self):
        return jsonify(
            {"detection": self.detection, "pos": self.pos, "panoramic": self.panoramic}
        )
