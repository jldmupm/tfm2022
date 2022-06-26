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
    type: "mongo"
    host: "localhost"
    database: "sensor"
    port: 27017
    collection: "readings"
    auth_mechanism: "&authSource=admin&authMechanism=SCRAM-SHA-1"
  feedbacks:
    type: "firebase"
    collection: "feedback"
    category: "Ambiente"

dask_cluster:
  scheduler_preconfig: "synchronous" # single-threaded, threads, processes, synchronous, distributed
  scheduler_url: "tcp://127.0.0.1:8786"
  partitions: 4
```

## conf/.env

Fichero de variables de entorno con las credenciales a utilizar en la conexión a las fuentes de datos.

Las variables que puede contener:
```
# The Dask scheduler URL
FIREBASE_FEEDBACK_CREDENTIALS_PATH=...path al fichero de credenciales de Firebase...

MONGODB_SENSOR_CREDENTIALS_USERNAME=...usuario de Mongo...
MONGODB_SENSOR_CREDENTIALS_PASSWORD=...password de Mongo..
```
