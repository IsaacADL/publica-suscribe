#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Archivo: procesador_de_medicamento.py
# Capitulo: 3 Estilo Publica-Subscribe
# Autor(es): Andrea Sarahí Rodarte María Guadalupe Celaya e Isaac Alejandro Díaz.
# Version: 2.0.1 Mayo 2017
# Descripción:
#
#   Esta clase define el rol de un suscriptor, es decir, es un componente que recibe mensajes.
#
#   Las características de ésta clase son las siguientes:
#
#                                  procesador_de_medicamento.py
#           +-----------------------+-------------------------+------------------------+
#           |  Nombre del elemento  |     Responsabilidad     |      Propiedades       |
#           +-----------------------+-------------------------+------------------------+
#           |                       |                         |  - Se suscribe a los   |
#           |                       |                         |    eventos generados   |
#           |                       |  - Procesar valores     |    por el wearable     |
#           |     Procesador de     |    externos para ingesta|    Xiaomi My Band.     |
#           |     Medicamento       |    programada de.       |  - Define los valores  |
#           |                       |    medicamentos.        |    para ingesta de     |
#           |                       |                         |    medicamentos.       |
#           |                       |                         |  - Notifica al monitor |
#           |                       |                         |    cuando se detecta   |
#           |                       |                         |    que un medicamento  |
#           |                       |                         |    debe ser ingerido.   |  
#           +-----------------------+-------------------------+------------------------+
#
#   A continuación se describen los métodos que se implementaron en ésta clase:
#
#                                               Métodos:
#           +------------------------+--------------------------+-----------------------+
#           |         Nombre         |        Parámetros        |        Función        |
#           +------------------------+--------------------------+-----------------------+
#           |                        |                          |  - Recibe la ínforma- |
#           |       consume()        |          Ninguno         |    ción de los medica-|
#           |                        |                          |    mentos.            |
#           |                        |                          |                       |
#           +------------------------+--------------------------+-----------------------+
#           |                        |  - ch: propio de Rabbit. |  - Procesa y detecta  |
#           |                        |  - method: propio de     |    valores propios del|
#           |                        |     Rabbit.              |    consumo de medica- |
#           |       callback()       |  - properties: propio de |    mentos.            |
#           |                        |     Rabbit.              |                       |
#           |                        |  - body: mensaje recibi- |                       |
#           |                        |     do.                  |                       |
#           +------------------------+--------------------------+-----------------------+
#           |    string_to_json()    |  - string: texto a con-  |  - Convierte un string|
#           |                        |     vertir en JSON.      |    en un objeto JSON. |
#           +------------------------+--------------------------+-----------------------+
#
#
#           Nota: "propio de Rabbit" implica que se utilizan de manera interna para realizar
#            de manera correcta la recepcion de datos, para éste ejemplo no shubo necesidad
#            de utilizarlos y para evitar la sobrecarga de información se han omitido sus
#            detalles. Para más información acerca del funcionamiento interno de RabbitMQ
#            puedes visitar: https://www.rabbitmq.com/
#
#-------------------------------------------------------------------------
import pika
import sys
sys.path.append('../')
from monitor import Monitor
import time
import datetime 


class ProcesadorRitmoCardiaco:

    def consume(self):
        try:
            # Se establece la conexión con el Distribuidor de Mensajes
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            # Se solicita un canal por el cuál se enviarán los signos vitales
            channel = connection.channel()
            # Se declara una cola para leer los mensajes enviados por el
            # Publicador
            channel.queue_declare(queue='medicine', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(on_message_callback=self.callback, queue='medicine')
            channel.start_consuming()  # Se realiza la suscripción en el Distribuidor de Mensajes
        except (KeyboardInterrupt, SystemExit):
            channel.close()  # Se cierra la conexión
            sys.exit("Conexión finalizada...")
            time.sleep(1)
            sys.exit("Programa terminado...")

    def callback(self, ch, method, properties, body):
        json_message = self.string_to_json(body)
        current_date = json_message['datetime']
        #Se obtienen las horas y minutos actuales.
        current_hour = current_date[11] + current_date[12]
        current_minute =  current_date[14] + current_date[15]
        #Se obtienen las horas y minutos de la primera ingesta de medicamento.
        intake_time = datetime.datetime.strptime(json_message['first_intake'], '%H:%M').time()
        intake_hour = intake_time.hour
        intake_minute = intake_time.minute
        #Se calcula la hora de siguiente ingesta,

        dose_time = int(json_message['hour'])#Lapso de tiempo entre ingestas
        current_intake = (int(intake_hour)+dose_time) 
        current_intake = current_intake if current_intake<24 else current_intake-24
        #debe ser igual a la hora actual para notificar.
        if  str(current_intake) == str(current_hour) and current_minute == str(intake_minute):
            monitor = Monitor()
            monitor.print_med_notification(json_message['datetime'], json_message['id'],
             json_message['dose'], json_message['medicine'], json_message['model'], json_message['hour'])

        time.sleep(1)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def string_to_json(self, string):
        message = {}
        string = string.decode('utf-8')
        string = string.replace('{', '')
        string = string.replace('}', '')
        values = string.split(', ')
        for x in values:
            v = x.split(': ')
            message[v[0].replace('\'', '')] = v[1].replace('\'', '')
        return message

if __name__ == '__main__':
    p_ritmo_cardiaco = ProcesadorRitmoCardiaco()
    p_ritmo_cardiaco.consume()
