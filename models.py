from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from flask import url_for
from datetime import datetime
import uuid

# تهيئة قاعدة البيانات والتشفير
db = SQLAlchemy()
bcrypt = Bcrypt()

# دالة توليد الترقيم السنوي (CAR-2025-0001, EQP-2025-0001)
def generate_sequential_id(prefix):
    year = datetime.now().year
    last_record = None
    if prefix == "CAR":
        last_record = Car.query.filter(Car.unique_id.like(f"{prefix}-{year}-%")).order_by(Car.id.desc()).first()
    elif prefix == "EMP":
        last_record = Employee.query.filter(Employee.unique_id.like(f"{prefix}-{year}-%")).order_by(Employee.id.desc()).first()
    elif prefix == "DOC":
        last_record = Document.query.filter(Document.unique_id.like(f"{prefix}-{year}-%")).order_by(Document.id.desc()).first()
    elif prefix == "EQP":
        last_record = Equipment.query.filter(Equipment.unique_id.like(f"{prefix}-{year}-%")).order_by(Equipment.id.desc()).first()

    if last_record and last_record.unique_id:
        try:
            last_num = int(last_record.unique_id.split('-')[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{year}-{new_num:04d}"

# نموذج إعدادات الشركة
class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), default="شركة الأرشيف")
    logo_filename = db.Column(db.String(200), default="default-logo.png")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def logo_url(self):
        if self.logo_filename and self.logo_filename != "default-logo.png":
            return url_for('uploaded_file', filename=f'logos/{self.logo_filename}', _external=True)
        return url_for('static', filename='images/default-logo.png')

# نموذج المستخدم
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, archivist, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def can_edit(self):
        return self.role in ['admin', 'archivist']

# نموذج السيارة
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: generate_sequential_id("CAR"))
    chassis_number = db.Column(db.String(100), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    car_type = db.Column(db.String(50))
    color = db.Column(db.String(30))
    year = db.Column(db.Integer)
    plate_number = db.Column(db.String(20))
    status = db.Column(db.String(20), default="active")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('CarFile', backref='car', lazy=True, cascade="all, delete-orphan")
    maintenance_records = db.relationship('MaintenanceRecord', backref='car', lazy=True, cascade="all, delete-orphan")

class CarFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(10))  # 'image' or 'pdf'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)

# نموذج سجل صيانة السيارة
class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # هيدروليك، محرك، بواط...
    date = db.Column(db.Date, nullable=False)
    cost = db.Column(db.Float)  # التكلفة
    notes = db.Column(db.Text)  # ملاحظات
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MaintenanceRecord {self.maintenance_type} for Car {self.car_id}>'

# نموذج الموظف
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: generate_sequential_id("EMP"))
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="active")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('EmployeeFile', backref='employee', lazy=True, cascade="all, delete-orphan")
    salary_info = db.relationship('EmployeeSalary', backref='employee', uselist=False)

class EmployeeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(10))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

# نموذج الوثيقة
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: generate_sequential_id("DOC"))
    title = db.Column(db.String(200), nullable=False)
    doc_type = db.Column(db.String(50))
    source = db.Column(db.String(100))
    issue_date = db.Column(db.Date)
    receive_date = db.Column(db.Date, default=datetime.utcnow)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="pending")
    folder = db.Column(db.String(100), default="عام")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('DocumentFile', backref='document', lazy=True, cascade="all, delete-orphan")

class DocumentFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(10))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)

# نموذج سجل النشاط
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(50))
    action = db.Column(db.String(50))    # create, update, delete, login, logout
    entity_type = db.Column(db.String(50)) # Car, Employee, Document, User, Equipment...
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

