class SystemStatus:
    def __init__(self, thermometer, kasa_client, strategy, controller):
        self.thermometer = thermometer
        self.kasa_client = kasa_client
        self.strategy = strategy
        self.controller = controller

    def snapshot(self):
        return {
            "temperature": self.thermometer.get_last_temperature(),
            "target": self.strategy.target_temperature,
            "heating": self.kasa_client.is_on(),
        }

    def get_temperature_history(self):
        return self.thermometer.get_temperature_history()