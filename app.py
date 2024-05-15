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
    texto_registro = StringProperty("")

    def on_press_registro(self):
        self.texto_registro = "Creando Registro..."
        name = self.ids.name_input.text
        address = self.ids.address_input.text
        age = self.ids.age_input.text
        phone = self.ids.phone_input.text
        last_name = self.ids.last_name_input.text
        #cleaning the fileds
        self.ids.name_input.text=""
        self.ids.address_input.text=""
        self.ids.age_input.text=""
        self.ids.phone_input.text=""
        self.ids.last_name_input.text=""
        #creating the sql conection and inserting data in the db
        complete_name = name + " " + last_name
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        c.execute("INSERT INTO registros (name,age,address,phone) VALUES (?,?,?,?)",(complete_name,age,address,phone))
        conn.commit()
        c.execute("SELECT id FROM registros WHERE name=?",(complete_name,))
        id_number = c.fetchall()[0][0]
        c.execute("INSERT INTO attendance (student_id,name,age,address) VALUES (?,?,?,?)",(id_number,complete_name,age,address))
        c.execute("INSERT INTO payments (student_id,clases_number,total) VALUES(?,?,?)",(id_number,0,0))
        conn.commit() 
        conn.close()
        QR_name = self.generate_QR(complete_name,id_number,age,address,phone)
        self.generate_pdf(QR_name,complete_name,id_number,phone)
        self.texto_registro = "Registro Completado"
        
    def generate_QR(self,name,id,age,address,phone):
        text = f'nombre:{name},id:{id},Edad:{age},localidad:{address},telefono:{phone}'
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        file_name = f"QR_{name}.png"
        path = f"{general_path}/Images/{file_name}"
        qr_img.save(path)
        return file_name

    def generate_pdf(self,QR_name,name,id,phone):
        logo_path = f"{general_path}/Images/f=ma11.png"
        QR_path = f"{general_path}/Images/{QR_name}"
        responsiva_path = f"{general_path}/Images/responsiva.jpg"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times","B",11)
        pdf.multi_cell(58,12,f"Nombre:{name} \nNúmero de alumno: {id} \nTelefono: {phone}",0,align='L')
        pdf.rect(10,10,58,48)#data rectangle
        pdf.rect(68,10,43,48)#QR rectangle
        pdf.rect(111,10,90,48)#logo rectangle
        pdf.dashed_line(0,70,212,70,2,1)
        pdf.line(60,280,160,280)
        pdf.text(95,285,"Firma del tutor")
        pdf.image(QR_path,68,13,42,42)
        pdf.image(logo_path,132,13,50,45)#credential
        pdf.image(logo_path,160,65,43,55)#responsive
        pdf.image(responsiva_path,20,100,180,160)
        pdf.output(f"{general_path}/pdfs/{name}.pdf","F")
        os.remove(QR_path)

class reportes(Screen):
    pass

class escanear(Screen):
    
    text_label = StringProperty("QR code info will be shown here")
    buttons_desactived = BooleanProperty(True)
    record = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(escanear, self).__init__(**kwargs)
        self.capture = None
        self.scanning = True

    def on_enter(self):
        self.start_camera()

    def on_leave(self):
        global id
        self.stop_camera()
        self.text_label= ""
        self.buttons_desactived = True

    def start_camera(self):
        self.record = True
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / 1.0)

    def update(self, dt):
        global id
        ret, frame = self.capture.read()
        if ret:
            qr_codes = decode(frame)
            if qr_codes:
                data = qr_codes[0].data.decode()
                pattern_id = r'id:\d+'
                matches = re.findall(pattern_id, data)
                id = matches[0][3:]
                self.buttons_desactived = False
                self.text_label = self.get_info(id)
                self.stop_camera()
                
    def stop_camera(self):
        self.record = False
        if self.capture:
            self.capture.release()

    def get_info(self,id):
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c= conn.cursor()
        query = "SELECT name FROM registros WHERE id=?"
        c.execute(query,(id,))
        name=c.fetchall()[0][0]
        query = "SELECT clases_number FROM payments WHERE student_id=?"
        c.execute(query,(id,))
        num_class = c.fetchall()[0][0]
        data = f"Número de alumno: {id}\nNombre: {name}\nClases restantes: {num_class}"
        return data
    
    def mark_present(self):
        global id
        mark_attendance(id)
        GetNumClases_OrSubstract(id,True)
        
class pagos(Screen):

    def on_enter(self):
        global id
        if id:
            self.ids.id.text = id
            self.ids.id.readonly = True
        else:
            self.ids.id.readonly= False
        return

    def pay_call(self):
        global id
        amount = self.ids.pay_register.text
        num_class = self.ids.class_register.text
        if not id:
            id = self.ids.id.text
        pay(id,amount,num_class)

    def get_daily_income(self):
        data = date.today().strftime("%d-%m-%Y")
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        query2 = 'SELECT "%s" FROM payments'%data
        print(query2)
        c.execute(query2)
        data = c.fetchall()
        total = sum([num[0] for num in data])
        return total
    
    def get_monthly_income(self):
        pass

