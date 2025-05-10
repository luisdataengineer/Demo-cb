# Usar una imagen base de Python delgada
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos primero para aprovechar el caché de Docker
# si este archivo no cambia entre builds.
COPY requirements.txt .

# Instalar las dependencias de Python especificadas en requirements.txt
# --no-cache-dir reduce el tamaño de la imagen al no almacenar el caché de pip.
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el archivo de la aplicación Flask al directorio de trabajo
COPY app.py .

# Exponer el puerto en el que Gunicorn escuchará dentro del contenedor
EXPOSE 5000

# Comando para ejecutar la aplicación Flask usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

