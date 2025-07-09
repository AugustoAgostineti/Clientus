from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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

# Models
class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClientCreate(BaseModel):
    name: str
    email: str
    password: str

class ClientLogin(BaseModel):
    email: str
    password: str

class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MaterialCreate(BaseModel):
    title: str
    description: str
    type: str
    scheduled_date: datetime
    file_url: Optional[str] = None

class MaterialResponse(BaseModel):
    id: str
    title: str
    description: str
    type: str
    status: str
    scheduled_date: datetime
    file_url: Optional[str] = None
    comments: List[CommentResponse] = []
    approval_history: List[ApprovalHistory] = []
    created_at: datetime

class MaterialUpdate(BaseModel):
    status: str
    comment: Optional[str] = None

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    category: str  # "strategy", "scripts", "briefs", "guidelines", "reports"
    type: str  # "pdf", "doc", "docx", "jpg", "png"
    size: str
    file_url: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class DocumentResponse(BaseModel):
    id: str
    name: str
    category: str
    type: str
    size: str
    file_url: str
    upload_date: datetime

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    status: str  # "active", "paused", "completed"
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    budget: float = 0.0
    spend: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    impressions: int
    clicks: int
    conversions: int
    budget: float
    spend: float
    ctr: float
    cpc: float
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
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
        if client_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    client = await db.clients.find_one({"id": client_id})
    if client is None:
        raise credentials_exception
    return Client(**client)

# Routes
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
        password_hash=get_password_hash(client_data.password)
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
        data={"sub": client["id"]}, expires_delta=access_token_expires
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
            name=campaign["name"],
            status=campaign["status"],
            impressions=campaign["impressions"],
            clicks=campaign["clicks"],
            conversions=campaign["conversions"],
            budget=campaign["budget"],
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
    documents = await db.documents.find({"client_id": current_client.id, "category": category}).to_list(1000)
    return [DocumentResponse(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_client: Client = Depends(get_current_client)):
    document = await db.documents.find_one({"id": document_id, "client_id": current_client.id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"download_url": document["file_url"]}

# Seed data endpoint for demo
@api_router.post("/seed")
async def seed_demo_data():
    # Create demo client
    demo_client = Client(
        name="Demo Client",
        email="demo@take2studio.com",
        password_hash=get_password_hash("demo123")
    )
    
    # Check if demo client already exists
    existing = await db.clients.find_one({"email": demo_client.email})
    if not existing:
        await db.clients.insert_one(demo_client.dict())
    else:
        # Use existing client ID
        demo_client.id = existing["id"]
    
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
            file_url="https://images.unsplash.com/photo-1513530534585-c7b1394c6d51"
        ),
        Material(
            client_id=demo_client.id,
            title="Story Series - Daily Tips",
            description="5-part story series with daily marketing tips for our audience",
            type="story",
            status="planned",
            scheduled_date=datetime(2025, 3, 20, 9, 0, 0)
        ),
        Material(
            client_id=demo_client.id,
            title="Carousel Post - Portfolio Showcase",
            description="Multi-image carousel showcasing recent client work and success stories",
            type="carousel",
            status="published",
            scheduled_date=datetime(2025, 3, 12, 16, 0, 0),
            file_url="https://images.unsplash.com/photo-1651688945265-be97106bb317",
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
            status="active",
            impressions=15420,
            clicks=832,
            conversions=47,
            budget=2500.00,
            spend=1850.75
        ),
        Campaign(
            client_id=demo_client.id,
            name="Brand Awareness Campaign",
            status="active",
            impressions=8750,
            clicks=425,
            conversions=23,
            budget=1500.00,
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
            upload_date=datetime(2025, 1, 1, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Roteiro - Vídeo Institucional",
            category="scripts",
            type="pdf",
            size="1.8 MB",
            file_url="https://example.com/documents/video-script.pdf",
            upload_date=datetime(2025, 1, 15, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Brief - Campanha Primavera",
            category="briefs",
            type="pdf",
            size="3.1 MB",
            file_url="https://example.com/documents/spring-brief.pdf",
            upload_date=datetime(2025, 2, 1, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Manual de Identidade Visual",
            category="guidelines",
            type="pdf",
            size="5.7 MB",
            file_url="https://example.com/documents/brand-guidelines.pdf",
            upload_date=datetime(2025, 1, 10, 0, 0, 0)
        ),
        Document(
            client_id=demo_client.id,
            name="Relatório de Performance - Fevereiro",
            category="reports",
            type="pdf",
            size="2.9 MB",
            file_url="https://example.com/documents/february-report.pdf",
            upload_date=datetime(2025, 3, 1, 0, 0, 0)
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