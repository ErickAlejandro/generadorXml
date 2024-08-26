from django.db import models

class Users(models.Model):
    id = models.AutoField(primary_key=True)
    RUC = models.BinaryField()  # Almacena los datos en formato binario
    password = models.TextField()  # Usamos TextField para NVARCHAR(MAX)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'ID: {self.id}, Password: {self.password}'

class xmlRegister(models.Model):
    id = models.AutoField(primary_key=True)
    clave = models.CharField(max_length=255)
    contenido = models.TextField()
    fechaRegistro = models.DateTimeField()
    fecha_emision = models.DateField()
    hora_emision = models.TimeField()

    class Meta:
        db_table = 'xmlRegister' 