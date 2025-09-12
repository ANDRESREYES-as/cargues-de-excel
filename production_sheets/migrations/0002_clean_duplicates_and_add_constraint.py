from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('production_sheets', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            -- Primero, eliminamos los detalles de producción de las planillas duplicadas
            DELETE FROM production_sheets_productiondetail
            WHERE production_sheet_id NOT IN (
                SELECT MIN(id)
                FROM production_sheets_productionsheet
                GROUP BY manifest_number
            );
            
            -- Luego eliminamos las planillas duplicadas
            DELETE FROM production_sheets_productionsheet
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM production_sheets_productionsheet
                GROUP BY manifest_number
            );
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name='productionsheet',
            constraint=models.UniqueConstraint(
                fields=['manifest_number'],
                name='unique_manifest_number'
            ),
        ),
    ]