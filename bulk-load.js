conn = new Mongo();
db = conn.getDB("sensor");

var cursor = db.readings.find({"time": {"$exists": true, "$type": 2 }}); 
while (cursor.hasNext()) { 
    var doc = cursor.next(); 
    db.readings.update(
        {"_id" : doc._id}, 
        {"$set" : {"time" : new Date( doc.time.replace(" ","T") )}}
    ) 
};

// mongo "mongodb://sensorUser:password@localhost:27017/sensor?retryWrites=true&authSource=admin&authMechanism=SCRAM-SHA-1" mod_load.js