class buscar_alumno(Screen):

    text_label = StringProperty("Datos")
    search_name = ""
    activate_delete = BooleanProperty(True)
    activate_attendance = BooleanProperty(True)

    def search_press(self):
        global id
        self.search_name = self.ids.search.text
        id = self.ids.search_id.text
        #cleaning the fields
        self.ids.search.text = ""
        self.ids.search_id.text = ""
        if id:
            conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
            c = conn.cursor()
            c.execute("SELECT * FROM registros WHERE id=?",(id,))
            label = c.fetchall()
            if label:
                num_class = GetNumClases_OrSubstract(id,False)
                self.text_label = f"""Nombre: {label[0][1]} \nTelefono: {label[0][4]}\nClases restantes: {num_class}"""
                self.activate_delete = False
                self.activate_attendance = False 
            else:
                self.text_label = "Registro Inexistente"
                self.activate_delete = True
                self.activate_attendance = True

        elif self.search_name:
            conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
            c = conn.cursor()
            c.execute("SELECT * FROM registros WHERE name=?",(self.search_name,))
            label = c.fetchall()
            if label:
                self.text_label = f"""Nombre: {label[0][1]} \nTelefono: {label[0][4]}"""
                id = label[0][0]
                self.activate_delete = False
                self.activate_attendance = False 
            else:
                self.text_label = "Registro Inexistente"
                self.activate_delete = True
                self.activate_attendance = True
        conn.commit()
        conn.close() 

    def mark_present(self):
        global id
        if not id:
            id = self.ids.search_id.text
        mark_attendance(id)
        GetNumClases_OrSubstract(id,True)
        self.text_label="Asistencia Registrada"

    def delete_register(self):
        global id
        print(id)
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        if id:
            c.execute("DELETE FROM registros WHERE id=?",(id,))
            c.execute("DELETE FROM attendance WHERE student_id=?",(id,))
        elif self.search_name:
            c.execute("SELECT id FROM registros WHERE name =?",(self.search_name))
            id = c.fetchall()[0][0]
            c.execute("DELETE FROM registros WHERE name=?",(id,))
            c.execute("DELETE FROM attendande WHERE id=?",(id,))

        conn.commit()
        conn.close()
        self.text_label = "Registro Eliminado"

class reporte_de_asistencias(Screen):
    day = date.today().day
    month = date.today().month
    year = date.today().year
    text_label = StringProperty("Selecciona un periodo")

    def on_january(self):
        get_df_dates(1,1,self.year,31,1,self.year)
        self.text_label="Reporte generado"
    def on_febuary(self):
        get_df_dates(1,2,self.year,29,2,self.year)
        self.text_label="Reporte generado"
    def on_march(self):
        get_df_dates(1,3,self.year,31,3,self.year)
        self.text_label="Reporte generado"
    def on_april(self):
        get_df_dates(1,4,self.year,30,4,self.year)
        self.text_label="Reporte generado"
    def on_may(self):
        get_df_dates(1,5,self.year,31,5,self.year)
        self.text_label="Reporte generado"
    def on_june(self):
        get_df_dates(1,6,self.year,30,6,self.year)
        self.text_label="Reporte generado"
    def on_july(self):
        get_df_dates(1,7,self.year,31,7,self.year)
        self.text_label="Reporte generado"
    def on_august(self):
        get_df_dates(1,8,self.year,31,8,self.year)
        self.text_label="Reporte generado"
    def on_september(self):
        get_df_dates(1,9,self.year,30,9,self.year)
        self.text_label="Reporte generado"
    def on_october(self):
        get_df_dates(1,10,self.year,31,10,self.year)
        self.text_label="Reporte generado"
    def on_november(self):
        get_df_dates(1,11,self.year,30,11,self.year)
        self.text_label="Reporte generado"
    def on_december(self):
        get_df_dates(1,12,self.year,31,12,self.year)
        self.text_label="Reporte generado"

class reporte_de_ingresos(Screen):
    day = date.today().day
    month = date.today().month
    year = date.today().year
    text_label = StringProperty("Selecciona un periodo")
    activate_buttons= BooleanProperty(True)

    def press_month(self):
        self.activate_buttons= False
    def on_january(self):
        self.text_label="Reporte generado"
    def on_febuary(self):
        self.text_label="Reporte generado"
    def on_march(self):
        self.text_label="Reporte generado"
    def on_april(self):
        self.text_label="Reporte generado"
    def on_may(self):
        self.text_label="Reporte generado"
    def on_june(self):
        self.text_label="Reporte generado"
    def on_july(self):
        self.text_label="Reporte generado"
    def on_august(self):
        self.text_label="Reporte generado"
    def on_september(self):
        self.text_label="Reporte generado"
    def on_october(self):
        self.text_label="Reporte generado"
    def on_november(self):
        self.text_label="Reporte generado"
    def on_december(self):
        self.text_label="Reporte generado"
    def get_daily_income(self):
        date = present_date
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        query2 = "SELECT %s FROM payments"%date####ERORR HERE
        c.execute(query2)
        data = c.fetchall()
        print(data)
        total=0
        if data:
            total = sum([num[0] for num in data])
        self.text_label = f"Ingreso de hoy: {total}"

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

        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS registros(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            age TEXT,
                            address TEXT,
                            phone TEXT
                        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                            student_id INTEGER NOT NULL,
                            name TEXT,
                            age INTEGER,
                            address TEXT,
                            FOREIGN KEY(student_id) REFERENCES registros(id)
                        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
                            student_id INTEGER NOT NULL,
                            clases_number INTEGER,
                            total INTEGER,
                            FOREIGN KEY(student_id) REFERENCES registros(id)
                        )''')
        conn.commit()
        conn.close()
        return kv
   
if __name__ == '__main__':
    Application().run()

