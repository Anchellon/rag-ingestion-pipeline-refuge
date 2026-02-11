# src/metadata/schema.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime



class ContactInfo(BaseModel):
    """Contact information - only extracted if service NOT in database"""
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class Location(BaseModel):
    """Location information - only extracted if service NOT in database"""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    neighborhood: Optional[str] = None

class ServiceDetails(BaseModel):
    """Service details - only extracted if service NOT in database"""
    hours: Optional[Dict] = None
    capacity: Optional[str] = None
    eligibility: Optional[str] = None
    cost: Optional[str] = None
    languages: Optional[List[str]] = None
    accessibility: Optional[str] = None

class ExtractedMetadata(BaseModel):
    """Metadata extracted from document content by LLM"""
    
    # === PRIMARY STRATEGY: Link to Database ===
    related_service_id: Optional[int] = Field(
        None, 
        description="ID of service in PostgreSQL if match found"
    )
    related_resource_id: Optional[int] = Field(
        None, 
        description="ID of organization in PostgreSQL if match found"
    )
    
    # === FALLBACK: If can't link, track mentions ===
    mentioned_services: Optional[List[str]] = Field(
        None,
        description="Service names mentioned in text (if not in DB)"
    )
    mentioned_organizations: Optional[List[str]] = Field(
        None,
        description="Organization names mentioned in text (if not in DB)"
    )
    mentioned_locations: Optional[List[str]] = Field(
        None,
        description="Locations mentioned in text"
    )
    
    # === DENORMALIZED FILTERS (always extract for fast filtering) ===
    service_type: Optional[str] = Field(
        None,
        description="Category: food, housing, healthcare, legal, education, employment, general, other"
    )
    city: Optional[str] = Field(
        None,
        description="Primary city mentioned"
    )
    neighborhood: Optional[str] = Field(
        None,
        description="Neighborhood if mentioned"
    )
    
    # === EXTRACTED DETAILS (only if service NOT in database) ===
    # These are None if related_service_id exists (get from DB instead)
    contact: Optional[ContactInfo] = Field(
        None,
        description="Extract only if service not in database"
    )
    location: Optional[Location] = Field(
        None,
        description="Extract only if service not in database"
    )
    service_details: Optional[ServiceDetails] = Field(
        None,
        description="Extract only if service not in database"
    )
    
    # === FOR GENERAL DOCUMENTS (when related_service_id is None) ===
    topic: Optional[str] = Field(
        None,
        description="Main topic for general documents (e.g., food_stamps, tenant_rights, application_process)"
    )
    content_category: Optional[str] = Field(
        None,
        description="Type of content: how_to, guide, policy, educational, announcement"
    )
    
    # === OPTIONAL METADATA ===
    publication_date: Optional[str] = Field(
        None,
        description="Publication date if mentioned in document"
    )
    publisher: Optional[str] = Field(
        None,
        description="Publishing organization for general documents"
    )

class ChunkMetadata(BaseModel):
    """Complete metadata for a document chunk stored in ChromaDB"""
    
    # === Source Information ===
    source_filename: str
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    
    # === Processing Information ===
    extracted_date: datetime = Field(default_factory=lambda: datetime.now())
    pipeline_version: str = "1.0.0"
    
    # === Document Classification ===
    document_type: str = Field(
        "unknown",
        description="brochure, guide, policy, flyer, announcement, report"
    )
    source_type: str = Field(
        "brochure",
        description="brochure, general_guide, policy_document, service_info"
    )
    
    # === Extracted Metadata ===
    extracted: ExtractedMetadata = Field(default_factory=ExtractedMetadata)
    
    # === Chunk Information ===
    chunk_index: int
    token_count: int
    
    # === Additional Fields ===
    keywords: Optional[List[str]] = None
    language: str = "en"
    
    # === Quality Flags ===
    needs_review: bool = Field(
        False,
        description="Flag for chunks that mention services not in database"
    )


# Schema File Explanation

# Purpose of This File
# Defines the data structure for:

# What metadata to extract from PDFs
# How to store it in ChromaDB
# How to link PDFs to your PostgreSQL database


