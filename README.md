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

De esta forma se habilitará un scheduler de Dask y 3 Workers, un servidor de Mongo y un cliente web para Mongo.

Se puede acceder al cliente Mongo en [http://localhost:8081](http://localhost:8081 "Cliente MongoDB")

```sh
cd local_runtime

./init-local.sh

docker-compose up
```


# Pruebas

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
    collection: "readings"
    auth_mechanism: "&authSource=admin&authMechanism=SCRAM-SHA-1"
  feedback:
    type: "firebase"
    collection: "feedback"

dask:
  scheduler_url: "tcp://127.0.0.1:8786"
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
