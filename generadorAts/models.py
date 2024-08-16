from django.db import models

class Users(models.Model):
    id = models.AutoField(primary_key=True)
    RUC = models.BinaryField()  # Almacena los datos en formato binario
    password = models.TextField()  # Usamos TextField para NVARCHAR(MAX)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'ID: {self.id}, Password: {self.password}'