# File Structure Overview
# schema.py
# │
# ├─ ContactInfo (helper)
# ├─ Location (helper)
# ├─ ServiceDetails (helper)
# │
# ├─ ExtractedMetadata (what LLM extracts)
# │
# └─ ChunkMetadata (what gets stored in ChromaDB)

# 1. Helper Models (ContactInfo, Location, ServiceDetails)
# Purpose: Organize related fields
# pythonclass ContactInfo(BaseModel):
#     phone: Optional[str] = None
#     email: Optional[str] = None
#     website: Optional[str] = None
# Why separate? Instead of:
# pythoncontact_phone: Optional[str]
# contact_email: Optional[str]
# contact_website: Optional[str]
# You get:
# pythoncontact: ContactInfo
# # Access: contact.phone, contact.email
# Cleaner, organized.

# 2. ExtractedMetadata (Core Extraction Logic)
# This is what the LLM extracts from each PDF chunk.
# Strategy Breakdown:
# Tier 1: Try to Link First (Primary)
# pythonrelated_service_id: Optional[int]
# related_resource_id: Optional[int]
# Logic:

# LLM reads chunk: "Soup Kitchen A at 123 Main St..."
# Searches PostgreSQL: Is "Soup Kitchen A" in database?
# If YES: related_service_id = 123, DONE
# If NO: Move to Tier 2


# Tier 2: Track Mentions (Fallback)
# pythonmentioned_services: Optional[List[str]]
# mentioned_organizations: Optional[List[str]]
# mentioned_locations: Optional[List[str]]
# Logic:

# Can't find in database
# But chunk mentions: "Oakland Food Bank"
# Store: mentioned_organizations = ["Oakland Food Bank"]
# Later: Admin can add to database and link


# Tier 3: Always Extract for Filtering
# pythonservice_type: Optional[str]  # "food", "housing"
# city: Optional[str]
# neighborhood: Optional[str]
# Why always?

# Enables fast ChromaDB filtering
# Don't need to query PostgreSQL to filter by city

# Example:
# python# Can filter without touching PostgreSQL
# search(filter={"city": "San Francisco", "service_type": "food"})

# Tier 4: Extract Details (Conditional)
# pythoncontact: Optional[ContactInfo]
# location: Optional[Location]
# service_details: Optional[ServiceDetails]
# Logic:

# IF related_service_id exists → Leave these as None

# Why? Get from PostgreSQL instead


# IF related_service_id is None → Extract these

# Why? Service not in database, capture what we can



# Example:
# Service EXISTS in DB:
# python{
#     related_service_id: 123,
#     contact: None,  # Don't extract, get from PostgreSQL
#     location: None  # Don't extract, get from PostgreSQL
# }
# Service NOT in DB:
# python{
#     related_service_id: None,
#     contact: {phone: "510-555-1234"},  # Extract it
#     location: {address: "456 Oak St"}  # Extract it
# }

# Tier 5: General Document Fields
# pythontopic: Optional[str]
# content_category: Optional[str]
# For PDFs that aren't about services:
# python{
#     related_service_id: None,
#     topic: "food_stamps",
#     content_category: "how_to"
# }

# 3. ChunkMetadata (What Actually Gets Stored)
# This wraps everything together for storage in ChromaDB.
# Contains:
# Source Info (where did this come from?)
# pythonsource_filename: str  # "guide.pdf"
# source_url: Optional[str]  # If downloaded from web
# page_number: Optional[int]  # Page 5

# Processing Info (when/how was it processed?)
# pythonextracted_date: datetime  # When ingested
# pipeline_version: str  # "1.0.0" (for schema versioning)
# Why version? If you change schema later:

# Old chunks: pipeline_version = "1.0.0"
# New chunks: pipeline_version = "2.0.0"
# Your code handles both versions


# Document Classification (what type of document?)
# pythondocument_type: str  # "brochure", "guide", "policy"
# source_type: str  # "service_info", "general_guide"
# Helps filtering:
# python# Only search official brochures
# search(filter={"document_type": "brochure"})

# The Extracted Data
# pythonextracted: ExtractedMetadata
# This holds everything the LLM extracted.
# Access like:
# pythonchunk.metadata.extracted.related_service_id
# chunk.metadata.extracted.city
# chunk.metadata.extracted.contact.phone

