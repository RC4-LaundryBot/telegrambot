from datetime import datetime, timedelta

class MockData():
    def getLevels(self):
        return [5, 8, 11, 14, 17]
    
    def getStatuses(self, level):
        count = 4

        machine_types = [
            "washer-coin",
            "washer-ezlink",
            "dryer-ezlink",
            "dryer-coin"
            ]
        start_times = [
            datetime.now() - timedelta(seconds=100),
            datetime.now() - timedelta(seconds=200),
            datetime.now() - timedelta(seconds=300),
            datetime.now() - timedelta(seconds=400)
            ]
        statuses = [0, 2, 1, 2]
        machine_durations = [30, 30, 40, 40]

        return [
            {
                "level": level,
                "type": machine_types[i],
                "start-time": start_times[i],
                "status": statuses[i],
                "time": datetime.now(),
                "machine-duration": machine_durations[i]
            } for i in range(0, count)
        ]

    def charts(self):
        chart = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}
        n = 0

        for day in chart:
            chart[day] = [x**2 + n for x in range(0, 72)]
            n += 1

        return chart
    