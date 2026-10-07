-- These queries should return no rows after migrations and catalog seeding.
SELECT 'orphan_floor' AS issue, floors.id::text AS record_id
FROM floors
LEFT JOIN locations ON locations.id = floors.location_id
WHERE locations.id IS NULL
UNION ALL
SELECT 'orphan_bay', bays.id::text
FROM bays
LEFT JOIN floors ON floors.id = bays.floor_id
WHERE floors.id IS NULL
UNION ALL
SELECT 'orphan_workspace', workspaces.id::text
FROM workspaces
LEFT JOIN bays ON bays.id = workspaces.bay_id
WHERE bays.id IS NULL
UNION ALL
SELECT 'orphan_booking_user', bookings.id::text
FROM bookings
LEFT JOIN users ON users.id = bookings.user_id
WHERE users.id IS NULL
UNION ALL
SELECT 'orphan_booking_workspace', bookings.id::text
FROM bookings
LEFT JOIN workspaces ON workspaces.id = bookings.workspace_id
WHERE workspaces.id IS NULL
UNION ALL
SELECT 'invalid_capacity', workspaces.id::text
FROM workspaces
WHERE capacity <= 0
UNION ALL
SELECT 'invalid_booking_window', bookings.id::text
FROM bookings
WHERE end_time <= start_time;

-- Show the installed PostgreSQL enum types and their values.
SELECT type.typname AS enum_type, enum.enumlabel AS enum_value
FROM pg_type AS type
JOIN pg_enum AS enum ON enum.enumtypid = type.oid
WHERE type.typname LIKE 'flexdesk_%'
ORDER BY type.typname, enum.enumsortorder;

-- Show the database's applied Alembic revision.
SELECT version_num FROM flexdesk_db_alembic_version;
