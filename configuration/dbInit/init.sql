CREATE TABLE announcement (
	announcementid SERIAL PRIMARY KEY,
	"timestamp" TIMESTAMP without time zone,
	update_date date,
	title text,
	description text,
	price integer,
	location text,
	rooms integer,
	constructed_m2 integer,
	ref text,
	energy_calification text,
	energy_consumption text,
	construction_date date,
	owner text,
	offer_type integer,
	image_urls text,
	url text,
	list_url text,
	spider text
);