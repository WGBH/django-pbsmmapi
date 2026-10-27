from django.db import migrations

# Only number rows that arrive without one, matching the Season trigger, so the
# ordinal PBS sends (or that an editor enters for a provisional row) is kept.
RESPECT_EXPLICIT_ORDINAL = """
CREATE OR REPLACE FUNCTION set_episode_ordinal()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ordinal IS NULL THEN
        NEW.ordinal := (
            SELECT COALESCE(MAX(ordinal), 0) + 1
            FROM pbsmm_episode
            WHERE season_id = NEW.season_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

ALWAYS_OVERWRITE_ORDINAL = """
CREATE OR REPLACE FUNCTION set_episode_ordinal()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ordinal := (
        SELECT COALESCE(MAX(ordinal), 0) + 1
        FROM pbsmm_episode
        WHERE season_id = NEW.season_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("episode", "0020_alter_episode_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=RESPECT_EXPLICIT_ORDINAL,
            reverse_sql=ALWAYS_OVERWRITE_ORDINAL,
        ),
    ]
