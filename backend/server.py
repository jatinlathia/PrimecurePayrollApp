from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str

class SalaryComponents(BaseModel):
    basic: float = 0
    house_rent_allowance: float = 0
    transport_allowance: float = 0
    fixed_allowance: float = 0
    home_collection_visit: float = 0
    professional_tax: float = 0

class EmployeeCreate(BaseModel):
    employee_no: str
    name: str
    designation: str
    date_of_joining: str
    work_location: str
    department: str
    bank_account_no: str
    salary_components: SalaryComponents

class Employee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_no: str
    name: str
    designation: str
    date_of_joining: str
    work_location: str
    department: str
    bank_account_no: str
    salary_components: SalaryComponents
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EmployeeUpdate(BaseModel):
    employee_no: Optional[str] = None
    name: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[str] = None
    work_location: Optional[str] = None
    department: Optional[str] = None
    bank_account_no: Optional[str] = None
    salary_components: Optional[SalaryComponents] = None

class PromotionCreate(BaseModel):
    employee_id: str
    new_designation: str
    new_salary_components: SalaryComponents
    promotion_date: str

class Promotion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    old_designation: str
    new_designation: str
    old_salary: float
    new_salary: float
    promotion_date: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PayslipGenerate(BaseModel):
    employee_id: str
    month: int
    year: int
    paid_days: int
    lop_days: int

