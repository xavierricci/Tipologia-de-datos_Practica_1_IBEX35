#!/usr/bin/env python
# coding: utf-8

# Recogida de datos del Ibex35 (para simplificar el formato para mostrar los datos mantenemos las mismas 35 empresas como referencia, en caso de que el listado cambie, se deberia empezar un nuevo listado).

# In[1]:



# Cargando librerias
import os
import requests
import pandas as pd
import numpy
import csv
from bs4 import BeautifulSoup
from dateutil.tz import gettz
from time import sleep
import datetime
import matplotlib.pyplot as plt


#para que el programa funcione igual aunque lo lancemos desde cualquier lugar del mundo usamos como referencia la hora de madrid
def today():
    t=datetime.datetime.now(gettz("Europe/Madrid")).isoformat()
    year=t[0:4]
    month=t[5:7]
    day=t[8:10]
    return day+"/"+month+"/"+year
#'07/04/2020'

#creamos una funcion para iterar por los datos que nos interesan
#vemos que el primer nombre esta en /html/body/div[1]/table/tbody/tr[4]/td[2]/div[1]/form/div[6]/table/tbody/tr[2]/td[1]
#y que su precio de cierre es       /html/body/div[1]/table/tbody/tr[4]/td[2]/div[1]/form/div[6]/table/tbody/tr[2]/td[2]
def iteracionTabla(tabla,x):
    listado = []
    name=""
    price=""
    #creamos un contador para recorrer las filas identificadas en el html con 'tr'
    nroFila=-1
    for fila in tabla.find_all("tr"):
        #para cada fila se selecciona 
        if nroFila==x:
            #creamos un contador para recorrer las celdas identificadas con 'td'
            nroCelda=0
            for celda in fila.find_all('td'):
                #el contador nos permite seleccionar la casilla que queremos. la guardamos en la lista
                if nroCelda==0:
                    name=celda.text
                    listado.append(name)
                if nroCelda==1:
                    price=celda.text
                    listado.append(price)
                nroCelda=nroCelda+1
        nroFila=nroFila+1
    return listado

#recogemos tambien el total (creo) PUEDE SERVIR PARA HACER UNA COMPARATIVA GENERAL?
def ibexTotal(tabla2):
    listadoExtra=[]
    date=""
    price=""
    nroFila=-1
    for fila in tabla2.find_all("tr"):
        if nroFila==0:
            #creamos un contador para recorrer las celdas identificadas con 'td'
            nroCelda=0
            for celda in fila.find_all('td'):
                #guardamos el precio
                if nroCelda==2:
                    price=celda.text
                if nroCelda==6:
                    date=celda.text
                    listadoExtra.append(date) 
                    # permite el seguimiento de la fecha de la entrada (fin de semana la bolsa no carga)
                    listadoExtra.append(price)
                nroCelda=nroCelda+1
        nroFila=nroFila+1
    return listadoExtra

#anadimos los resultados a una sola lista 
def listadoDiario(tabla,tabla2):
    listadoTotal=[]
    listadoTotal.append(ibexTotal(tabla2)) 
    for x in range(35):  
        listadoTotal.append(iteracionTabla(tabla,x))    
    return listadoTotal
#un solo documento continene: el total diario(creo), la fecha y las 35 empresas con su valor 

#listadoDiario()[0]


