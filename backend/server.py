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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Number to words converter for Indian currency
def number_to_words_indian(num):
    """Convert number to words in Indian English format"""
    if num == 0:
        return "Zero"
    
    def convert_less_than_thousand(n):
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        
        if n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        else:
            return ones[n // 100] + " Hundred" + (" " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")
    
    # Split into integer and decimal parts
    rupees = int(num)
    paise = round((num - rupees) * 100)
    
    result = []
    
    if rupees == 0:
        result.append("Zero Rupees")
    else:
        # Indian numbering system: crores, lakhs, thousands, hundreds
        crores = rupees // 10000000
        lakhs = (rupees % 10000000) // 100000
        thousands = (rupees % 100000) // 1000
        hundreds = rupees % 1000
        
        if crores > 0:
            result.append(convert_less_than_thousand(crores) + " Crore")
        if lakhs > 0:
            result.append(convert_less_than_thousand(lakhs) + " Lakh")
        if thousands > 0:
            result.append(convert_less_than_thousand(thousands) + " Thousand")
        if hundreds > 0:
            result.append(convert_less_than_thousand(hundreds))
        
        result.append("Rupees")
    
    if paise > 0:
        result.append("and " + convert_less_than_thousand(paise) + " Paise")
    
    result.append("Only")
    
    return " ".join(result)

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
    home_collection_visit: Optional[float] = 0
    custom_deduction_name: Optional[str] = None
    custom_deduction_amount: Optional[float] = 0

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
        promotion_data.new_salary_components.fixed_allowance
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
    
    # Add Home Collection - Visit if provided (monthly variable component)
    if payslip_data.home_collection_visit and payslip_data.home_collection_visit > 0:
        earnings['Home Collection - Visit'] = payslip_data.home_collection_visit
    
    gross_earnings = sum(earnings.values())
    
    # Calculate deductions (only non-zero components)
    deductions = {}
    if components.get('professional_tax', 0) > 0:
        deductions['Professional Tax'] = components['professional_tax']
    
    # Add custom deduction if provided (monthly variable component)
    if payslip_data.custom_deduction_name and payslip_data.custom_deduction_amount and payslip_data.custom_deduction_amount > 0:
        deductions[payslip_data.custom_deduction_name] = payslip_data.custom_deduction_amount
    
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

@api_router.delete("/payslips/{payslip_id}")
async def delete_payslip(payslip_id: str, username: str = Depends(verify_token)):
    payslip = await db.payslips.find_one({"id": payslip_id})
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    await db.payslips.delete_one({"id": payslip_id})
    return {"message": "Payslip deleted successfully"}

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
    
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # TABLE 1: Company Header + Employee Summary
    # Row 1: Company Name, Address and Logo in same cell
    company_style = ParagraphStyle('Company', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', alignment=TA_LEFT)
    
    # Load and resize logo
    logo_path = Path(__file__).parent / 'logo.png'
    logo = Image(str(logo_path), width=1.753*inch, height=0.69*inch)
    
    # Create a table within the cell to position text left and logo right
    company_info_text = Paragraph(
        'PRIMECURE PATHLABS PRIVATE LIMITED<br/>'
        '<font size=8 color="grey">131, Rhydham Plaza, Amar Jawan Circle, Nikol,<br/>'
        'Ahmedabad, Gujarat 382350 India</font>',
        company_style
    )
    
    # Inner table for company header with text on left and logo on right
    # Adjusted column widths to accommodate larger logo
    company_header_data = [[company_info_text, logo]]
    company_header_table = Table(company_header_data, colWidths=[5.8*inch, 1.5*inch])
    company_header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('RIGHTPADDING', (1, 0), (1, 0), 10),  # Add padding to keep logo within bounds
    ]))
    
    # Row 2: Employee Summary Header - REMOVED
    
    # Employee Details (left aligned and right aligned)
    detail_style = ParagraphStyle('Detail', parent=styles['Normal'], fontSize=9, leading=14)
    
    left_details = Paragraph(
        f"<b>Employee Name:</b> {employee['name']}<br/>"
        f"<b>Designation:</b> {employee['designation']}<br/>"
        f"<b>Date of Joining:</b> {employee['date_of_joining']}<br/>"
        f"<b>Paid Days:</b> {payslip['paid_days']}<br/>"
        f"<b>Work Location:</b> {employee['work_location']}",
        detail_style
    )
    
    right_details = Paragraph(
        f"<b>Employee No:</b> {employee['employee_no']}<br/>"
        f"<b>Department:</b> {employee['department']}<br/>"
        f"<b>Bank Account No:</b> {employee['bank_account_no']}<br/>"
        f"<b>LOP Days:</b> {payslip['lop_days']}",
        detail_style
    )
    
    # Build Table 1
    table1_data = [
        [company_header_table],
        [left_details, right_details]
    ]
    
    table1 = Table(table1_data, colWidths=[4.5*inch, 3*inch])
    table1.setStyle(TableStyle([
        # Row 1: Company header with logo in same cell
        ('SPAN', (0, 0), (1, 0)),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, 0), 0.5, colors.grey),
        
        # Row 2: Employee details (previously row 3)
        ('ALIGN', (0, 1), (0, 1), 'LEFT'),
        ('ALIGN', (1, 1), (1, 1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, 1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('LEFTPADDING', (0, 1), (-1, 1), 10),
        ('GRID', (0, 1), (-1, 1), 0.5, colors.grey),
    ]))
    
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Payslip for the month of {month_names[payslip['month']]} {payslip['year']}</b>", 
                              ParagraphStyle('MonthTitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5))
    elements.append(table1)
    elements.append(Spacer(1, 15))
    
    # TABLE 2: Earnings and Deductions
    salary_style = ParagraphStyle('Salary', parent=styles['Normal'], fontSize=9)
    salary_header_style = ParagraphStyle('SalaryHeader', parent=styles['Normal'], fontSize=10, textColor=colors.black, fontName='Helvetica-Bold', alignment=TA_CENTER)
    amount_header_style = ParagraphStyle('AmountHeader', parent=styles['Normal'], fontSize=9, textColor=colors.black, alignment=TA_CENTER, fontName='Helvetica-Bold')
    summary_title_style = ParagraphStyle('SummaryTitle', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.black)
    
    # Build earnings and deductions rows (without rupee symbol in front)
    earnings_list = [[Paragraph(k, salary_style), Paragraph(f"{v:,.2f}", ParagraphStyle('Amount', parent=salary_style, alignment=TA_RIGHT))] for k, v in payslip['earnings'].items()]
    deductions_list = [[Paragraph(k, salary_style), Paragraph(f"{v:,.2f}", ParagraphStyle('Amount', parent=salary_style, alignment=TA_RIGHT))] for k, v in payslip['deductions'].items()]
    
    # Make both lists the same length
    max_rows = max(len(earnings_list), len(deductions_list))
    while len(earnings_list) < max_rows:
        earnings_list.append(['', ''])
    while len(deductions_list) < max_rows:
        deductions_list.append(['', ''])
    
    # Create salary table with EMPLOYEE PAY SUMMARY header row and column headers
    salary_data = [
        [Paragraph('EMPLOYEE PAY SUMMARY', summary_title_style), '', '', ''],
        [Paragraph('EARNINGS', salary_header_style), Paragraph('AMOUNT', amount_header_style), 
         Paragraph('DEDUCTIONS', salary_header_style), Paragraph('AMOUNT', amount_header_style)]
    ]
    
    for i in range(max_rows):
        row = earnings_list[i] + deductions_list[i]
        salary_data.append(row)
    
    # Add totals
    salary_data.append([
        Paragraph('<b>Gross Earnings</b>', salary_style),
        Paragraph(f"<b>{payslip['gross_earnings']:,.2f}</b>", ParagraphStyle('TotalAmount', parent=salary_style, alignment=TA_RIGHT, fontName='Helvetica-Bold')),
        Paragraph('<b>Total Deductions</b>', salary_style),
        Paragraph(f"<b>{payslip['total_deductions']:,.2f}</b>", ParagraphStyle('TotalAmount', parent=salary_style, alignment=TA_RIGHT, fontName='Helvetica-Bold'))
    ])
    
    salary_table = Table(salary_data, colWidths=[2.5*inch, 1.25*inch, 2.5*inch, 1.25*inch])
    salary_table.setStyle(TableStyle([
        # Title row styling (EMPLOYEE PAY SUMMARY)
        ('SPAN', (0, 0), (3, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Header row styling (EARNINGS/DEDUCTIONS)
        ('BACKGROUND', (0, 1), (1, 1), colors.HexColor('#d3d3d3')),
        ('BACKGROUND', (2, 1), (3, 1), colors.HexColor('#d3d3d3')),
        ('ALIGN', (1, 1), (1, 1), 'CENTER'),
        ('ALIGN', (3, 1), (3, 1), 'CENTER'),
        
        # All cells
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Amount columns alignment
        ('ALIGN', (1, 2), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 2), (3, -1), 'RIGHT'),
        
        # Total row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 15))
    
    # Net Payable
    net_amount_words = number_to_words_indian(payslip['net_payable'])
    
    # Combine numeric amount and words in the same cell
    net_amount_with_words = Paragraph(
        f"<b>{payslip['net_payable']:,.2f}</b><br/>"
        f"<font size=8 color='grey'><i>({net_amount_words})</i></font>",
        ParagraphStyle('NetAmount', parent=salary_style, alignment=TA_RIGHT, fontName='Helvetica-Bold')
    )
    
    net_data = [[
        Paragraph('<b>Total Net Payable</b>', salary_style),
        net_amount_with_words
    ]]
    net_table = Table(net_data, colWidths=[1.5*inch, 6*inch])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d3d3d3')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
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
