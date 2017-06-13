import random, datetime, dateutil.relativedelta, time, json
from kafka import KafkaProducer
from AssetBuilder import AssetBuilder
from KuduConnection import KuduConnection

class DataGenerator():

    # Initialize generator by reading in all config values
    def __init__(self, config, file):
        for section in ['sensor device data', 'hadoop']:
            if section not in config:
                raise Exception('Error: missing [%s] config' % (section))

        self._config = {}

        # Hadoop Config Data
        self._config['kafka_brokers'] = config['hadoop']['kafka_brokers']
        self._config['kafka_topic'] = config['hadoop']['kafka_topic']
        self._config['kudu_master'] = config['hadoop']['kudu_masters']
        self._config['kudu_port'] = config['hadoop']['kudu_port']

        # Well configuration data
        self._config['wells'] = int(config['well information']['wells'])
        self._config['min_lat'] = float(config['well information']['min_lat'])
        self._config['max_lat'] = float(config['well information']['max_lat'])
        self._config['min_long'] = float(config['well information']['min_long'])
        self._config['max_long'] = float(config['well information']['max_long'])
        self._config['chemicals'] = config['well information']['chemicals']

        self._config['days_history'] = int(config['sensor device data']['days_history'])
        self._config['measurement_interval'] = int(config['sensor device data']['measurement_interval'])

        self._raw_measurements = []
        self._maintenance_costs = []
        self._maintenance_logs = []

        self._kudu = KuduConnection(self._config['kudu_master'], self._config['kudu_port'])
        #self._kafka_producer = KafkaProducer(bootstrap_servers=self._config['kafka_brokers'], api_version=(0, 10))

        self._ab = AssetBuilder(self._config['wells'], self._kudu)

    def generateStaticData(self, load = True):
        self._ab.build_wells(self._config['min_lat'],self._config['max_lat'],
                             self._config['min_long'],self._config['max_long'],self._config['chemicals'])
        self._ab.build_assets(load = load)

    def generateHistoricData(self):
        self._ab.build_assets(load = False)
        days_history = self._config['days_history']
        measurement_interval = self._config['measurement_interval']
        end_date = datetime.datetime.now()
        start_date = (end_date - dateutil.relativedelta.relativedelta(days=days_history)) \
                        .replace(hour=0, minute=0, second=0, microsecond=0)

        for simulation_date in [start_date + datetime.timedelta(days = x) for x in range(0, days_history)]:
            end_of_day = simulation_date.replace(hour=0,minute=0,second=0,microsecond=0) + datetime.timedelta(days=1)

            for simulation_time in [simulation_date + datetime.timedelta(seconds = x)
                     for x in range(0, int((end_of_day-simulation_date).total_seconds()), measurement_interval)]:
                self._ab.build_readings(time.mktime(simulation_time.timetuple()))