def programaRecogida():
    #indicamos la web
    url_page = 'http://www.bolsamadrid.es/esp/aspx/Mercados/Precios.aspx?indice=ESI100000000'

    #introducimos el html en un objeto beautifulSoap
    page = requests.get(url_page).text 
    soup = BeautifulSoup(page, "lxml")

    #seleccionamos la tabla a partir del Xpath //*[@id="ctl00_Contenido_tblAcciones"] que copiamos con el boton derecho sobre el inspector de html de firefox
    tabla = soup.find('table', attrs={'id': "ctl00_Contenido_tblAcciones"})

    tabla2 = soup.find('table', attrs={'id': "ctl00_Contenido_tblÍndice"})

    
    #ordenamos los datos recogidos en dos listas separadas para crear un dataframe
    list = []
    list = listadoDiario(tabla,tabla2)

    nombres=[]
    for x in range(len(list)):
        nombres.append(list[x][0])
    
    #los datos originales de los precios estan en string y conun punto para los miles y coma para los decimales. Convertimos este formato a float.
    precios=[]
    for x in range(len(list)):
        #cambiamos el punto de millar por nada y la coma decimal por un punto decimal, redondeando a 3 decimales
        precios.append(round(float(list[x][1].replace('.','').replace(',','.')), 3))
    

    #creacion de un dataframe
    fecha = list[0][0]
    nombres[0] = 'TOTAL'
    data = {'empresa': nombres,
            fecha: precios
            }

    df = pd.DataFrame (data, columns = ['empresa',fecha])


    #almacenado de los datos en un csv que se va actualizando siempre que la fecha de entrada de los datos haya cambiado 

    #primero nos aseguramos de si el documento ya existe y si no existe lo creamos
    if os.path.isfile('ibex35.csv') == False:
        df.to_csv('ibex35.csv', encoding='utf −8 ',index=False,sep=",")

    #creamos un documento de trabajo importando los datos ya guardados
    dfGuardado = pd.read_csv('ibex35.csv',sep=",")

    
    #miramos si hoy ya se ha hecho la carga para evitar cargar dos veces los mismos datos
    if dfGuardado.columns[-1] != (today()):
        #es los datos que estamos cargando son los mismos del dia anterior es pq la bolsa no abre hoy (findesemana o catastrofe)
        if dfGuardado.columns[-1][0:10] >= (fecha):
            dfGuardado[today() +'_Cerrado'] = precios #en caso de que la ficha no se modifique (el fin de semana la bolsa no se actualiza) no habra entrada 
        else:
            dfGuardado[today()] = precios #en caso de que la ficha no se modifique (el fin de semana la bolsa no se actualiza) no habra entrada 

        dfGuardado.to_csv('ibex35.csv', encoding='utf −8 ',index=False,sep=",")
    else:
        pass


    
def plotibex35(NombreCSVentreComillas):
    dfGuardado = pd.read_csv(NombreCSVentreComillas,sep=",")
    
    #creamos un listado de cabeceras
    cabeceras=[]
    for date in range(len(dfGuardado.columns[1:])):
        cabeceras.append(dfGuardado.columns[1:][date])
   

    # Creamos un listado con todos los valores (se podrian llamar por filas para respesetar la evolucion de cada empresa)
    Row_list =[] 
    for row in range(len(dfGuardado)): 
        # Create list for the current row 
        for cabecera in cabeceras:
            #print(row)
            Row_list.append(round(dfGuardado[cabecera][row],3))
    
    # Creamos un rango de espacios del grafico
    largoXfila=(len(cabeceras))
    
    # Seleccionamos los valores que vamos a representar
    datos_Y=(Row_list[0:largoXfila]) 
  
    inicial=1
    rango_X=range(inicial,inicial+largoXfila)
    
    x = rango_X
    y = datos_Y
    labels = cabeceras
    
    plt.plot(x, y)
    plt.xticks(x, labels, rotation='vertical')
    plt.margins(0.2)
    plt.subplots_adjust(bottom=0.15)

    #seleccionamos los 10 primeros caracteres de la fecha pq en caso de que la bolsa este cerrada, no queremos incluir esa informacion en el titulo 
    plt.title("Evolución del Ibex 35 entre " +labels[0][0:10]+" y "+labels[-1][0:10])
    plt.ylabel('Total al cierre (miles €)')
    plt.legend(['Evolucion del Total'], loc=4)
    
    return plt.show()

     
