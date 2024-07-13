import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from mysql.connector import connect, Error
from datetime import datetime, date, timedelta

# 資料庫設置
Base = declarative_base()

class Memo(Base):
    __tablename__ = 'memos'
    id = Column(Integer, primary_key=True)
    course = Column(String(255))  # 指定長度
    assignment = Column(String(255))  # 指定長度
    due_date = Column(Date)

# 從文件讀取 MySQL 連接資訊
def read_db_config(file_path='db_config.txt'):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split(':')
            config[key] = value
    return config

# 創建資料庫
def create_database(config):
    try:
        with connect(
            host=config['host'],
            user=config['username'],
            password=config['password']
        ) as connection:
            create_db_query = f"CREATE DATABASE IF NOT EXISTS {config['database']}"
            with connection.cursor() as cursor:
                cursor.execute(create_db_query)
    except Error as e:
        print(f"Error: '{e}'")

db_config = read_db_config()
create_database(db_config)
DATABASE_URI = f"mysql+mysqlconnector://{db_config['username']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

# 嘗試連接資料庫，如果資料庫不存在則創建
try:
    engine = create_engine(DATABASE_URI)
    Base.metadata.create_all(engine)  # 自動創建資料表
except OperationalError:
    create_database(db_config)
    engine = create_engine(DATABASE_URI)
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# GUI設置
class MemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("功課備忘錄")

        # 設置樣式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Helvetica", 12), padding=10)
        self.style.configure("TLabel", font=("Helvetica", 12), padding=5)
        self.style.configure("TEntry", font=("Helvetica", 12), padding=5, fieldbackground="white")
        self.style.map("TButton", background=[("active", "#45a049")])

        # 課程輸入框
        self.course_label = ttk.Label(root, text="課程")
        self.course_label.grid(row=0, column=0, padx=10, pady=5)
        self.course_entry = ttk.Entry(root)
        self.course_entry.grid(row=0, column=1, padx=10, pady=5)

        # 作業輸入框
        self.assignment_label = ttk.Label(root, text="作業")
        self.assignment_label.grid(row=1, column=0, padx=10, pady=5)
        self.assignment_entry = ttk.Entry(root)
        self.assignment_entry.grid(row=1, column=1, padx=10, pady=5)

        # 截止日期選擇框
        self.due_date_label = ttk.Label(root, text="截止日期")
        self.due_date_label.grid(row=2, column=0, padx=10, pady=5)
        self.due_date_entry = DateEntry(root, date_pattern='yyyy-mm-dd', background='darkblue', foreground='white', borderwidth=2)
        self.due_date_entry.grid(row=2, column=1, padx=10, pady=5)

        # 高亮天數輸入框
        self.highlight_days_label = ttk.Label(root, text="剩餘天數標記")
        self.highlight_days_label.grid(row=3, column=0, padx=10, pady=5)
        self.highlight_days_entry = ttk.Entry(root)
        self.highlight_days_entry.insert(0, "3")  # 預設值
        self.highlight_days_entry.grid(row=3, column=1, padx=10, pady=5)

        # 按鈕區域
        self.add_button = ttk.Button(root, text="新增功課", command=self.add_memo)
        self.add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        self.update_button = ttk.Button(root, text="更新功課", command=self.update_memo)
        self.update_button.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

        self.delete_button = ttk.Button(root, text="刪除功課", command=self.delete_memo)
        self.delete_button.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

        # 排序按鈕
        self.sort_asc_button = ttk.Button(root, text="近到遠", command=lambda: self.load_memos(order='asc'))
        self.sort_asc_button.grid(row=7, column=0, padx=10, pady=5)

        self.sort_desc_button = ttk.Button(root, text="遠到近", command=lambda: self.load_memos(order='desc'))
        self.sort_desc_button.grid(row=7, column=1, padx=10, pady=5)

        # 備忘錄列表框
        self.memos_listbox = tk.Listbox(root, font=("Helvetica", 12), selectmode=tk.SINGLE)
        self.memos_listbox.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky='nsew')

        # 計數標籤
        self.count_label = ttk.Label(root, text="總功課數：0")
        self.count_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5)

        self.load_memos()

    def add_memo(self):
        course = self.course_entry.get()
        assignment = self.assignment_entry.get()
        due_date = self.due_date_entry.get()

        if course and assignment and due_date:
            try:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                new_memo = Memo(course=course, assignment=assignment, due_date=due_date_obj)
                session.add(new_memo)
                session.commit()
                self.load_memos()
                messagebox.showinfo("成功", "功課已新增")
            except ValueError:
                messagebox.showwarning("輸入錯誤", "請輸入有效的日期格式 (YYYY-MM-DD)")
        else:
            messagebox.showwarning("輸入錯誤", "請填寫所有欄位")

    def load_memos(self, order='asc'):
        self.memos_listbox.delete(0, tk.END)
        if order == 'asc':
            memos = session.query(Memo).order_by(Memo.due_date.asc()).all()
        else:
            memos = session.query(Memo).order_by(Memo.due_date.desc()).all()
        
        count = 0
        try:
            highlight_days = int(self.highlight_days_entry.get())
        except ValueError:
            highlight_days = 3  # 預設值

        for memo in memos:
            count += 1
            memo_text = f"{memo.id}: {memo.course} - {memo.assignment} (截止日期: {memo.due_date})"
            if memo.due_date <= date.today() + timedelta(days=highlight_days):
                self.memos_listbox.insert(tk.END, memo_text)
                self.memos_listbox.itemconfig(tk.END, {'fg':'red'})  # 設置字體顏色為紅色
            else:
                self.memos_listbox.insert(tk.END, memo_text)
        
        self.count_label.config(text=f"總功課數：{count}")

    def update_memo(self):
        selected_memo = self.memos_listbox.get(tk.ACTIVE)
        if selected_memo:
            memo_id = int(selected_memo.split(":")[0])
            memo_to_update = session.query(Memo).filter_by(id=memo_id).first()
            if memo_to_update:
                new_course = self.course_entry.get()
                new_assignment = self.assignment_entry.get()
                new_due_date = self.due_date_entry.get()
                if new_course and new_assignment and new_due_date:
                    try:
                        new_due_date_obj = datetime.strptime(new_due_date, "%Y-%m-%d").date()
                        memo_to_update.course = new_course
                        memo_to_update.assignment = new_assignment
                        memo_to_update.due_date = new_due_date_obj
                        session.commit()
                        self.load_memos()
                        messagebox.showinfo("成功", "功課已更新")
                    except ValueError:
                        messagebox.showwarning("輸入錯誤", "請輸入有效的日期格式 (YYYY-MM-DD)")
                else:
                    messagebox.showwarning("輸入錯誤", "請填寫所有欄位")
            else:
                messagebox.showwarning("錯誤", "找不到功課")
        else:
            messagebox.showwarning("錯誤", "請選擇一個功課")

    def delete_memo(self):
        selected_memo = self.memos_listbox.get(tk.ACTIVE)
        if selected_memo:
            memo_id = int(selected_memo.split(":")[0])
            memo_to_delete = session.query(Memo).filter_by(id=memo_id).first()
            if memo_to_delete:
                session.delete(memo_to_delete)
                session.commit()
                self.load_memos()
                messagebox.showinfo("成功", "功課已刪除")
            else:
                messagebox.showwarning("錯誤", "找不到功課")
        else:
            messagebox.showwarning("錯誤", "請選擇一個功課")

# 啟動應用程式
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
