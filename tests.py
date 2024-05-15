# from fpdf import FPDF
import os
# import qrcode
import sqlite3
from datetime import date, datetime
# import cv2
# from pyzbar.pyzbar import decode
# from kivy.clock import Clock
import pandas as pd
import kivy

general_path = os.path.dirname(os.path.abspath(__file__).replace('\\','/'))

# def generate_QR(name,id,age,address,phone):
#     text = f'nombre:{name},id:{id},Edad:{age},localidad:{address},telefono:{phone}'
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(text)
#     qr.make(fit=True)
#     qr_img = qr.make_image(fill_color="black", back_color="white")
#     file_name = f"QR_{name}.png"
#     path = f"android/listas/Images/{file_name}"
#     qr_img.save(path)
#     return file_name

# def generate_pdf(QR_name,name,id,phone):
#     general_path = os.path.dirname(os.path.abspath(__file__).replace('\\','/'))
#     logo_path = f"{general_path}/Images/f=ma11.png"
#     QR_path = f"{general_path}/Images/{QR_name}"
#     responsiva_path = f"{general_path}/Images/responsiva.jpg"
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Times","B",11)
#     pdf.multi_cell(58,12,f"Nombre:{name} \nNúmero de alumno: {id} \nTelefono: {phone}",0,align='L')
#     pdf.rect(10,10,58,48)#data rectangle
#     pdf.rect(68,10,43,48)#QR rectangle
#     pdf.rect(111,10,90,48)#logo rectangle
#     pdf.dashed_line(0,70,212,70,2,1)
#     pdf.line(60,280,160,280)
#     pdf.text(95,285,"Firma del tutor")
#     pdf.image(QR_path,68,13,42,42)
#     pdf.image(logo_path,132,13,50,45)
#     pdf.image(logo_path,160,65,43,55)
#     pdf.image(responsiva_path,20,100,180,160)
#     pdf.output(f"Android/listas/pdfs/Registro_{name}.pdf","F")
#     os.remove(QR_path)

def generate_report(month):
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    sql_query = "SELECT * FROM attendance WHERE substr(date,4,2)='%s'"%month#(date,start,numbers to take)
    df = pd.read_sql(sql_query,conn)
    sort_df = df.sort_values(by='student_id')
    print(sort_df)

def add_attendance(id,day,month,year):
    present_date = "{}-{}-{}".format(day,month,year)
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    c.execute("PRAGMA table_info({})".format("attendance"))
    columns_info = c.fetchall()
    column_exists = any(column[1] == present_date for column in columns_info)
    if column_exists:
        c.execute("UPDATE attendance SET '%s'=1 WHERE student_id=?"%present_date,id)
    else:
        c.execute("ALTER TABLE attendance ADD COLUMN '%s' INTEGER"%present_date)
        conn.commit()
        c.execute("UPDATE attendance SET '%s'= CASE WHEN student_id =? THEN 1 ELSE 0 END"%present_date,id)
    conn.commit()
    conn.close()

def validate_time(string,selected):
    try:
        selected.append(datetime.strptime(string,"%d-%m-%Y"))
        return True
    except:
        return False

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
    #result_df.to_csv(rute+file_name,index=False)
    return result_df

def get_daily_income(date):
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    query2 = 'SELECT "%s" FROM payments'%date
    c.execute(query2)
    data = c.fetchall()
    total = sum([num[0] for num in data])
    print(total)

def pay(day,month,year,id,amount,num_class):
        present_date = f"{day}-{month}-{year}"
        conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(payments)")
        columns_info=c.fetchall()
        column_exists = any(column[1] == present_date for column in columns_info)
        if column_exists:
            query = 'UPDATE payments SET "%s" = ? WHERE student_id = ?'%present_date
            c.execute(query,(amount,id))
            #c.execute("UPDATE payments SET '%s'='%d' WHERE student_id='%s'"%(present_date,amount,id))
        else:
            c.execute("ALTER TABLE payments ADD COLUMN '%s' INTEGER"%present_date)
            conn.commit()
            query = "UPDATE payments SET '%s' = CASE WHEN student_id=? THEN ? ELSE 0 END"%present_date
            c.execute(query,(id,amount))
            conn.commit()
        c.execute("UPDATE payments SET clases_number=? WHERE student_id=?",(num_class,id))
        c.execute("SELECT total FROM payments WHERE student_id=?",(id,))
        new_total = c.fetchall()[0][0]+int(amount)
        c.execute("UPDATE payments SET total=? WHERE student_id=?",(new_total,id))
        conn.commit()
        conn.close()

