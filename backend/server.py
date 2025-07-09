from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import bcrypt

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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "take2studio-secret-key-2025"
ALGORITHM = "HS256"

# =================== MODELS ===================

# Client Models (Updated)
class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    contact_person: Optional[str] = None
    project_type: str = "marketing_digital"  # marketing_digital, branding, ecommerce
    status: str = "active"  # active, paused, completed
    visible_metrics: List[str] = ["impressions", "clicks", "ctr", "spend"]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClientCreate(BaseModel):
    name: str
    email: str
    password: str
    contact_person: Optional[str] = None
    project_type: str = "marketing_digital"
    visible_metrics: List[str] = ["impressions", "clicks", "ctr", "spend"]

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    visible_metrics: Optional[List[str]] = None

class ClientLogin(BaseModel):
    email: str
    password: str

class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
    contact_person: Optional[str] = None
    project_type: str
    status: str
    visible_metrics: List[str]
    created_at: datetime

class ClientStatsResponse(BaseModel):
    id: str
    name: str
    status: str
    materials_count: int
    pending_approvals: int
    active_campaigns: int
    current_project: Optional[str] = None

# Admin User Models
class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    role: str = "editor"  # admin, editor, viewer
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "editor"

class AdminLogin(BaseModel):
    email: str
    password: str

class AdminResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

# Material Models (Updated)
class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "unread"  # "read", "unread"

class CommentCreate(BaseModel):
    text: str

class CommentResponse(BaseModel):
    id: str
    text: str
    client_name: str
    timestamp: datetime
    status: str

class ApprovalHistory(BaseModel):
    action: str  # "approved", "revision_requested", "published"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    comment: Optional[str] = None

