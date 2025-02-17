db = db.getSiblingDB('spainhouses');

db.createCollection('announcements');

// Offer indexes
db.announcements.createIndex({ "offer_type": 1, "update_date": 1, "ref": 1, "spider": 1 }, { unique: true });
db.announcements.createIndex({ "price": 1 });
db.announcements.createIndex({ "rooms": 1 });
db.announcements.createIndex({ "ref": 1 });
db.announcements.createIndex({ "constructed_m2": 1 });
db.announcements.createIndex({ "energy_calification": 1 });
db.announcements.createIndex({ "offer_type": 1 });
db.announcements.createIndex({ "timestamp": 1 });
db.announcements.createIndex({ "update_date": 1 });
db.announcements.createIndex({ "location.text": 1 });
db.announcements.createIndex({ "location.state": 1 });
db.announcements.createIndex({ "location.city": 1 });
db.announcements.createIndex({ "location.country": 1 });
db.announcements.createIndex({ "location.street": 1 });
db.announcements.createIndex({ "location.postcode": 1 });
db.announcements.createIndex({ "location.number": 1 });
db.announcements.createIndex({ "title": "text", "description": "text", "location.text": "text" });