def esFechaCorrecta(fechafinal):
           
    dia=(today()[0:2])
    mes=today()[3:5]
    anyo=today()[6:10]
    
        
    diafinal=(fechafinal[0:2])
    mesfinal=fechafinal[3:5]
    anyofinal=fechafinal[6:10]
        
    totalActual = (int(anyo)*1000) + (int(mes)*100) + int(dia)
    totalFinal = (int(anyofinal)*1000) + (int(mesfinal)*100) + int(diafinal) 
    
    return totalActual<totalFinal
    
################################funciones de mantenimiento ##################################

#esta funcion permite borrar la ultima columna, esto es muy util durante el periodo de pruebas
def borrarUltimaColumna(NombreCSVentreComillas):
    dfGuardado = pd.read_csv(NombreCSVentreComillas,sep=",")
    del dfGuardado[dfGuardado.columns[-1]]
    dfGuardado.to_csv(NombreCSVentreComillas, encoding='utf −8 ',index=False,sep=",")

#programa para convertir listados antiguos al formato de nuestro csv con precios en float con punto para decimal
#esta funcion solo es útil para las personas que utilizaron la version anterior que guardaba en los csv los numeros en string separados por espacio
def cambiarFormatoLista(NombreCSVentreComillas):
    dfGuardado222 = pd.read_csv(NombreCSVentreComillas,sep=",")
    for m in dfGuardado222.columns[1:]:
        sinComa=[]
        for entrada in dfGuardado222[m]:
            #cambiamos el punto de millar por nada y la coma decimal por un punto decimal, redondeando a 3 decimales
            sinComa.append(round(float(entrada.replace('.','').replace(',','.')),3))
        dfGuardado222[m]=sinComa 
        
    return dfGuardado222.to_csv(NombreCSVentreComillas, encoding='utf −8 ',index=False,sep=",")


#######################################################################################
#######################################################################################
#######################################################################################

# esta funcion arranca el programa (que ya no se apaga) y lo lanza cada dia a las 17:45, hora de madrid cuando se cierra la bolsa 
#al lanzar el programa se tiene que decidir hasta que dia tiene que recoger los datos
def lanzarScraping(fechafinal):
    print('Arrancado')
    #today=datetime.datetime.now(gettz("Europe/Madrid")).isoformat()[1:10]
    
    PERIOD_OF_TIME = 60*60*24 # 24h 

    while True :
        
        horaMadrid = datetime.datetime.now(gettz("Europe/Madrid")).isoformat()[11:16]
           
        
        if esFechaCorrecta(fechafinal)==False:
            print("La fecha escogida ha de ser posterior al dia de hoy: " + today())
            break
            
        elif (horaMadrid > '18:00'):
     
            programaRecogida()
            
            print("Datos recogidos el " + today() +" a las "+horaMadrid)
            
            #una vez recogidos los datos si se ha llegado a la fecha indicada se termina el programa se para
            if today() == fechafinal: 
                print("El programa ha finalizado la recogida de datos")
                plotibex35('ibex35.csv')
                break
                
            #Si no aun no se ha llegado a la fecha final el programa espera hasta el dia siguiente para relanzarse 
            print("La proxiama carga de datos será en 24 horas")
            plotibex35('ibex35.csv')
            sleep(PERIOD_OF_TIME)
            
        else:
            print("Ahora en Madrid son las "+ horaMadrid)
            print("Aun no es la hora... Lo volveremos a itentar en una hora")
            plotibex35('ibex35.csv')
            sleep(60*60) # Si aun no es la hora, volver a intentarlo en 1h
            
            
            
# Escribir la fecha en que el programa debe dejar de recoger datos entre comillas.          
lanzarScraping('31/03/2021')

#En caso de hacer pruebas y recoger los datos antes del cierre, esta función borrará la última entrada del documento guaradado
#borrarUltimaColumna()




dfGuardado222 = pd.read_csv('ibex35.csv',sep=",")
dfGuardado222




