# Desarrollo

## Obtener el código
```sh
git clone git@github.com:jldmupm/tfm2022.git
```

## Instalar las dependencias

```
cd tfm2022

poetry install
```

## Preparar el entorno de ejecución local

```sh
./run-local.sh
```

De esta forma se habilitarán los servicios mediante containers:
 - un scheduler de Dask (con el dashboard activo).
 - 3 Workers de Dask.
 - un servidor de base de datos Mongo .
 - un cliente web para Mongo.
 - un scheduler para ejecutar el análisis periodicamente.

Además se ejecutará el dashboard de análisis principal en: [http://localhost:5000/dashboard](http://localhost:5000 "Analysis")

Se puede acceder al cliente Mongo en [http://localhost:8081](http://localhost:8081 "Cliente MongoDB")

Se puede acceder al dashboard de Dask en [http://localhost:8787](http://localhost:8787 "Dashboard Dash")


# Testing

```sh
./test.sh
```

# Configuración

## conf/config.yml

Fichero con la configuración de las fuentes de datos, el cliente Dask y el Dashboard.

El contenido del fichero:
```yaml
datasources:
  sensors:
    host: "127.0.0.1"
    database: "sensor"
    port: 27017
    collection: "readings"
    auth_mechanism: "&authSource=admin&authMechanism=SCRAM-SHA-1"
  feedbacks:
    collection: "feedback"
    category: "Ambiente"

cluster:
  engine: "dask"
  scheduler_type: "distributed" #"processes" #"distributed"
  scheduler_url: "127.0.0.1:8786"
  partitions: 2
  workers: 3

cache:
  enable: False
  host: "127.0.0.1"
  port: 27017
  database: "cache_db"
  collection: "cache_collection"
  
data: # mappings
  feedback:
    category: "Ambiente" # vote category containing votes related to the environment
    sense:
      # maps a measure with a reason from the votes
      temperature_hot:
        pos: ['Temperatura Perfecta']
        neg: ['Demasiado calor']
        
      temperature_cold:
        pos: ['Temperatura Perfecta']
        neg: ['Demasiado frío']

      humidity_hot:
        pos: ['Temperatura Perfecta']
        neg: ['Demasiado calor']
        
      humidity_cold:
        pos: ['Temperatura Perfecta']
        neg: ['Demasiado frío']

      luminosity:
        pos: ['Iluminación correcta']
        neg: ['Poca luz']

      co2:
        pos: ['Ambiente agradable']
        neg: ['Ambiente denso']

      noise:
        pos: ['Sin ruido']
        neg: ['Demasiado ruido']

      movement:
        pos: []
        neg: []
        
  sensors:
    # maps a measure with sensor types
    temperature_hot: ['room_temp', 'add_temp', 'surf_temp']
    temperature_cold: ['room_temp', 'add_temp', 'surf_temp']
    humidity_hot: ['humidity']
    humidity_cold: ['humidity']
    luminosity: ['luminosity']
    movement: ['movement']
    co2: ['co2']
    noise: ['noise']

api:
  host: '127.0.0.1'
  port: 9080
```

## conf/.env

Fichero de variables de entorno con las credenciales a utilizar en la conexión a las fuentes de datos.

Las variables que puede contener:
```
# The Dask scheduler URL
FIREBASE_FEEDBACK_CREDENTIALS_PATH=...path al fichero de credenciales de Firebase...

MONGODB_SENSOR_SENSOR_USERNAME=...usuario de Mongo...
MONGODB_SENSOR_SENSOR_PASSWORD=...password de Mongo...

MONGODB_CACHE_USERNAME=...usuario de Mongo...
MONGODB_CACHE_PASSWORD=...password de Mongo...

SCHEDULER_URL=127.0.0.1:8786

MONGO_HOST=127.0.0.1
MONGO_DATABASE=sensor
MONGO_PORT=27017
MONGO_COLLECTION=readings
MONGO_AUTH_MECHANISM=&authSource=admin&authMechanism=SCRAM-SHA-1
FIREBASE_COLLECTION=feedback
FEEDBACK_ANALYSIS_CATEGORY=Ambiente

#USE_FILE_INSTEAD_OF_FIRESTORE=./mod_feedback.csv
```