class Payslip(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    employee_no: str
    designation: str
    month: int
    year: int
    paid_days: int
    lop_days: int
    earnings: dict
    deductions: dict
    gross_earnings: float
    total_deductions: float
    net_payable: float
    generated_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DashboardStats(BaseModel):
    total_active_employees: int
    total_monthly_payroll: float
    total_payslips_generated: int

# Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def init_admin():
    admin = await db.admins.find_one({"username": "admin"})
    if not admin:
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        await db.admins.insert_one({
            "username": "admin",
            "password_hash": hashed_password.decode('utf-8')
        })

# Auth Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    admin = await db.admins.find_one({"username": request.username}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not bcrypt.checkpw(request.password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": request.username})
    return LoginResponse(token=access_token, username=request.username)

# Employee Routes
@api_router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate, username: str = Depends(verify_token)):
    # Check if employee_no already exists
    existing = await db.employees.find_one({"employee_no": employee_data.employee_no, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Employee number already exists")
    
    employee = Employee(**employee_data.model_dump())
    doc = employee.model_dump()
    await db.employees.insert_one(doc)
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(username: str = Depends(verify_token)):
    employees = await db.employees.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return employees

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str, username: str = Depends(verify_token)):
    employee = await db.employees.find_one({"id": employee_id, "is_active": True}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, employee_data: EmployeeUpdate, username: str = Depends(verify_token)):
    employee = await db.employees.find_one({"id": employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = {k: v for k, v in employee_data.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.employees.update_one({"id": employee_id}, {"$set": update_data})
    
    updated_employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return updated_employee

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, username: str = Depends(verify_token)):
    employee = await db.employees.find_one({"id": employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Soft delete
    await db.employees.update_one(
        {"id": employee_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Employee terminated successfully"}

# Promotion Routes
@api_router.post("/promotions", response_model=Promotion)
async def create_promotion(promotion_data: PromotionCreate, username: str = Depends(verify_token)):
    employee = await db.employees.find_one({"id": promotion_data.employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate old and new salary
    old_components = employee['salary_components']
    old_salary = sum([v for k, v in old_components.items() if k != 'professional_tax'])
    
    new_salary = sum([
        promotion_data.new_salary_components.basic,
        promotion_data.new_salary_components.house_rent_allowance,
        promotion_data.new_salary_components.transport_allowance,
        promotion_data.new_salary_components.fixed_allowance,
        promotion_data.new_salary_components.home_collection_visit
    ])
    
    promotion = Promotion(
        employee_id=promotion_data.employee_id,
        employee_name=employee['name'],
        old_designation=employee['designation'],
        new_designation=promotion_data.new_designation,
        old_salary=old_salary,
        new_salary=new_salary,
        promotion_date=promotion_data.promotion_date
    )
    
    doc = promotion.model_dump()
    await db.promotion_history.insert_one(doc)
    
    # Update employee
    await db.employees.update_one(
        {"id": promotion_data.employee_id},
        {"$set": {
            "designation": promotion_data.new_designation,
            "salary_components": promotion_data.new_salary_components.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return promotion

@api_router.get("/promotions", response_model=List[Promotion])
async def get_all_promotions(username: str = Depends(verify_token)):
    promotions = await db.promotion_history.find({}, {"_id": 0}).sort("promotion_date", -1).to_list(1000)
    return promotions

@api_router.get("/promotions/{employee_id}", response_model=List[Promotion])
async def get_employee_promotions(employee_id: str, username: str = Depends(verify_token)):
    promotions = await db.promotion_history.find({"employee_id": employee_id}, {"_id": 0}).sort("promotion_date", -1).to_list(1000)
    return promotions

# Payslip Routes
@api_router.post("/payslips/generate", response_model=Payslip)
async def generate_payslip(payslip_data: PayslipGenerate, username: str = Depends(verify_token)):
    employee = await db.employees.find_one({"id": payslip_data.employee_id, "is_active": True})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if payslip already exists
    existing_payslip = await db.payslips.find_one({
        "employee_id": payslip_data.employee_id,
        "month": payslip_data.month,
        "year": payslip_data.year
    })
    if existing_payslip:
        raise HTTPException(status_code=400, detail="Payslip already exists for this month")
    
    components = employee['salary_components']
    
    # Calculate earnings (only non-zero components)
    earnings = {}
    if components.get('basic', 0) > 0:
        earnings['Basic'] = components['basic']
    if components.get('house_rent_allowance', 0) > 0:
        earnings['House Rent Allowance'] = components['house_rent_allowance']
    if components.get('transport_allowance', 0) > 0:
        earnings['Transport Allowance'] = components['transport_allowance']
    if components.get('fixed_allowance', 0) > 0:
        earnings['Fixed Allowance'] = components['fixed_allowance']
    if components.get('home_collection_visit', 0) > 0:
        earnings['Home Collection - Visit'] = components['home_collection_visit']
    
    gross_earnings = sum(earnings.values())
    
    # Calculate deductions (only non-zero components)
    deductions = {}
    if components.get('professional_tax', 0) > 0:
        deductions['Professional Tax'] = components['professional_tax']
    
    total_deductions = sum(deductions.values())
    net_payable = gross_earnings - total_deductions
    
    payslip = Payslip(
        employee_id=payslip_data.employee_id,
        employee_name=employee['name'],
        employee_no=employee['employee_no'],
        designation=employee['designation'],
        month=payslip_data.month,
        year=payslip_data.year,
        paid_days=payslip_data.paid_days,
        lop_days=payslip_data.lop_days,
        earnings=earnings,
        deductions=deductions,
        gross_earnings=gross_earnings,
        total_deductions=total_deductions,
        net_payable=net_payable
    )
    
    doc = payslip.model_dump()
    await db.payslips.insert_one(doc)
    return payslip

@api_router.get("/payslips", response_model=List[Payslip])
async def get_payslips(username: str = Depends(verify_token)):
    payslips = await db.payslips.find({}, {"_id": 0}).sort("generated_date", -1).to_list(1000)
    return payslips

@api_router.get("/payslips/{payslip_id}", response_model=Payslip)
async def get_payslip(payslip_id: str, username: str = Depends(verify_token)):
    payslip = await db.payslips.find_one({"id": payslip_id}, {"_id": 0})
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    return payslip

@api_router.get("/payslips/download/{payslip_id}")
async def download_payslip(payslip_id: str, username: str = Depends(verify_token)):
    payslip = await db.payslips.find_one({"id": payslip_id}, {"_id": 0})
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    employee = await db.employees.find_one({"id": payslip['employee_id']}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=20)
    title = Paragraph(f"Payslip for the month of {month_names[payslip['month']]} {payslip['year']}", title_style)
    elements.append(title)
    
    # Employee Pay Summary Header
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.white, spaceAfter=10)
    header_data = [[Paragraph('EMPLOYEE PAY SUMMARY', header_style)]]
    header_table = Table(header_data, colWidths=[7.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # Employee Details
    detail_style = ParagraphStyle('Detail', parent=styles['Normal'], fontSize=9)
    detail_data = [
        [Paragraph('<b>Employee Name:</b>', detail_style), Paragraph(employee['name'], detail_style),
         Paragraph('<b>Employee No:</b>', detail_style), Paragraph(employee['employee_no'], detail_style)],
        [Paragraph('<b>Designation:</b>', detail_style), Paragraph(employee['designation'], detail_style),
         Paragraph('<b>Department:</b>', detail_style), Paragraph(employee['department'], detail_style)],
        [Paragraph('<b>Date of Joining:</b>', detail_style), Paragraph(employee['date_of_joining'], detail_style),
         Paragraph('<b>Bank Account No:</b>', detail_style), Paragraph(employee['bank_account_no'], detail_style)],
        [Paragraph('<b>Paid Days:</b>', detail_style), Paragraph(str(payslip['paid_days']), detail_style),
         Paragraph('<b>LOP Days:</b>', detail_style), Paragraph(str(payslip['lop_days']), detail_style)],
        [Paragraph('<b>Work Location:</b>', detail_style), Paragraph(employee['work_location'], detail_style), '', ''],
    ]
    
    detail_table = Table(detail_data, colWidths=[1.5*inch, 2.25*inch, 1.5*inch, 2.25*inch])
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 15))
    
    # Earnings and Deductions Table
    salary_style = ParagraphStyle('Salary', parent=styles['Normal'], fontSize=9)
    salary_header_style = ParagraphStyle('SalaryHeader', parent=styles['Normal'], fontSize=10, textColor=colors.white)
    
    # Build earnings and deductions rows
    earnings_list = [[Paragraph(k, salary_style), Paragraph(f"₹{v:,.2f}", salary_style)] for k, v in payslip['earnings'].items()]
    deductions_list = [[Paragraph(k, salary_style), Paragraph(f"₹{v:,.2f}", salary_style)] for k, v in payslip['deductions'].items()]
    
    # Make both lists the same length
    max_rows = max(len(earnings_list), len(deductions_list))
    while len(earnings_list) < max_rows:
        earnings_list.append(['', ''])
    while len(deductions_list) < max_rows:
        deductions_list.append(['', ''])
    
    # Create salary table
    salary_data = [[Paragraph('EARNINGS', salary_header_style), '', Paragraph('DEDUCTIONS', salary_header_style), '']]
    
    for i in range(max_rows):
        row = earnings_list[i] + deductions_list[i]
        salary_data.append(row)
    
    # Add totals
    salary_data.append([
        Paragraph('<b>Gross Earnings</b>', salary_style),
        Paragraph(f"<b>₹{payslip['gross_earnings']:,.2f}</b>", salary_style),
        Paragraph('<b>Total Deductions</b>', salary_style),
        Paragraph(f"<b>₹{payslip['total_deductions']:,.2f}</b>", salary_style)
    ])
    
    salary_table = Table(salary_data, colWidths=[2.5*inch, 1.25*inch, 2.5*inch, 1.25*inch])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#34495e')),
        ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#34495e')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 15))
    
    # Net Payable
    net_data = [[
        Paragraph('<b>Total Net Payable</b>', salary_style),
        Paragraph(f"<b>₹{payslip['net_payable']:,.2f}</b>", salary_style)
    ]]
    net_table = Table(net_data, colWidths=[5.5*inch, 2*inch])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#27ae60')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    footer = Paragraph('-- This is a system generated payslip, hence the signature is not required. --', footer_style)
    elements.append(footer)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{employee['employee_no']}_{month_names[payslip['month']]}_{payslip['year']}.pdf"}
    )

# Dashboard Routes
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(username: str = Depends(verify_token)):
    # Count active employees
    active_employees = await db.employees.count_documents({"is_active": True})
    
    # Calculate total monthly payroll
    employees = await db.employees.find({"is_active": True}, {"_id": 0}).to_list(1000)
    total_payroll = 0
    for emp in employees:
        components = emp['salary_components']
        gross = sum([v for k, v in components.items() if k != 'professional_tax'])
        deductions = components.get('professional_tax', 0)
        total_payroll += (gross - deductions)
    
    # Count payslips
    total_payslips = await db.payslips.count_documents({})
    
    return DashboardStats(
        total_active_employees=active_employees,
        total_monthly_payroll=total_payroll,
        total_payslips_generated=total_payslips
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_admin()
    logger.info("Default admin created: username=admin, password=admin123")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
