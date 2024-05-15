###################### KIVY LIBRARYS ###########################
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
##################### ACTION LIBRARYS ##########################
import qrcode
import matplotlib.pyplot as plt
import sqlite3
from fpdf import FPDF
import os
from datetime import date
import cv2
from pyzbar.pyzbar import decode
import re
from datetime import datetime
import pandas as pd
#################### GLOBAL VARIABLES ##########################
Builder.load_file('app.kv')
general_path = os.path.dirname(os.path.abspath(__file__).replace('\\','/'))
#present_date = date.today().strftime("%d-%m-%Y")
present_date = "14-05-2024"
id = None
##################### GLOABAL FUNCTIONS ########################

def pay(s_id,amount,num_class):
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(payments)")
        columns_info=c.fetchall()
        column_exists = any(column[1] == present_date for column in columns_info)
        if column_exists:
            query = 'UPDATE payments SET "%s" = ? WHERE student_id = ?'%present_date
            c.execute(query,(amount,s_id))
            #c.execute("UPDATE payments SET '%s'='%d' WHERE student_id='%s'"%(present_date,amount,id))
        else:
            c.execute("ALTER TABLE payments ADD COLUMN '%s' INTEGER"%present_date)
            conn.commit()
            query = "UPDATE payments SET '%s' = CASE WHEN student_id=? THEN ? ELSE 0 END"%present_date
            c.execute(query,(s_id,amount))
            conn.commit()
        c.execute("UPDATE payments SET clases_number=? WHERE student_id=?",(num_class,s_id))
        c.execute("SELECT total FROM payments WHERE student_id=?",(s_id,))
        new_total = c.fetchall()[0][0]+int(amount)
        c.execute("UPDATE payments SET total=? WHERE student_id=?",(new_total,s_id))
        conn.commit()
        conn.close()

def mark_attendance(s_id):
    global id
    if s_id:
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info({})".format("attendance"))
        columns_info = c.fetchall()
        column_exists = any(column[1] == present_date for column in columns_info)
        if column_exists:
            sql = f"UPDATE attendance SET '{present_date}' = 1 WHERE student_id = ?"
            c.execute(sql,(s_id,))
        else:
            c.execute("ALTER TABLE attendance ADD COLUMN '%s' INTEGER"%present_date)
            conn.commit()
            sql = f"UPDATE attendance SET '{present_date}'= CASE WHEN student_id =? THEN 1 ELSE 0 END"
            c.execute(sql,(s_id,))
        conn.commit()
        conn.close()

def GetNumClases_OrSubstract(id,subtract_class):
    #this function get the number of clases per student and subtract a class if the parameter
    #subtract_class is True
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    query = "SELECT clases_number FROM payments WHERE student_id=?"
    c.execute(query,(id,))
    num_class = c.fetchall()[0][0]

    if subtract_class:
        if num_class!=0:
            num_class-=1
            query = "UPDATE payments SET clases_number=? WHERE student_id=?"
            c.execute(query,(num_class,id))
            conn.commit()
            return num_class
        else:
            pay(id,35,0)
            return num_class
    else:
        return num_class

def Make0_Nonevalues(table):
    conn = sqlite3.connect(f'{general_path}/data/alumnos.db')
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    for column in columns:
        query = 'UPDATE %s SET "%s"=0 WHERE "%s" IS NULL'%(table,column,column)
        c.execute(query)
    conn.commit()
    conn.close()

def get_df_dates(s_day,s_month,s_year,e_day,e_month,e_year):
    file_name = f"Report_{s_day}_{s_month}_{s_year}--{e_day}_{e_month}_{e_year}.csv"
    rute = f"{general_path}/reports/"
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    c.execute("SELECT * FROM attendance LIMIT 1")
    columns_selected = [datetime.strptime(col[0],"%d-%m-%Y") for col in c.description[4:]]
    
    start = datetime.strptime(f"{str(s_day)}-{str(s_month)}-{str(s_year)}","%d-%m-%Y")
    end = datetime.strptime(f"{str(e_day)}-{str(e_month)}-{str(e_year)}","%d-%m-%Y")

    period_columns = [date1.strftime("%d-%m-%Y") for date1 in columns_selected if start<=date1<=end]

    dates_query = "SELECT * FROM attendance"

    df_dates = pd.read_sql(dates_query,conn)
    selected_dates = df_dates[period_columns]
    data = df_dates[['name','age','address']]
    result_df = pd.concat([data,selected_dates],axis=1)
    result_df.to_csv(rute+file_name,index=False)
    return result_df

#################### APP FUNCTIONALITIS ########################
class main_screen(Screen):
    pass

class agregar_alumno(Screen):
    pass

class reportes(Screen):
    pass

class escanear(Screen):
    pass
class pagos(Screen):
    pass
class buscar_alumno(Screen):
    pass

class reporte_de_asistencias(Screen):
    pass

class reporte_de_ingresos(Screen):
    pass

class Navegar(ScreenManager):
    pass
  
class Application(App):
    def build(self):
        Window.size = (360,640)
        kv = ScreenManager()
        kv.add_widget(main_screen(name='1'))
        kv.add_widget(agregar_alumno(name='2'))
        kv.add_widget(reportes(name='3'))
        kv.add_widget(escanear(name='4'))
        kv.add_widget(buscar_alumno(name='5'))
        kv.add_widget(reporte_de_asistencias(name='6'))
        kv.add_widget(reporte_de_ingresos(name='7'))
        kv.add_widget(pagos(name='8'))
        return kv
   
if __name__ == '__main__':
    Application().run()