def get_monthly_income(s_day,s_month,e_day,e_month):
    e_year = "2024"
    s_year = "2024"
    file_name = f"Report_{s_day}_{s_month}_{s_year}---{e_day}_{e_month}_{e_year}.csv"
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    c.execute("SELECT * FROM payments LIMIT 1")
    columns_selected = [datetime.strptime(col[0],"%d-%m-%Y") for col in c.description[4:]]
    start = datetime.strptime(f"{str(s_day)}-{str(s_month)}-{str(s_year)}","%d-%m-%Y")
    end = datetime.strptime(f"{str(e_day)}-{str(e_month)}-{str(e_year)}","%d-%m-%Y")

    period_columns = [date1.strftime("%d-%m-%Y") for date1 in columns_selected if start<=date1<=end]

    dates_query = "SELECT * FROM payments"

    df_dates = pd.read_sql(dates_query,conn)

    selected_dates = df_dates[period_columns]
    data = df_dates[['student_id','clases_number','total']]
    result_df = pd.concat([data,selected_dates],axis=1)
    #result_df.to_csv(file_name,index=False)
    return result_df

def Make0_Nonevalues(table):
    conn = sqlite3.connect(f'{general_path}/data/alumnos.db')
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    print(columns)
    column = columns[3]
    for column in columns:
        query = 'UPDATE %s SET "%s"=0 WHERE "%s" IS NULL'%(table,column,column)
        c.execute(query)
    conn.commit()
    conn.close()

def GetNumClases_OrSubstract(id,subtract_class):
    #this function get the number of clases per student and subtract a class if the parameter
    #subtract_class is True
    conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
    c = conn.cursor()
    query = "SELECT clases_number FROM payments WHERE student_id=?"
    c.execute(query,(id))
    num_class = c.fetchall()[0][0]
    if subtract_class and (num_class!=0):
        num_class-=1
        query = "UPDATE payments SET clases_number=? WHERE student_id=?"
        c.execute(query,(num_class,id))
        conn.commit()
        return num_class
    else:
        return num_class


# ids=['1','2','3','4','5','6','7','8','9']
# day='7'
# month= "05"
# id=""
# # for id in ids:
# add_attendance(id,day,month,"2024")
# print("succesfully inserted data")
# pay(day,month,'2024',id,35,0)
# print("payment succesfully")

#Make0_Nonevalues('payments')
# Make0_Nonevalues('attendance')

# conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
# c = conn.cursor()
# c.execute("PRAGMA table_info({})".format("payments"))
# columns_info = c.fetchall()
# print(columns_info)


# c.execute("PRAGMA table_info({})".format("payments"))
# print(c.fetchall())
# c.execute("PRAGMA table_info({})".format("attendance"))
# print(c.fetchall())
# present_date = '28-04-2024'
# amount = 120
# id = 3
# query = 'UPDATE payments SET "%s" = ? WHERE student_id = ?'%present_date
# c.execute(query,(amount,id))
# conn.commit()

# conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
# c = conn.cursor()
# c.execute("SELECT * FROM payments")
# print(c.fetchall())
# c.execute("SELECT * FROM attendance")
# print(c.fetchall())

# from kivy.app import App
# from kivy.uix.screenmanager import Screen
# from kivy.clock import Clock
# from kivy.lang import Builder
# import cv2
# from pyzbar.pyzbar import decode
# import re
# from kivy.properties import StringProperty

# Builder.load_file("my.kv")

# class CameraScreen(Screen):
#     def start_camera(self):
#         self.capture = cv2.VideoCapture(0)
#         Clock.schedule_interval(self.update, 1.0 / 30.0)

#     def update(self, dt):
#         ret, frame = self.capture.read()
#         if ret:
#             qr_codes = decode(frame)
#             if qr_codes:
#                 self.ids.qr_label.text = qr_codes[0].data.decode()
#                 self.stop_camera()

#     def stop_camera(self):
#         if hasattr(self, 'capture'):
#             self.capture.release()

# class MyApp(App):
#     def build(self):
#         return CameraScreen()


# if __name__ == '__main__':
#     MyApp().run()


#print(GetNumClases_OrSubstract('2',True))

conn = sqlite3.connect(f"{general_path}/data/alumnos.db")
c = conn.cursor()
# c.execute('ALTER TABLE attendance RENAME COLUMN "08-05-2024" TO "09-05-2024"')
# conn.commit()
# c.execute("PRAGMA table_info({})".format("attendance"))
# print(c.fetchall())
# c.execute('UPDATE payments SET "09-05-2024" = 0 WHERE student_id =1')
# conn.commit()
c.execute("SELECT * FROM payments")
print("PAYMENTS ###########\n",c.fetchall())
# c.execute("SELECT * FROM attendance")
# print("ATTENDANCE ###########\n",c.fetchall())
# c.execute("SELECT * FROM registros")
# print("REGISTROS ###########\n",c.fetchall())
#print(date.today().strftime("%d-%m-%Y"))


print(get_df_dates(1,5,2024,30,5,2024))
#print(get_monthly_income(1,5,30,5))
#print(get_daily_income("07-05-2024"))

    