# Chunk Info (technical details)
# pythonchunk_index: int  # 0, 1, 2... (position in document)
# token_count: int  # Size of chunk

# Quality Flags
# pythonneeds_review: bool
# ```

# **Use case:**
# - Chunk mentions organization not in database
# - Set `needs_review = True`
# - Admin dashboard shows these for review
# - Admin adds to database, updates metadata

# ---

# ## How These Models Work Together

# ### During Ingestion:
# ```
# 1. Load PDF
#    ↓
# 2. Split into chunks
#    ↓
# 3. For each chunk:
   
#    LLM extracts → ExtractedMetadata
#    {
#        related_service_id: 123,
#        service_type: "food",
#        city: "San Francisco",
#        contact: None  # In DB
#    }
   
#    ↓
   
#    Wrap in ChunkMetadata
#    {
#        source_filename: "guide.pdf",
#        page_number: 5,
#        chunk_index: 12,
#        token_count: 450,
#        extracted: {above ExtractedMetadata}
#    }
   
#    ↓
   
#    Store in ChromaDB
# ```

# ---

# ### During Querying:
# ```
# User: "Food services in SF"
#    ↓
# ChromaDB filters:
#    filter = {
#        "extracted.service_type": "food",
#        "extracted.city": "San Francisco"
#    }
#    ↓
# Returns chunks
#    ↓
# For each chunk:
#    - If related_service_id exists → Fetch from PostgreSQL
#    - If not → Use extracted.contact, extracted.location

# Key Design Decisions Explained
# 1. Optional Everything
# pythonOptional[str] = None
# Why? PDFs are messy. Sometimes info missing.

# 2. Nested Models
# pythoncontact: Optional[ContactInfo]
# Why? Organization. Instead of flat fields.

# 3. Conditional Extraction
# python# Extract contact ONLY if not in database
# contact: Optional[ContactInfo]
# Why? Avoid duplicating PostgreSQL.

# 4. Denormalized Filters
# pythoncity: Optional[str]  # Even though might be in PostgreSQL
# Why? Fast filtering in ChromaDB without PostgreSQL lookup.

# 5. Versioning
# pythonpipeline_version: str = "1.0.0"
# Why? Schema will change. Track which version each chunk uses.

# Usage Examples
# Example 1: Service-Specific PDF (In Database)
# pythonchunk_metadata = ChunkMetadata(
#     source_filename="soup_kitchen_brochure.pdf",
#     page_number=1,
#     chunk_index=0,
#     token_count=450,
#     document_type="brochure",
#     extracted=ExtractedMetadata(
#         related_service_id=123,  # Found in DB
#         service_type="food",
#         city="San Francisco",
#         contact=None,  # Get from PostgreSQL
#         location=None  # Get from PostgreSQL
#     )
# )

# Example 2: Service-Specific PDF (NOT in Database)
# pythonchunk_metadata = ChunkMetadata(
#     source_filename="oakland_food_bank.pdf",
#     page_number=2,
#     chunk_index=5,
#     token_count=380,
#     document_type="brochure",
#     needs_review=True,  # Flag for admin
#     extracted=ExtractedMetadata(
#         related_service_id=None,  # Not found
#         mentioned_organizations=["Oakland Food Bank"],
#         service_type="food",
#         city="Oakland",
#         contact=ContactInfo(phone="510-555-1234"),  # Extracted
#         location=Location(address="456 Broadway")   # Extracted
#     )
# )

# Example 3: General Guide
# pythonchunk_metadata = ChunkMetadata(
#     source_filename="food_stamps_guide.pdf",
#     page_number=3,
#     chunk_index=8,
#     token_count=520,
#     document_type="guide",
#     source_type="general_guide",
#     extracted=ExtractedMetadata(
#         related_service_id=None,
#         topic="food_stamps",
#         content_category="how_to",
#         publisher="California DHHS"
#     )
# )

# Summary
# This schema:

# Tries to link to PostgreSQL first
# Falls back to extraction if can't link
# Always extracts filters (city, type)
# Tracks what needs review
# Versions itself for future changes

# It's flexible enough to handle:

# Service PDFs (in DB or not)
# General guides
# Policy documents
# Announcements