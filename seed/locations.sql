INSERT INTO locations (name, city, address)
VALUES
    ('Bengaluru', 'Bengaluru', NULL),
    ('Chennai - Olympia Pinnacle', 'Chennai', NULL),
    ('Goa - Bhaskar', 'Goa', NULL),
    ('Goa - Charak', 'Goa', NULL),
    ('Gurugram - DLF Cybercity', 'Gurugram', NULL),
    ('Hyderabad - Equinox', 'Hyderabad', NULL),
    ('Hyderabad - Waverock', 'Hyderabad', NULL),
    ('Hyderabad- Argus Block', 'Hyderabad', NULL),
    ('Indore - Brilliant Centre', 'Indore', NULL),
    ('Jaipur - Fort Anandam', 'Jaipur', NULL),
    ('Kochi- Nippon Q1', 'Kochi', NULL),
    ('Kolkata - Godrej Genesis', 'Kolkata', NULL),
    ('Mumbai - Time Square', 'Mumbai', NULL),
    ('Nagpur - Gargi', 'Nagpur', NULL),
    ('Nagpur - Maitreyi', 'Nagpur', NULL),
    ('Noida- Logix Cyber Park', 'Noida', NULL),
    ('Pune - Aryabhata', 'Pune', NULL),
    ('Pune - Bhageerath', 'Pune', NULL),
    ('Pune - HJ-Atharvaveda', 'Pune', NULL),
    ('Pune - HJ-Rgveda', 'Pune', NULL),
    ('Pune - HJ-Samaveda', 'Pune', NULL),
    ('Pune - HJ-Yajurveda', 'Pune', NULL),
    ('Pune - Pingala', 'Pune', NULL),
    ('Pune - Ramanujan', 'Pune', NULL)
ON CONFLICT (name) DO UPDATE
SET city = EXCLUDED.city;
