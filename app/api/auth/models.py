from tortoise import fields, models

class ApiKey(models.Model):
    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, unique=True, index=True)
    name = fields.CharField(max_length=255) # Client name
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    # Billing
    price_per_million_chars = fields.FloatField(default=15.0) # $15 per 1M chars default

class UsageLog(models.Model):
    id = fields.IntField(pk=True)
    api_key = fields.ForeignKeyField('models.ApiKey', related_name='usage_logs')
    characters = fields.IntField()
    cost = fields.DecimalField(max_digits=10, decimal_places=4)
    timestamp = fields.DatetimeField(auto_now_add=True)
