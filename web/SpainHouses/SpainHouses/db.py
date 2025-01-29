from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
from math import ceil

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = PyMongo(current_app).db
       
    return db

db = LocalProxy(get_db)

def build_paginated_offers_query(filters):
    query = {}

    if filters:
        price_query = {}
        area_query = {}

        if "minPrice" in filters:
            price_query["$gte"] = int(filters["minPrice"])
        if "maxPrice" in filters:
            price_query["$lte"] = int(filters["maxPrice"])
        if price_query:
            query["price"] = price_query

        if "minArea" in filters:
            area_query["$gte"] = int(filters["minArea"])
        if "maxArea" in filters:
            area_query["$lte"] = int(filters["maxArea"])
        if area_query:
            query["constructed_m2"] = area_query

        if "minRooms" in filters:
            query["rooms"] = {"$gte": int(filters["minRooms"])}
        if "minBathrooms" in filters:
            query["bathrooms"] = {"$gte": int(filters["minBathrooms"])}
        if "constructionDate" in filters:
            query["construction_date"] = {"$gte": filters["constructionDate"]}
        if "offerType" in filters:
            query["offer_type"] = filters["offerType"]
        if "city" in filters:
            query["location.city"] = {"$regex": filters["city"], "$options": "i"}
        if "state" in filters:
            query["location.state"] = {"$regex": filters["state"], "$options": "i"}
        if "postcode" in filters:
            query["location.postcode"] = filters["postcode"]
        if "number" in filters:
            query["location.number"] = filters["number"]
        if "fullTextSearch" in filters:
            query["$text"] = {"$search": filters["fullTextSearch"]}

    return query

def get_paginated_offers(filters, page, offers_per_page):
    page = max(1, page)
    query = build_paginated_offers_query(filters)

    pipeline = [
        {"$match": query},
        {"$sort": {"update_date": -1}},
        {"$group": {
                "_id": "$ref",
                "doc": {"$first": "$$ROOT"}
            }
        },
        {"$replaceRoot": {"newRoot": "$doc"}},
        {"$skip": (page - 1) * offers_per_page},
        {"$limit": offers_per_page}
    ]

    total_docs = len(list(db.announcements.aggregate([
        {"$match": query},
        {"$group": {"_id": "$ref"}}
    ])))
    
    total_pages = ceil(total_docs / offers_per_page)
    offers = db.announcements.aggregate(pipeline)
    
    return {
        'total_docs': total_docs,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': offers_per_page,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'docs': list(offers)
    }

def get_offer(ref):
    pipeline = [
        {
            "$match": {
                "ref": ref
            }
        },
        {
            "$sort": {
                "update_date": -1
            }
        },
        {
            "$limit": 1
        }
    ]

    offer = db.announcements.aggregate(pipeline).next()

    return offer
    
def get_offers_by_ref(refs):
    return list(db.announcements.find({"ref": {"$in": refs}}))

def get_offer_historic(ref):
    return list(db.announcements.find({"ref": ref}))