# نموذج المعدات (قلابات، خلاطات، لودرات...)
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: generate_sequential_id("EQP"))
    equipment_type = db.Column(db.String(50), nullable=False)  # قلاب، خلاطة، لودر...
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    chassis_number = db.Column(db.String(100), unique=True, nullable=False)
    engine_number = db.Column(db.String(100))
    capacity = db.Column(db.Float)  # السعة بالمتر المكعب
    max_load = db.Column(db.Float)  # الحمولة القصوى بالطن
    current_km = db.Column(db.Integer, default=0)  # عداد الكيلومترات/الساعات
    last_maintenance_km = db.Column(db.Integer, default=0)  # آخر كيلومتر تم عنده الصيانة
    next_maintenance_km = db.Column(db.Integer)  # الكيلومتر التالي للصيانة
    status = db.Column(db.String(20), default="active")  # active, maintenance, out_of_service
    purchase_date = db.Column(db.Date)  # تاريخ الشراء
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    fuel_records = db.relationship('FuelRecord', backref='equipment', lazy=True, cascade="all, delete-orphan")
    maintenance_records = db.relationship('EquipmentMaintenance', backref='equipment', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Equipment {self.brand} {self.model}>'

# نموذج سجلات الوقود
class FuelRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # باللتر
    price_per_liter = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    current_km = db.Column(db.Integer, nullable=False)  # عداد الكيلومترات عند التعبئة
    fuel_type = db.Column(db.String(20))  # بنزين، ديزل...
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FuelRecord {self.quantity}L for Equipment {self.equipment_id}>'

# نموذج صيانة المعدات
class EquipmentMaintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # دورية، طارئة، إصلاح...
    description = db.Column(db.String(100))  # تغيير زيت، فلتر هواء...
    date = db.Column(db.Date, nullable=False)
    cost = db.Column(db.Float)
    current_km = db.Column(db.Integer, nullable=False)  # كيلومترات المعدة عند الصيانة
    next_maintenance_km = db.Column(db.Integer)  # كيلومترات الصيانة القادمة
    performed_by = db.Column(db.String(100))  # من قام بالصيانة
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EquipmentMaintenance {self.maintenance_type} for Equipment {self.equipment_id}>'

# نموذج إعدادات الرواتب
class SalarySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daily_rate = db.Column(db.Float, nullable=False, default=100.0)  # قيمة اليوم
    hourly_rate = db.Column(db.Float, nullable=False, default=15.0)  # قيمة الساعة
    overtime_daily_rate = db.Column(db.Float, nullable=False, default=150.0)  # قيمة اليوم الإضافي
    overtime_hourly_rate = db.Column(db.Float, nullable=False, default=25.0)  # قيمة الساعة الإضافية
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# نموذج راتب الموظف الأساسي
class EmployeeSalary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    base_salary = db.Column(db.Float, nullable=True, default=0.0)  # 👈 تم تعديل هذا الحقل ليقبل القيم الفارغة
    daily_wage = db.Column(db.Float)
    hourly_wage = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج سجل الحضور والغياب
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, half_day
    week_number = db.Column(db.Integer, nullable=False)  # رقم الأسبوع في السنة
    year = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج الساعات والأيام الإضافية
class OvertimeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    overtime_type = db.Column(db.String(20), nullable=False)  # daily, hourly
    quantity = db.Column(db.Float, nullable=False)  # عدد الأيام أو الساعات
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج السلف
class AdvancePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    is_paid = db.Column(db.Boolean, default=False)  # تم سدادها أم لا
    paid_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج سجل الرواتب الأسبوعية
class PayrollRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_days = db.Column(db.Integer, default=6)  # أيام العمل في الأسبوع
    present_days = db.Column(db.Integer, default=0)
    absent_days = db.Column(db.Integer, default=0)
    half_days = db.Column(db.Integer, default=0)
    overtime_days = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    basic_salary = db.Column(db.Float, default=0)
    overtime_amount = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)  # الخصومات (غياب + سلف)
    advances_deduction = db.Column(db.Float, default=0)  # حسم السلف
    net_salary = db.Column(db.Float, default=0)
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)