class Material(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    title: str
    description: str
    type: str  # "photo", "video", "carousel", "story"
    status: str  # "planned", "in_production", "awaiting_approval", "approved", "revision_requested", "published"
    scheduled_date: datetime
    file_url: Optional[str] = None
    comments: List[Comment] = []
    approval_history: List[ApprovalHistory] = []
    tags: List[str] = []
    created_by: Optional[str] = None  # admin user id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MaterialCreate(BaseModel):
    client_id: str
    title: str
    description: str
    type: str
    scheduled_date: datetime
    file_url: Optional[str] = None
    tags: List[str] = []

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    file_url: Optional[str] = None
    tags: Optional[List[str]] = None

class MaterialResponse(BaseModel):
    id: str
    client_id: str
    client_name: Optional[str] = None
    title: str
    description: str
    type: str
    status: str
    scheduled_date: datetime
    file_url: Optional[str] = None
    comments: List[CommentResponse] = []
    approval_history: List[ApprovalHistory] = []
    tags: List[str] = []
    created_at: datetime

# Campaign Models (Updated)
class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    objective: str = "conversions"  # conversions, traffic, awareness, leads
    platform: List[str] = ["meta"]  # meta, google, linkedin, tiktok
    status: str = "active"  # active, paused, completed
    daily_budget: float = 0.0
    total_budget: float = 0.0
    start_date: datetime
    end_date: Optional[datetime] = None
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    created_by: Optional[str] = None  # admin user id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CampaignCreate(BaseModel):
    client_id: str
    name: str
    objective: str = "conversions"
    platform: List[str] = ["meta"]
    daily_budget: float
    total_budget: float
    start_date: datetime
    end_date: Optional[datetime] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    platform: Optional[List[str]] = None
    status: Optional[str] = None
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    spend: Optional[float] = None

class CampaignResponse(BaseModel):
    id: str
    client_id: str
    client_name: Optional[str] = None
    name: str
    objective: str
    platform: List[str]
    status: str
    daily_budget: float
    total_budget: float
    start_date: datetime
    end_date: Optional[datetime] = None
    impressions: int
    clicks: int
    conversions: int
    spend: float
    ctr: float
    cpc: float
    created_at: datetime

# Document Models (Updated)
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    category: str  # "strategy", "scripts", "briefs", "guidelines", "reports"
    type: str  # "pdf", "doc", "docx", "jpg", "png"
    size: str
    file_url: str
    description: Optional[str] = None
    visible_to_client: bool = True
    uploaded_by: Optional[str] = None  # admin user id
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class DocumentCreate(BaseModel):
    client_id: str
    name: str
    category: str
    type: str
    size: str
    file_url: str
    description: Optional[str] = None
    visible_to_client: bool = True

class DocumentResponse(BaseModel):
    id: str
    client_id: str
    client_name: Optional[str] = None
    name: str
    category: str
    type: str
    size: str
    file_url: str
    description: Optional[str] = None
    visible_to_client: bool
    upload_date: datetime

# Dashboard Stats
class DashboardStats(BaseModel):
    total_clients: int
    active_clients: int
    total_materials: int
    pending_materials: int
    pending_approvals: int
    active_campaigns: int
    total_documents: int

class RecentActivity(BaseModel):
    id: str
    type: str  # "material_uploaded", "approval_requested", "campaign_updated"
    description: str
    client_name: str
    timestamp: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# =================== HELPER FUNCTIONS ===================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_client(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")
        user_type: str = payload.get("type", "client")
        if client_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    if user_type == "client":
        client = await db.clients.find_one({"id": client_id})
        if client is None:
            raise credentials_exception
        return Client(**client)
    else:
        raise credentials_exception

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        user_type: str = payload.get("type", "client")
        if admin_id is None or user_type != "admin":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    admin = await db.admin_users.find_one({"id": admin_id})
    if admin is None:
        raise credentials_exception
    return AdminUser(**admin)

# =================== CLIENT ROUTES (EXISTING) ===================

@api_router.post("/auth/register", response_model=ClientResponse)
async def register(client_data: ClientCreate):
    # Check if client already exists
    existing_client = await db.clients.find_one({"email": client_data.email})
    if existing_client:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new client
    client = Client(
        name=client_data.name,
        email=client_data.email,
        password_hash=get_password_hash(client_data.password),
        contact_person=client_data.contact_person,
        project_type=client_data.project_type,
        visible_metrics=client_data.visible_metrics
    )
    
    await db.clients.insert_one(client.dict())
    return ClientResponse(**client.dict())

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: ClientLogin):
    client = await db.clients.find_one({"email": login_data.email})
    if not client or not verify_password(login_data.password, client["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": client["id"], "type": "client"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=ClientResponse)
async def get_current_client_info(current_client: Client = Depends(get_current_client)):
    return ClientResponse(**current_client.dict())

@api_router.get("/materials", response_model=List[MaterialResponse])
async def get_materials(current_client: Client = Depends(get_current_client)):
    materials = await db.materials.find({"client_id": current_client.id}).to_list(1000)
    return [MaterialResponse(**material) for material in materials]

@api_router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str, current_client: Client = Depends(get_current_client)):
    material = await db.materials.find_one({"id": material_id, "client_id": current_client.id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return MaterialResponse(**material)

@api_router.post("/materials", response_model=MaterialResponse)
async def create_material(material_data: MaterialCreate, current_client: Client = Depends(get_current_client)):
    material = Material(
        client_id=current_client.id,
        title=material_data.title,
        description=material_data.description,
        type=material_data.type,
        scheduled_date=material_data.scheduled_date,
        file_url=material_data.file_url,
        status="planned"
    )
    
    await db.materials.insert_one(material.dict())
    return MaterialResponse(**material.dict())

@api_router.post("/materials/{material_id}/approve")
async def approve_material(material_id: str, current_client: Client = Depends(get_current_client)):
    # Find material
    material = await db.materials.find_one({"id": material_id, "client_id": current_client.id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update status and add approval history
    approval_entry = ApprovalHistory(action="approved")
    
    await db.materials.update_one(
        {"id": material_id},
        {
            "$set": {"status": "approved"},
            "$push": {"approval_history": approval_entry.dict()}
        }
    )
    
    return {"message": "Material approved successfully"}

@api_router.post("/materials/{material_id}/request-revision")
async def request_revision(material_id: str, comment_data: CommentCreate, current_client: Client = Depends(get_current_client)):
    # Find material
    material = await db.materials.find_one({"id": material_id, "client_id": current_client.id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Create comment
    comment = Comment(
        text=comment_data.text,
        client_name=current_client.name
    )
    
    # Create approval history entry
    approval_entry = ApprovalHistory(action="revision_requested", comment=comment_data.text)
    
    # Update material
    await db.materials.update_one(
        {"id": material_id},
        {
            "$set": {"status": "revision_requested"},
            "$push": {
                "comments": comment.dict(),
                "approval_history": approval_entry.dict()
            }
        }
    )
    
    return {"message": "Revision request submitted successfully"}

@api_router.get("/materials/{material_id}/comments", response_model=List[CommentResponse])
async def get_material_comments(material_id: str, current_client: Client = Depends(get_current_client)):
    material = await db.materials.find_one({"id": material_id, "client_id": current_client.id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    comments = material.get("comments", [])
    return [CommentResponse(**comment) for comment in comments]

@api_router.post("/materials/{material_id}/comments", response_model=CommentResponse)
async def add_material_comment(material_id: str, comment_data: CommentCreate, current_client: Client = Depends(get_current_client)):
    material = await db.materials.find_one({"id": material_id, "client_id": current_client.id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    comment = Comment(
        text=comment_data.text,
        client_name=current_client.name
    )
    
    await db.materials.update_one(
        {"id": material_id},
        {"$push": {"comments": comment.dict()}}
    )
    
    return CommentResponse(**comment.dict())

@api_router.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(current_client: Client = Depends(get_current_client)):
    campaigns = await db.campaigns.find({"client_id": current_client.id}).to_list(1000)
    
    campaign_responses = []
    for campaign in campaigns:
        ctr = (campaign["clicks"] / campaign["impressions"]) * 100 if campaign["impressions"] > 0 else 0
        cpc = campaign["spend"] / campaign["clicks"] if campaign["clicks"] > 0 else 0
        
        campaign_responses.append(CampaignResponse(
            id=campaign["id"],
            client_id=campaign["client_id"],
            name=campaign["name"],
            objective=campaign.get("objective", "conversions"),
            platform=campaign.get("platform", ["meta"]),
            status=campaign["status"],
            daily_budget=campaign.get("daily_budget", 0.0),
            total_budget=campaign.get("total_budget", 0.0),
            start_date=campaign.get("start_date", campaign["created_at"]),
            end_date=campaign.get("end_date"),
            impressions=campaign["impressions"],
            clicks=campaign["clicks"],
            conversions=campaign["conversions"],
            spend=campaign["spend"],
            ctr=round(ctr, 2),
            cpc=round(cpc, 2),
            created_at=campaign["created_at"]
        ))
    
    return campaign_responses

@api_router.get("/documents/categories")
async def get_document_categories(current_client: Client = Depends(get_current_client)):
    categories = [
        {"id": "strategy", "name": "📋 Posicionamento & Estratégia", "description": "Documentos estratégicos da marca"},
        {"id": "scripts", "name": "🎬 Roteiros de Vídeos", "description": "Scripts e roteiros para conteúdo"},
        {"id": "briefs", "name": "📊 Briefings de Campanhas", "description": "Briefings detalhados das campanhas"},
        {"id": "guidelines", "name": "🎨 Guidelines Visuais", "description": "Manuais de identidade visual"},
        {"id": "reports", "name": "📈 Relatórios", "description": "Relatórios de performance e resultados"}
    ]
    return categories

@api_router.get("/documents/{category}", response_model=List[DocumentResponse])
async def get_documents_by_category(category: str, current_client: Client = Depends(get_current_client)):
    documents = await db.documents.find({"client_id": current_client.id, "category": category, "visible_to_client": True}).to_list(1000)
    return [DocumentResponse(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_client: Client = Depends(get_current_client)):
    document = await db.documents.find_one({"id": document_id, "client_id": current_client.id, "visible_to_client": True})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"download_url": document["file_url"]}

# =================== ADMIN ROUTES (NEW) ===================

@api_router.post("/admin/auth/login", response_model=Token)
async def admin_login(login_data: AdminLogin):
    admin = await db.admin_users.find_one({"email": login_data.email})
    if not admin or not verify_password(login_data.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": admin["id"], "type": "admin"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/admin/auth/me", response_model=AdminResponse)
async def get_current_admin_info(current_admin: AdminUser = Depends(get_current_admin)):
    return AdminResponse(**current_admin.dict())

@api_router.get("/admin/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_admin: AdminUser = Depends(get_current_admin)):
    # Count totals
    total_clients = await db.clients.count_documents({})
    active_clients = await db.clients.count_documents({"status": "active"})
    total_materials = await db.materials.count_documents({})
    pending_materials = await db.materials.count_documents({"status": {"$in": ["planned", "in_production"]}})
    pending_approvals = await db.materials.count_documents({"status": "awaiting_approval"})
    active_campaigns = await db.campaigns.count_documents({"status": "active"})
    total_documents = await db.documents.count_documents({})
    
    return DashboardStats(
        total_clients=total_clients,
        active_clients=active_clients,
        total_materials=total_materials,
        pending_materials=pending_materials,
        pending_approvals=pending_approvals,
        active_campaigns=active_campaigns,
        total_documents=total_documents
    )

@api_router.get("/admin/clients", response_model=List[ClientStatsResponse])
async def get_all_clients(current_admin: AdminUser = Depends(get_current_admin)):
    clients = await db.clients.find({}).to_list(1000)
    
    client_stats = []
    for client in clients:
        # Count materials and approvals for each client
        materials_count = await db.materials.count_documents({"client_id": client["id"]})
        pending_approvals = await db.materials.count_documents({"client_id": client["id"], "status": "awaiting_approval"})
        active_campaigns = await db.campaigns.count_documents({"client_id": client["id"], "status": "active"})
        
        client_stats.append(ClientStatsResponse(
            id=client["id"],
            name=client["name"],
            status=client["status"],
            materials_count=materials_count,
            pending_approvals=pending_approvals,
            active_campaigns=active_campaigns,
            current_project=client.get("project_type", "")
        ))
    
    return client_stats

@api_router.get("/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client_by_id(client_id: str, current_admin: AdminUser = Depends(get_current_admin)):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse(**client)

@api_router.post("/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, current_admin: AdminUser = Depends(get_current_admin)):
    # Check if client already exists
    existing_client = await db.clients.find_one({"email": client_data.email})
    if existing_client:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new client
    client = Client(
        name=client_data.name,
        email=client_data.email,
        password_hash=get_password_hash(client_data.password),
        contact_person=client_data.contact_person,
        project_type=client_data.project_type,
        visible_metrics=client_data.visible_metrics
    )
    
    await db.clients.insert_one(client.dict())
    return ClientResponse(**client.dict())

@api_router.put("/admin/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client_data: ClientUpdate, current_admin: AdminUser = Depends(get_current_admin)):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = {k: v for k, v in client_data.dict().items() if v is not None}
    
    if update_data:
        await db.clients.update_one(
            {"id": client_id},
            {"$set": update_data}
        )
    
    updated_client = await db.clients.find_one({"id": client_id})
    return ClientResponse(**updated_client)

@api_router.delete("/admin/clients/{client_id}")
async def delete_client(client_id: str, current_admin: AdminUser = Depends(get_current_admin)):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Delete related data
    await db.materials.delete_many({"client_id": client_id})
    await db.campaigns.delete_many({"client_id": client_id})
    await db.documents.delete_many({"client_id": client_id})
    await db.clients.delete_one({"id": client_id})
    
    return {"message": "Client and related data deleted successfully"}

@api_router.get("/admin/materials", response_model=List[MaterialResponse])
async def get_all_materials(current_admin: AdminUser = Depends(get_current_admin)):
    materials = await db.materials.find({}).to_list(1000)
    
    # Add client names
    material_responses = []
    for material in materials:
        client = await db.clients.find_one({"id": material["client_id"]})
        material_response = MaterialResponse(**material)
        material_response.client_name = client["name"] if client else "Unknown Client"
        material_responses.append(material_response)
    
    return material_responses

@api_router.post("/admin/materials", response_model=MaterialResponse)
async def create_material_admin(material_data: MaterialCreate, current_admin: AdminUser = Depends(get_current_admin)):
    # Verify client exists
    client = await db.clients.find_one({"id": material_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    material = Material(
        client_id=material_data.client_id,
        title=material_data.title,
        description=material_data.description,
        type=material_data.type,
        scheduled_date=material_data.scheduled_date,
        file_url=material_data.file_url,
        tags=material_data.tags,
        status="planned",
        created_by=current_admin.id
    )
    
    await db.materials.insert_one(material.dict())
    material_response = MaterialResponse(**material.dict())
    material_response.client_name = client["name"]
    return material_response

@api_router.put("/admin/materials/{material_id}", response_model=MaterialResponse)
async def update_material(material_id: str, material_data: MaterialUpdate, current_admin: AdminUser = Depends(get_current_admin)):
    material = await db.materials.find_one({"id": material_id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    update_data = {k: v for k, v in material_data.dict().items() if v is not None}
    
    if update_data:
        await db.materials.update_one(
            {"id": material_id},
            {"$set": update_data}
        )
    
    updated_material = await db.materials.find_one({"id": material_id})
    client = await db.clients.find_one({"id": updated_material["client_id"]})
    
    material_response = MaterialResponse(**updated_material)
    material_response.client_name = client["name"] if client else "Unknown Client"
    return material_response

@api_router.get("/admin/campaigns", response_model=List[CampaignResponse])
async def get_all_campaigns(current_admin: AdminUser = Depends(get_current_admin)):
    campaigns = await db.campaigns.find({}).to_list(1000)
    
    campaign_responses = []
    for campaign in campaigns:
        client = await db.clients.find_one({"id": campaign["client_id"]})
        ctr = (campaign["clicks"] / campaign["impressions"]) * 100 if campaign["impressions"] > 0 else 0
        cpc = campaign["spend"] / campaign["clicks"] if campaign["clicks"] > 0 else 0
        
        campaign_response = CampaignResponse(
            id=campaign["id"],
            client_id=campaign["client_id"],
            client_name=client["name"] if client else "Unknown Client",
            name=campaign["name"],
            objective=campaign.get("objective", "conversions"),
            platform=campaign.get("platform", ["meta"]),
            status=campaign["status"],
            daily_budget=campaign.get("daily_budget", 0.0),
            total_budget=campaign.get("total_budget", 0.0),
            start_date=campaign.get("start_date", campaign["created_at"]),
            end_date=campaign.get("end_date"),
            impressions=campaign["impressions"],
            clicks=campaign["clicks"],
            conversions=campaign["conversions"],
            spend=campaign["spend"],
            ctr=round(ctr, 2),
            cpc=round(cpc, 2),
            created_at=campaign["created_at"]
        )
        campaign_responses.append(campaign_response)
    
    return campaign_responses

@api_router.post("/admin/campaigns", response_model=CampaignResponse)
async def create_campaign_admin(campaign_data: CampaignCreate, current_admin: AdminUser = Depends(get_current_admin)):
    # Verify client exists
    client = await db.clients.find_one({"id": campaign_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    campaign = Campaign(
        client_id=campaign_data.client_id,
        name=campaign_data.name,
        objective=campaign_data.objective,
        platform=campaign_data.platform,
        daily_budget=campaign_data.daily_budget,
        total_budget=campaign_data.total_budget,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        status="active",
        created_by=current_admin.id
    )
    
    await db.campaigns.insert_one(campaign.dict())
    
    # Return campaign with client name
    ctr = 0.0
    cpc = 0.0
    campaign_response = CampaignResponse(
        id=campaign.id,
        client_id=campaign.client_id,
        client_name=client["name"],
        name=campaign.name,
        objective=campaign.objective,
        platform=campaign.platform,
        status=campaign.status,
        daily_budget=campaign.daily_budget,
        total_budget=campaign.total_budget,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        impressions=0,
        clicks=0,
        conversions=0,
        spend=0.0,
        ctr=ctr,
        cpc=cpc,
        created_at=campaign.created_at
    )
    
    return campaign_response

@api_router.get("/admin/documents", response_model=List[DocumentResponse])
async def get_all_documents(current_admin: AdminUser = Depends(get_current_admin)):
    documents = await db.documents.find({}).to_list(1000)
    
    # Add client names
    document_responses = []
    for document in documents:
        client = await db.clients.find_one({"id": document["client_id"]})
        document_response = DocumentResponse(**document)
        document_response.client_name = client["name"] if client else "Unknown Client"
        document_responses.append(document_response)
    
    return document_responses

@api_router.post("/admin/documents", response_model=DocumentResponse)
async def create_document_admin(document_data: DocumentCreate, current_admin: AdminUser = Depends(get_current_admin)):
    # Verify client exists
    client = await db.clients.find_one({"id": document_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    document = Document(
        client_id=document_data.client_id,
        name=document_data.name,
        category=document_data.category,
        type=document_data.type,
        size=document_data.size,
        file_url=document_data.file_url,
        description=document_data.description,
        visible_to_client=document_data.visible_to_client,
        uploaded_by=current_admin.id
    )
    
    await db.documents.insert_one(document.dict())
    document_response = DocumentResponse(**document.dict())
    document_response.client_name = client["name"]
    return document_response

# Seed data endpoint for demo
@api_router.post("/seed")
async def seed_demo_data():
    # Create demo client
    demo_client = Client(
        name="Demo Client",
        email="demo@take2studio.com",
        password_hash=get_password_hash("demo123"),
        contact_person="João Silva",
        project_type="marketing_digital",
        status="active",
        visible_metrics=["impressions", "clicks", "ctr", "spend", "conversions"]
    )
    
    # Check if demo client already exists
    existing = await db.clients.find_one({"email": demo_client.email})
    if not existing:
        await db.clients.insert_one(demo_client.dict())
    else:
        # Use existing client ID
        demo_client.id = existing["id"]
    
    # Create admin users
    admin_users = [
        AdminUser(
            name="Administrador Take 2",
            email="admin@take2studio.com",
            password_hash=get_password_hash("admin123"),
            role="admin"
        ),
        AdminUser(
            name="Editor Take 2",
            email="editor@take2studio.com",
            password_hash=get_password_hash("editor123"),
            role="editor"
        )
    ]
    
    for admin in admin_users:
        existing_admin = await db.admin_users.find_one({"email": admin.email})
        if not existing_admin:
            await db.admin_users.insert_one(admin.dict())
    
    # Create additional demo clients
    additional_clients = [
        Client(
            name="Empresa Tech Inovadora",
            email="tech@example.com",
            password_hash=get_password_hash("tech123"),
            contact_person="Maria Santos",
            project_type="marketing_digital",
            status="active"
        ),
        Client(
            name="Boutique Fashion Brand",
            email="fashion@example.com", 
            password_hash=get_password_hash("fashion123"),
            contact_person="Ana Costa",
            project_type="branding",
            status="active"
        ),
        Client(
            name="E-commerce Startup",
            email="ecom@example.com",
            password_hash=get_password_hash("ecom123"),
            contact_person="Pedro Lima",
            project_type="ecommerce",
            status="paused"
        )
    ]
    
    for client in additional_clients:
        existing_client = await db.clients.find_one({"email": client.email})
        if not existing_client:
            await db.clients.insert_one(client.dict())
    
    # Create demo materials with expanded status and comments
    demo_materials = [
        Material(
            client_id=demo_client.id,
            title="Instagram Post - New Product Launch",
            description="Exciting announcement about our latest product line with engaging visuals and compelling copy",
            type="photo",
            status="awaiting_approval",
            scheduled_date=datetime(2025, 3, 15, 10, 0, 0),
            file_url="https://images.unsplash.com/photo-1611162618071-b39a2ec055fb",
            tags=["product", "launch", "instagram"],
            comments=[
                Comment(
                    text="This looks great! Could we try a different background color to make it more vibrant?",
                    client_name="Demo Client",
                    timestamp=datetime.utcnow() - timedelta(hours=2)
                ).dict()
            ],
            approval_history=[
                ApprovalHistory(
                    action="revision_requested",
                    timestamp=datetime.utcnow() - timedelta(hours=2),
                    comment="Background color change requested"
                ).dict()
            ]
        ),
        Material(
            client_id=demo_client.id,
            title="Facebook Video - Behind the Scenes",
            description="Behind the scenes footage of our production process showcasing our team at work",
            type="video",
            status="in_production",
            scheduled_date=datetime(2025, 3, 18, 14, 0, 0),
            file_url="https://images.unsplash.com/photo-1513530534585-c7b1394c6d51",
            tags=["bts", "video", "facebook"]
        ),
        Material(
            client_id=demo_client.id,
            title="Story Series - Daily Tips",
            description="5-part story series with daily marketing tips for our audience",
            type="story",
            status="planned",
            scheduled_date=datetime(2025, 3, 20, 9, 0, 0),
            tags=["tips", "stories", "series"]
        ),
        Material(
            client_id=demo_client.id,
            title="Carousel Post - Portfolio Showcase",
            description="Multi-image carousel showcasing recent client work and success stories",
            type="carousel",
            status="published",
            scheduled_date=datetime(2025, 3, 12, 16, 0, 0),
            file_url="https://images.unsplash.com/photo-1651688945265-be97106bb317",
            tags=["portfolio", "carousel", "showcase"],
            approval_history=[
                ApprovalHistory(
                    action="approved",
                    timestamp=datetime.utcnow() - timedelta(days=1)
                ).dict(),
                ApprovalHistory(
                    action="published",
                    timestamp=datetime.utcnow() - timedelta(hours=6)
                ).dict()
            ]
        ),
        Material(
            client_id=demo_client.id,
            title="LinkedIn Article - Industry Insights",
            description="Professional article about latest industry trends and insights",
            type="photo",
            status="approved",
            scheduled_date=datetime(2025, 3, 22, 11, 0, 0),
            file_url="https://images.unsplash.com/photo-1516321318423-f06f85e504b3",
            tags=["linkedin", "article", "industry"],
            approval_history=[
                ApprovalHistory(
                    action="approved",
                    timestamp=datetime.utcnow() - timedelta(hours=12)
                ).dict()
            ]
        ),
        Material(
            client_id=demo_client.id,
            title="TikTok Video - Trending Challenge",
            description="Creative video following the latest TikTok trend to increase engagement",
            type="video",
            status="revision_requested",
            scheduled_date=datetime(2025, 3, 25, 15, 0, 0),
            file_url="https://images.unsplash.com/photo-1598300042247-d088f8ab3a91",
            tags=["tiktok", "trend", "challenge"],
            comments=[
                Comment(
                    text="The concept is great, but could we make the opening more dynamic? Maybe add some text overlays?",
                    client_name="Demo Client",
                    timestamp=datetime.utcnow() - timedelta(hours=4)
                ).dict()
            ],
            approval_history=[
                ApprovalHistory(
                    action="revision_requested",
                    timestamp=datetime.utcnow() - timedelta(hours=4),
                    comment="Opening needs to be more dynamic"
                ).dict()
            ]
        )
    ]
    
    # Insert demo materials
    for material in demo_materials:
        existing_material = await db.materials.find_one({"id": material.id})
        if not existing_material:
            await db.materials.insert_one(material.dict())
    
    # Create demo campaigns
    demo_campaigns = [
        Campaign(
            client_id=demo_client.id,
            name="Spring Product Launch",
            objective="conversions",
            platform=["meta", "google"],
            status="active",
            daily_budget=100.0,
            total_budget=2500.0,
            start_date=datetime.utcnow() - timedelta(days=10),
            impressions=15420,
            clicks=832,
            conversions=47,
            spend=1850.75
        ),
        Campaign(
            client_id=demo_client.id,
            name="Brand Awareness Campaign",
            objective="awareness",
            platform=["meta"],
            status="active",
            daily_budget=75.0,
            total_budget=1500.0,
            start_date=datetime.utcnow() - timedelta(days=5),
            impressions=8750,
            clicks=425,
            conversions=23,
            spend=1125.50
        )
    ]
    
    # Insert demo campaigns
    for campaign in demo_campaigns:
        existing_campaign = await db.campaigns.find_one({"id": campaign.id})
        if not existing_campaign:
            await db.campaigns.insert_one(campaign.dict())
    
    # Create demo documents
    demo_documents = [
        Document(
            client_id=demo_client.id,
            name="Posicionamento da Marca - Janeiro 2025",
            category="strategy",
            type="pdf",
            size="2.3 MB",
            file_url="https://example.com/documents/positioning.pdf",
            description="Documento estratégico com posicionamento da marca para 2025",
            visible_to_client=True,
            upload_date=datetime(2025, 1, 1, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Roteiro - Vídeo Institucional",
            category="scripts",
            type="pdf",
            size="1.8 MB",
            file_url="https://example.com/documents/video-script.pdf",
            description="Roteiro completo para vídeo institucional",
            visible_to_client=True,
            upload_date=datetime(2025, 1, 15, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Brief - Campanha Primavera",
            category="briefs",
            type="pdf",
            size="3.1 MB",
            file_url="https://example.com/documents/spring-brief.pdf",
            description="Brief detalhado da campanha de primavera",
            visible_to_client=True,
            upload_date=datetime(2025, 2, 1, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Manual de Identidade Visual",
            category="guidelines",
            type="pdf",
            size="5.7 MB",
            file_url="https://example.com/documents/brand-guidelines.pdf",
            description="Manual completo de identidade visual",
            visible_to_client=True,
            upload_date=datetime(2025, 1, 10, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Relatório de Performance - Fevereiro",
            category="reports",
            type="pdf",
            size="2.9 MB",
            file_url="https://example.com/documents/february-report.pdf",
            description="Relatório mensal de performance das campanhas",
            visible_to_client=True,
            upload_date=datetime(2025, 3, 1, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Estratégia Interna - Q1 2025",
            category="strategy",
            type="pdf",
            size="1.5 MB",
            file_url="https://example.com/documents/internal-strategy.pdf",
            description="Estratégia interna para o primeiro trimestre",
            visible_to_client=False,
            upload_date=datetime(2025, 1, 5, 0, 0, 0)
        )
    ]
    
    # Insert demo documents
    for doc in demo_documents:
        existing_doc = await db.documents.find_one({"id": doc.id})
        if not existing_doc:
            await db.documents.insert_one(doc.dict())
    
    return {"message": "Demo data seeded successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()