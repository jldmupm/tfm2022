// The first script is a JavaScript file. It creates a user,
// authenticates the user, and then creates a database with a
// collection.

// Create user
dbAdmin = db.getSiblingDB("admin");
dbAdmin.createUser({
    user: "sensorUser",
    pwd: "password",
    customData: { description: "to use for sensor read/write"},
    roles: [{ role: "userAdminAnyDatabase", db: "admin" }],
    mechanisms: ["SCRAM-SHA-1"],
});

// Authenticate user
dbAdmin.auth({
    user: "sensorUser",
    pwd: "password",
    mechanisms: ["SCRAM-SHA-1"],
    digestPassword: true,
});

// Create DB and collection
db = new Mongo().getDB("sensor");
db.createCollection("readings", { capped: false });
