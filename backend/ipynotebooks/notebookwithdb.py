import sys, os
from typing import List, Optional, Dict, Any, Tuple
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import numpy as np
# Project setup
project_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))
sys.path.append(project_root)
# Environment variables
os.environ["GROQ_API_KEY"] = ""
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = "requirements_neo4j"
# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
DEFAULT_NUM_PACKAGES = 2  # or 3, 4, etc.
# Neo4j imports
from neo4j import GraphDatabase
# Sentence Transformers for embeddings
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
# Load the model (important to use the exact name)
model_name = "openai/gpt-oss-20b:free"
llm = ChatOpenAI(
    model=model_name,
    temperature=0.7
)
# =============================================================================
# SENTENCE TRANSFORMERS EMBEDDINGS CLASS
# =============================================================================
class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = 384
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    def embed_query(self, text):
        return self.model.encode(text).tolist()
# Initialize the embedding model
embedding_model = SentenceTransformerEmbeddings()
# =============================================================================
# ENUM DEFINITIONS
# =============================================================================
class StatusEnum(str, Enum):
    draft = "Draft"
    approved = "Approved"
    rejected = "Rejected"
    in_review = "In Review"
class PriorityEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"
class RiskSeverityEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"
class RequirementTypeEnum(str, Enum):
    functional = "Functional"
    non_functional = "Non-functional"
    performance = "Performance"
    safety = "Safety"
    regulatory = "Regulatory"
# =============================================================================
# BASE CLASS WITH SIMILARITY SUPPORT
# =============================================================================
class SimilarityInfo(BaseModel):
    similarity_check_performed: bool = Field(default=False)
    similarity_score: Optional[float] = Field(default=None, description="Similarity score with the most similar node")
    similar_node_id: Optional[str] = Field(default=None, description="ID of the most similar node")
    similarity_reason: Optional[str] = Field(default=None, description="Reason for similarity (e.g., description match)")
class BaseEntity(BaseModel):
    id: str = Field(..., description="Unique identifier")
    description: str = Field(..., description="Primary description")
    status: StatusEnum = Field(default=StatusEnum.draft)
    version: str = Field(default="1.0")
    created_by: Optional[str] = Field(default="System")
    created_on: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    linked_to: List[str] = Field(default_factory=list, description="IDs of related entities")
    similarity_info: SimilarityInfo = Field(default_factory=SimilarityInfo)
# =============================================================================
# SPECIFIC CLASSES - WITH ID AND DESCRIPTION AS PRIMARY FIELDS
# =============================================================================
class KeywordOutput(BaseModel):
    keywords: List[str] = Field(..., description="2-3 keywords, each 3 words long")
class Project(BaseEntity):
    name: str = Field(..., description="Project name")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    owner: Optional[str] = None
    category: Optional[str] = None
class StakeholderNeed(BaseEntity):
    stakeholder: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.medium
    rationale: Optional[str] = None
class Requirement(BaseEntity):
    project: str = Field(default="")
    type: RequirementTypeEnum = RequirementTypeEnum.functional
    priority: PriorityEnum = PriorityEnum.high
    acceptance_criteria: Optional[str] = None
    rationale: Optional[str] = None
    trace_to_stakeholder: Optional[str] = None
class DesignSpec(BaseEntity):
    component: Optional[str] = None
    engineering_reference: Optional[str] = None
    feasibility: Optional[str] = None
class Risk(BaseEntity):
    severity: RiskSeverityEnum = RiskSeverityEnum.medium
    probability: PriorityEnum = PriorityEnum.medium
    impact: PriorityEnum = PriorityEnum.medium
    risk_score: Optional[int] = None
    category: Optional[str] = None
class Mitigation(BaseEntity):
    applies_to_risk: str = Field(..., description="Risk ID this mitigation applies to")
    effectiveness: PriorityEnum = PriorityEnum.medium
    implementation_owner: Optional[str] = None
class TestCase(BaseEntity):
    test_type: str = Field(default="Functional")
    expected_result: str = Field(..., description="Expected test outcome")
    test_method: str = Field(default="Manual")
    pass_fail_criteria: Optional[str] = None
class Tooling(BaseEntity):
    tool_type: str = Field(default="Injection Mold")
    lead_time_days: Optional[int] = None
    supplier: Optional[str] = None
class Cost(BaseEntity):
    estimated_cost: float = Field(..., description="Estimated cost amount")
    currency: str = Field(default="USD")
    lifecycle_cost: Optional[float] = None
    cost_driver: Optional[str] = None
class Manufacturing(BaseEntity):
    process_type: str = Field(default="Mass Production")
    cycle_time: Optional[float] = None
    machine_requirement: Optional[str] = None
class Compliance(BaseEntity):
    standard_name: str = Field(..., description="Name of the standard")
    jurisdiction: Optional[str] = None
    mandatory: bool = Field(default=True)
class ChangeRequest(BaseEntity):
    initiated_by: str = Field(..., description="Who initiated the change")
    priority: PriorityEnum = PriorityEnum.high
    impact_analysis: Optional[str] = None
    approved_by: Optional[str] = None


# =============================================================================
# COMPOSITE CLASSES
# =============================================================================
class RequirementPackage(BaseModel):
    stakeholder_need: StakeholderNeed
    requirement: Requirement
    design_spec: DesignSpec
    risk: Risk
    mitigation: Mitigation
    test_case: TestCase
    tooling: Tooling
    cost: Cost
    manufacturing: Manufacturing
    compliance: Compliance
class ImpactAnalysis(BaseModel):
    source_requirement: str
    impacted_elements: List[Dict[str, Any]]
    severity: str
    total_impact_weight: float
class DependencyAnalysis(BaseModel):
    requirement_a: str
    requirement_b: str
    connection_paths: int
    shared_nodes: List[str]
    impact_severity: str
    recommendation: str
# =============================================================================
# NEO4J CONNECTION WITH VECTOR SUPPORT
# =============================================================================
class Neo4jConnection:
    def __init__(self, uri="neo4j+s://39397f27.databases.neo4j.io", user="neo4j", password=""):
    # def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="123456789"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._initialize_database()
    def close(self):
        self.driver.close()
    def _initialize_database(self):
        """Initialize the database with constraints, indexes, and vector support"""
        try:
            with self.driver.session(database="neo4j") as session:
                # Create constraints for unique IDs
                constraints = [
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:StakeholderNeed) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Requirement) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:DesignSpec) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Risk) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Mitigation) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:TestCase) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Tooling) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Cost) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Manufacturing) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Compliance) REQUIRE n.id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ChangeRequest) REQUIRE n.id IS UNIQUE"
                ]
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        print(f"⚠️  Could not create constraint: {e}")
                # Create vector indexes for similarity search
                vector_indexes = [
                    """
                    CREATE VECTOR INDEX stakeholder_need_similarity IF NOT EXISTS
                    FOR (n:StakeholderNeed) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """,
                    """
                    CREATE VECTOR INDEX requirement_similarity IF NOT EXISTS
                    FOR (n:Requirement) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """,
                    """
                    CREATE VECTOR INDEX risk_similarity IF NOT EXISTS
                    FOR (n:Risk) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """,
                    """
                    CREATE VECTOR INDEX compliance_similarity IF NOT EXISTS
                    FOR (n:Compliance) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """,
                    """
                    CREATE VECTOR INDEX design_spec_similarity IF NOT EXISTS
                    FOR (n:DesignSpec) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """
                ]
                for index_query in vector_indexes:
                    try:
                        session.run(index_query)
                    except Exception as e:
                        print(f"⚠️  Could not create vector index: {e}")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")
    def execute_query(self, query, parameters=None):
        try:
            with self.driver.session(database="neo4j") as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"⚠️  Query execution warning: {e}")
            return []
# Global Neo4j connection
neo4j_conn = Neo4jConnection()
# =============================================================================
# PROJECT MANAGEMENT FUNCTIONS
# =============================================================================
def get_existing_projects() -> List[Dict[str, Any]]:
    """Get all existing projects from Neo4j"""
    try:
        query = """
        MATCH (p:Project)
        RETURN p.id AS id, p.name AS name, p.description AS description,
               p.created_on AS created_on, p.status AS status
        ORDER BY p.id
        """
        return neo4j_conn.execute_query(query)
    except Exception as e:
        print(f"⚠️  Error getting projects: {e}")
        return []
def get_next_project_id() -> str:
    """Generate the next available project ID (PRJ-001, PRJ-002, etc.)"""
    try:
        query = """
        MATCH (p:Project)
        WHERE p.id STARTS WITH 'PRJ-'
        RETURN p.id
        ORDER BY p.id DESC
        LIMIT 1
        """
        results = neo4j_conn.execute_query(query)
        if not results:
            return "PRJ-001"
        # Extract the highest number
        highest_id = results[0]['p.id']
        try:
            num_part = highest_id.split('-')[1]
            current_num = int(num_part)
            next_num = current_num + 1
            return f"PRJ-{next_num:03d}"
        except (IndexError, ValueError):
            return "PRJ-001"
    except Exception as e:
        print(f"⚠️  Error generating project ID: {e}")
        return "PRJ-001"
def create_new_project(project_id: str, name: str, description: str = "") -> bool:
    """Create a new project in Neo4j"""
    try:
        query = """
        CREATE (p:Project {
            id: $id,
            name: $name,
            description: $description,
            status: $status,
            version: $version,
            created_by: $created_by,
            created_on: $created_on,
            last_modified: $last_modified
        })
        RETURN p.id
        """
        result = neo4j_conn.execute_query(query, {
            "id": project_id,
            "name": name,
            "description": description or f"Project {project_id}",
            "status": "Active",
            "version": "1.0",
            "created_by": "User",
            "created_on": datetime.utcnow(),
            "last_modified": datetime.utcnow()
        })
        return len(result) > 0
    except Exception as e:
        print(f"⚠️  Error creating project: {e}")
        return False
def select_or_create_project() -> Dict[str, Any]:
    """Let user select from existing projects or create a new one"""
    print("\n" + "="*60)
    print("🏢 PROJECT SELECTION")
    print("="*60)
    # Get existing projects
    existing_projects = get_existing_projects()
    if existing_projects:
        print("\n📋 EXISTING PROJECTS:")
        for i, project in enumerate(existing_projects, 1):
            print(f"  {i}. {project['id']}: {project['name']}")
            if project.get('description'):
                print(f"     {project['description'][:80]}...")
            print(f"     Created: {project.get('created_on', 'Unknown')}, Status: {project.get('status', 'Unknown')}")
            print()
    print("  N. Create NEW Project")
    print("  Q. Quit")
    while True:
        choice = input("\n👉 Select project (number/N/Q): ").strip().upper()
        if choice == 'Q':
            return None
        if choice == 'N':
            # Create new project
            print("\n🆕 CREATING NEW PROJECT")
            project_id = get_next_project_id()
            print(f"📝 Generated Project ID: {project_id}")
            name = input("🏷️  Enter project name: ").strip()
            if not name:
                name = f"Project {project_id}"
            description = input("📄 Enter project description (optional): ").strip()
            if create_new_project(project_id, name, description):
                print(f"✅ Created new project: {project_id} - {name}")
                return {
                    "id": project_id,
                    "name": name,
                    "description": description,
                    "is_new": True
                }
            else:
                print("❌ Failed to create project")
                continue
        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(existing_projects):
                selected_project = existing_projects[choice_num - 1]
                print(f"✅ Selected project: {selected_project['id']} - {selected_project['name']}")
                return {
                    "id": selected_project['id'],
                    "name": selected_project['name'],
                    "description": selected_project.get('description', ''),
                    "is_new": False
                }
        print("❌ Invalid choice. Please try again.")
# =============================================================================
# SIMILARITY SEARCH FUNCTIONS
# =============================================================================
def check_similarity(node_type: str, description: str, threshold: float = 0.8) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Check if a similar node already exists in Neo4j using vector similarity search
    Returns: (similarity_score, similar_node_id, similarity_reason)
    """
    try:
        # Generate embedding for the description
        embedding = embedding_model.embed_query(description)
        # Map node types to their labels and index names
        type_mapping = {
            "stakeholder_need": ("StakeholderNeed", "stakeholder_need_similarity"),
            "requirement": ("Requirement", "requirement_similarity"), 
            "risk": ("Risk", "risk_similarity"),
            "compliance": ("Compliance", "compliance_similarity"),
            "design_spec": ("DesignSpec", "design_spec_similarity")
        }
        if node_type not in type_mapping:
            return None, None, None
        node_label, index_name = type_mapping[node_type]
        # Perform similarity search using Neo4j vector index
        query = f"""
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        WHERE score > $threshold
        RETURN node.id AS similar_id, node.description AS similar_description, score
        ORDER BY score DESC
        LIMIT 1
        """
        results = neo4j_conn.execute_query(query, {
            "index_name": index_name,
            "top_k": 5,
            "embedding": embedding,
            "threshold": threshold
        })
        if results and len(results) > 0:
            result = results[0]
            return result['score'], result['similar_id'], f"High similarity with existing {node_label}: {result['similar_description'][:100]}..."
        else:
            return 0.0, None, "No similar nodes found above threshold"
    except Exception as e:
        print(f"⚠️  Similarity search error for {node_type}: {e}")
        return None, None, None
def check_all_similarities(package: RequirementPackage) -> RequirementPackage:
    """Check similarities for all components in a requirement package"""
    # Check similarity for StakeholderNeed
    sn_similarity = check_similarity("stakeholder_need", package.stakeholder_need.description)
    package.stakeholder_need.similarity_info = SimilarityInfo(
        similarity_check_performed=True,
        similarity_score=sn_similarity[0],
        similar_node_id=sn_similarity[1],
        similarity_reason=sn_similarity[2]
    )
    # Check similarity for Requirement
    req_similarity = check_similarity("requirement", package.requirement.description)
    package.requirement.similarity_info = SimilarityInfo(
        similarity_check_performed=True,
        similarity_score=req_similarity[0],
        similar_node_id=req_similarity[1],
        similarity_reason=req_similarity[2]
    )
    # Check similarity for Risk
    risk_similarity = check_similarity("risk", package.risk.description)
    package.risk.similarity_info = SimilarityInfo(
        similarity_check_performed=True,
        similarity_score=risk_similarity[0],
        similar_node_id=risk_similarity[1],
        similarity_reason=risk_similarity[2]
    )
    # Check similarity for Compliance
    comp_similarity = check_similarity("compliance", package.compliance.description)
    package.compliance.similarity_info = SimilarityInfo(
        similarity_check_performed=True,
        similarity_score=comp_similarity[0],
        similar_node_id=comp_similarity[1],
        similarity_reason=comp_similarity[2]
    )
    # Check similarity for DesignSpec
    ds_similarity = check_similarity("design_spec", package.design_spec.description)
    package.design_spec.similarity_info = SimilarityInfo(
        similarity_check_performed=True,
        similarity_score=ds_similarity[0],
        similar_node_id=ds_similarity[1],
        similarity_reason=ds_similarity[2]
    )
    return package
def display_similarity_results(package: RequirementPackage):
    """Display similarity results for a package"""
    print(f"\n🔍 SIMILARITY ANALYSIS RESULTS:")
    components = [
        ("Stakeholder Need", package.stakeholder_need),
        ("Requirement", package.requirement),
        ("Risk", package.risk),
        ("Compliance", package.compliance),
        ("Design Spec", package.design_spec)
    ]
    for name, component in components:
        print(f"   {name} {component.id}:")
        if component.similarity_info.similarity_score and component.similarity_info.similarity_score > 0.7:
            print(f"     ⚠️  SIMILAR: {component.similarity_info.similarity_score:.3f} - {component.similarity_info.similarity_reason}")
        else:
            print(f"     ✅ UNIQUE: No significant similarities found")
# =============================================================================
# GRAPH STATE
# =============================================================================
class RequirementState(TypedDict):
    requirement_description: str
    keyword_output: Optional[KeywordOutput]
    selected_keyword: Optional[str]
    stakeholder_need: Optional[StakeholderNeed]
    requirement_packages: Optional[List[RequirementPackage]]
    approval_status: Optional[str]
    impact_analysis: Optional[ImpactAnalysis]
    dependency_analysis: Optional[DependencyAnalysis]
    change_request: Optional[ChangeRequest]
    existing_requirements: Optional[List[str]]
    shared_nodes_found: Optional[List[Dict[str, Any]]]
    modification_mode: Optional[bool]
    target_requirement_id: Optional[str]
    id_counter: Optional[Dict[str, int]]
    user_feedback: Optional[str]
    regeneration_count: Optional[int]
    original_packages: Optional[List[RequirementPackage]]
    regenerate_specific_id: Optional[str]
    current_project: Optional[Dict[str, Any]]
# =============================================================================
# UTILITY FUNCTIONS - IMPROVED ID GENERATION
# =============================================================================
def initialize_id_counter() -> Dict[str, int]:
    """Initialize ID counter for all node types based on database state - IMPROVED"""
    counter = {}
    prefixes = ['SN', 'RQ', 'DS', 'RK', 'MT', 'TC', 'TL', 'CF', 'MP', 'CR', 'CRQ']
    for prefix in prefixes:
        try:
            # Query to find the highest existing ID for this prefix
            query = """
            MATCH (n) 
            WHERE n.id STARTS WITH $prefix
            RETURN n.id
            ORDER BY n.id DESC
            LIMIT 1
            """
            results = neo4j_conn.execute_query(query, {"prefix": f"{prefix}-"})
            if not results:
                counter[prefix] = 1
            else:
                # Extract the highest number
                highest_id = results[0]['n.id']
                try:
                    num_part = highest_id.split('-')[1]
                    current_num = int(num_part)
                    counter[prefix] = current_num + 1
                except (IndexError, ValueError):
                    counter[prefix] = 1
        except Exception as e:
            print(f"⚠️  Warning initializing counter for {prefix}: {e}")
            counter[prefix] = 1
    # Ensure RQ counter is used for all related components
    # This ensures sequencing: RQ-001 -> DS-001, RK-001, etc.
    if 'RQ' in counter:
        rq_counter = counter['RQ']
        for prefix in ['DS', 'RK', 'MT', 'TC', 'TL', 'CF', 'MP', 'CR']:
            if prefix in counter:
                counter[prefix] = max(counter[prefix], rq_counter)
    return counter
def generate_unique_id(state: RequirementState, prefix: str) -> str:
    """Generate unique ID using session counter to ensure uniqueness within this run"""
    counter = state.get("id_counter", initialize_id_counter())
    current_id = counter.get(prefix, 1)
    new_id = f"{prefix}-{current_id:03d}"
    # Update counter for next call
    counter[prefix] = current_id + 1
    return new_id
def check_database_has_data() -> bool:
    """Check if database has any requirements data"""
    try:
        query = "MATCH (n) RETURN n LIMIT 1"
        result = neo4j_conn.execute_query(query)
        return len(result) > 0
    except Exception:
        return False
def get_existing_requirements(project_id: str = None) -> List[str]:
    """Get list of all existing requirements for a specific project"""
    if not check_database_has_data():
        return []
    try:
        if project_id:
            query = """
            MATCH (p:Project {id: $project_id})-[:HAS_REQUIREMENT]->(rq:Requirement)
            RETURN rq.id ORDER BY rq.id
            """
            results = neo4j_conn.execute_query(query, {"project_id": project_id})
        else:
            query = "MATCH (rq:Requirement) RETURN rq.id ORDER BY rq.id"
            results = neo4j_conn.execute_query(query)
        return [record['rq.id'] for record in results]
    except Exception:
        return []
def get_project_requirements(project_id: str) -> List[Dict[str, Any]]:
    """Get all requirements for a specific project"""
    try:
        # First check if requirements exist at all
        check_query = """
        MATCH (rq:Requirement)
        RETURN COUNT(rq) AS total_requirements
        """
        check_result = neo4j_conn.execute_query(check_query)
        if not check_result or check_result[0].get('total_requirements', 0) == 0:
            return []  # No requirements in database
        # If we have requirements, query them for the specific project
        query = """
        MATCH (p:Project {id: $project_id})-[:HAS_REQUIREMENT]->(rq:Requirement)
        RETURN rq.id AS requirement_id, rq.description AS description, rq.created_on AS created
        ORDER BY rq.id
        """
        return neo4j_conn.execute_query(query, {"project_id": project_id})
    except Exception as e:
        print(f"⚠️  Error getting project requirements: {e}")
        return []
def find_all_shared_nodes(project_id: str = None) -> List[Dict[str, Any]]:
    """Find all shared nodes across the graph - FIXED for empty database"""
    if not check_database_has_data():
        return []
    try:
        if project_id:
            # Find shared nodes within a specific project
            query = """
            MATCH (p:Project {id: $project_id})-[:HAS_REQUIREMENT]->(rq:Requirement)-->(shared)
            WHERE any(label in labels(shared) WHERE label IN ['DesignSpec', 'Manufacturing', 'Tooling', 'StakeholderNeed', 'Risk', 'Mitigation', 'TestCase', 'Cost', 'Compliance'])
            WITH shared, COUNT(DISTINCT rq) AS req_count
            WHERE req_count > 1
            RETURN shared.id AS node_id, shared.description AS description, 
                   labels(shared)[0] AS type, req_count
            ORDER BY req_count DESC
            LIMIT 10
            """
            return neo4j_conn.execute_query(query, {"project_id": project_id})
        else:
            # Find shared nodes across all projects
            query = """
            MATCH (shared)
            WHERE any(label in labels(shared) WHERE label IN ['DesignSpec', 'Manufacturing', 'Tooling', 'StakeholderNeed', 'Risk', 'Mitigation', 'TestCase', 'Cost', 'Compliance'])
            WITH shared, size([(shared)<--(rq:Requirement) | rq]) AS req_count
            WHERE req_count > 1
            RETURN shared.id AS node_id, shared.description AS description, 
                   labels(shared)[0] AS type, req_count
            ORDER BY req_count DESC
            LIMIT 10
            """
            return neo4j_conn.execute_query(query)
    except Exception as e:
        print(f"⚠️  Shared nodes query warning: {e}")
        return []
def perform_impact_analysis(requirement_id: str) -> ImpactAnalysis:
    """Perform impact analysis for a requirement"""
    if not check_database_has_data():
        return ImpactAnalysis(
            source_requirement=requirement_id,
            impacted_elements=[],
            severity="Unknown",
            total_impact_weight=0.0
        )
    try:
        # Direct impact query
        impact_query = """
        MATCH (rq:Requirement {id: $requirement_id})-[r*1..3]-(impacted)
        RETURN DISTINCT impacted.id AS Impacted_Element_ID, 
               labels(impacted) AS Element_Type, 
               impacted.description AS Description,
               type(r[0]) AS Relationship_Type
        """
        results = neo4j_conn.execute_query(impact_query, {"requirement_id": requirement_id})
        # Calculate impact weight
        severity_weights = {"High": 0.9, "Medium": 0.5, "Low": 0.2}
        total_weight = 0
        for record in results:
            rel_type = record.get('Relationship_Type', '')
            if 'HAS_RISK' in rel_type:
                total_weight += severity_weights.get("High", 0.5)
            elif 'IMPLEMENTS' in rel_type:
                total_weight += severity_weights.get("Medium", 0.3)
            else:
                total_weight += severity_weights.get("Low", 0.1)
        # Determine overall severity
        if total_weight > 2.0:
            severity = "High"
        elif total_weight > 1.0:
            severity = "Medium"
        else:
            severity = "Low"
        return ImpactAnalysis(
            source_requirement=requirement_id,
            impacted_elements=results,
            severity=severity,
            total_impact_weight=total_weight
        )
    except Exception as e:
        print(f"⚠️  Error performing impact analysis: {e}")
        return ImpactAnalysis(
            source_requirement=requirement_id,
            impacted_elements=[],
            severity="Unknown",
            total_impact_weight=0.0
        )
def check_requirement_dependency(req_a: str, req_b: str) -> DependencyAnalysis:
    """Check dependency between two requirements"""
    if not check_database_has_data():
        return DependencyAnalysis(
            requirement_a=req_a,
            requirement_b=req_b,
            connection_paths=0,
            shared_nodes=[],
            impact_severity="NONE",
            recommendation="No existing requirements to analyze dependencies with"
        )
    try:
        # Check connection paths
        connection_query = """
        MATCH path=(rq1:Requirement {id: $req_a})-[*1..5]-(rq2:Requirement {id: $req_b})
        RETURN COUNT(path) AS NumConnections
        """
        connection_result = neo4j_conn.execute_query(connection_query, {"req_a": req_a, "req_b": req_b})
        num_connections = connection_result[0]['NumConnections'] if connection_result else 0
        # Check shared nodes
        shared_nodes_query = """
        MATCH (rq1:Requirement {id: $req_a})-->(shared)<--(rq2:Requirement {id: $req_b})
        RETURN shared.id AS shared_id, labels(shared) AS shared_type
        """
        # shared_nodes_result = neo4j_conn.execute_query(shared_nodes_query, {"req_a": req_a, {"req_b": req_b})
        # shared_nodes = [f"{node['shared_id']} ({node['shared_type'][0]})" for node in shared_nodes_result]
        shared_nodes_result = neo4j_conn.execute_query(shared_nodes_query, {"req_a": req_a, "req_b": req_b})
        shared_nodes = [f"{node['shared_id']} ({node['shared_type'][0]})" for node in shared_nodes_result]
        # Determine impact severity
        if num_connections > 3 or any('Manufacturing' in node for node in shared_nodes):
            impact_severity = "HIGH"
            recommendation = "Immediate review required - shared manufacturing processes"
        elif num_connections > 1 or any('DesignSpec' in node for node in shared_nodes):
            impact_severity = "MEDIUM"
            recommendation = "Review recommended - shared design elements"
        elif num_connections > 0:
            impact_severity = "LOW"
            recommendation = "Monitor for changes - indirect connections exist"
        else:
            impact_severity = "NONE"
            recommendation = "No immediate impact detected"
        return DependencyAnalysis(
            requirement_a=req_a,
            requirement_b=req_b,
            connection_paths=num_connections,
            shared_nodes=shared_nodes,
            impact_severity=impact_severity,
            recommendation=recommendation
        )
    except Exception as e:
        print(f"⚠️  Error checking dependency: {e}")
        return DependencyAnalysis(
            requirement_a=req_a,
            requirement_b=req_b,
            connection_paths=0,
            shared_nodes=[],
            impact_severity="UNKNOWN",
            recommendation="Error analyzing dependency"
        )
# =============================================================================
# LANGGRAPH NODES - ENHANCED WITH SIMILARITY AND REGENERATION
# =============================================================================
def initialize_workflow(state: RequirementState):
    """Step 0: Initialize workflow with project selection"""
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE REQUIREMENTS MANAGEMENT SYSTEM WITH VECTOR SIMILARITY")
    print("="*80)
    # Project selection
    selected_project = select_or_create_project()
    if not selected_project:
        print("❌ No project selected. Exiting workflow.")
        return {"current_project": None}
    # Initialize ID counter based on current database state
    id_counter = initialize_id_counter()
    # Check if database has any data and show project info
    existing_reqs = get_existing_requirements(selected_project['id'])
    project_reqs = get_project_requirements(selected_project['id'])
    print(f"\n🏢 SELECTED PROJECT: {selected_project['name']} ({selected_project['id']})")
    if selected_project.get('is_new'):
        print("🆕 This is a NEW project")
    else:
        print("📁 This is an EXISTING project")
    if project_reqs:
        print(f"📋 Project has {len(project_reqs)} requirements:")
        for req in project_reqs[:3]:  # Show first 3
            desc = req['description'][:60] + "..." if len(req['description']) > 60 else req['description']
            print(f"   • {req['requirement_id']}: {desc}")
        if len(project_reqs) > 3:
            print(f"   • ... and {len(project_reqs) - 3} more requirements")
    if existing_reqs and len(existing_reqs) > len(project_reqs):
        print(f"\n📋 Found {len(existing_reqs)} total requirements in database for this project")
    # Get requirement description from user
    print(f"\n📝 REQUIREMENT INPUT FOR PROJECT: {selected_project['name']}")
    if not state.get("requirement_description"):
        requirement_description = input("Enter the requirement description: ").strip()
        if not requirement_description:
            requirement_description = """The ballpoint pen manufacturing system shall be designed to produce high-quality writing instruments that deliver smooth ink flow, ergonomic comfort, and durability. It must ensure consistent writing performance for at least 1500 meters without leakage or skipping. The materials used shall be non-toxic, lightweight, and compliant with international safety standards such as ISO and ASTM. The manufacturing process shall support production volumes of 50,000 units per month with 99.5% quality yield."""
            print(f"Using default requirement description: {requirement_description[:100]}...")
    else:
        requirement_description = state["requirement_description"]
    return {
        "requirement_description": requirement_description,
        "modification_mode": False,
        "target_requirement_id": None,
        "existing_requirements": existing_reqs,
        "id_counter": id_counter,
        "regeneration_count": 0,
        "user_feedback": None,
        "original_packages": None,
        "regenerate_specific_id": None,
        "current_project": selected_project
    }
def generate_keywords(state: RequirementState):
    """Step 1: Generate keywords from requirement description"""
    parser = PydanticOutputParser(pydantic_object=KeywordOutput)
    llm = ChatOpenAI(
    model=model_name,
    temperature=0.7
)
    prompt = ChatPromptTemplate.from_template("""
    You are an expert requirement analyst.
    Given this requirement description:
    "{requirement_description}"
    Generate exactly 2-3 keywords, each containing 3 words that capture key aspects.
    Focus on: functionality, quality attributes, and constraints.
    {format_instructions}
    """)
    chain = prompt | llm | parser
    result = chain.invoke({
        "requirement_description": state["requirement_description"],
        "format_instructions": parser.get_format_instructions()
    })
    print(f"\n📝 Generated Keywords: {result.keywords}")
    return {"keyword_output": result}
def human_select_keyword(state: RequirementState):
    """Step 2: Human selects keyword focus"""
    print("\n" + "="*60)
    print("✅ GENERATED KEYWORDS")
    print("="*60)
    for i, kw in enumerate(state["keyword_output"].keywords, 1):
        print(f"  {i}. {kw}")
    while True:
        choice = input("\n👉 Select keyword number (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            return {"selected_keyword": None}
        if choice.isdigit() and 1 <= int(choice) <= len(state["keyword_output"].keywords):
            selected = state["keyword_output"].keywords[int(choice)-1]
            print(f"✓ Selected: {selected}")
            return {"selected_keyword": selected}
        print("❌ Invalid choice. Try again.")
def should_continue_to_requirements(state: RequirementState):
    """Conditional routing after keyword selection"""
    if state.get("selected_keyword"):
        return "generate_stakeholder_need"
    return END
def generate_stakeholder_need(state: RequirementState):
    """Step 3: Generate stakeholder need with session-based ID"""
    parser = PydanticOutputParser(pydantic_object=StakeholderNeed)
    llm = ChatOpenAI(
    model=model_name,
    temperature=0.7
)
    sn_id = generate_unique_id(state, "SN")
    prompt = ChatPromptTemplate.from_template("""
    You are a requirements engineering specialist.
    Based on this requirement description and selected keyword focus:
    Description: "{requirement_description}"
    Keyword Focus: "{selected_keyword}"
    Generate a clear stakeholder need statement that:
    - Identifies the user pain point or business problem
    - Defines success criteria
    - References any regulatory drivers
    - Is concise and business-focused
    Analyze: User pain points, business problems, success criteria, regulatory drivers
    Use this ID: {sn_id}
    Additional fields to populate:
    - stakeholder: Identify the primary stakeholder (e.g., "End Users", "Manufacturing Team", "Quality Assurance")
    - priority: Choose from Low, Medium, High, Critical
    - rationale: Explain why this need is important
    {format_instructions}
    """)
    chain = prompt | llm | parser
    result = chain.invoke({
        "requirement_description": state["requirement_description"],
        "selected_keyword": state["selected_keyword"],
        "sn_id": sn_id,
        "format_instructions": parser.get_format_instructions()
    })
    print(f"\n🎯 STAKEHOLDER NEED: {result.id}")
    print(f"   {result.description}")
    print(f"   Stakeholder: {result.stakeholder}")
    print(f"   Priority: {result.priority}")
    # Update state with new ID counter
    return {
        "stakeholder_need": result,
        "id_counter": state["id_counter"]  # Pass the updated counter
    }
def detect_shared_nodes(state: RequirementState):
    """Step 4: Detect shared nodes with fixed query"""
    print("\n🔍 Scanning for shared nodes across requirements...")
    current_project = state.get("current_project")
    project_id = current_project['id'] if current_project else None
    shared_nodes = find_all_shared_nodes(project_id)
    if shared_nodes:
        print(f"\n📊 FOUND {len(shared_nodes)} SHARED NODES:")
        for node in shared_nodes[:3]:  # Show first 3
            desc = node.get('description', 'No description')[:80]
            print(f"   • {node['node_id']} ({node['type']}): {desc}...")
            print(f"     Used by {node['req_count']} requirements")
    else:
        print("\n📊 No shared nodes detected across requirements")
    return {"shared_nodes_found": shared_nodes}
import re
from datetime import datetime

def _fix_datetime_strings_in_package(pkg_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively fixes common datetime string formats in a package dictionary
    generated by the LLM to ensure Pydantic compatibility.
    """
    def fix_datetime_str(dt_str: str) -> str:
        # Example problematic format: "2025-10-25T12:14:0Z"
        # Expected format: "YYYY-MM-DDTHH:MM:SSZ"
        # Match the pattern YYYY-MM-DDTHH:MM:SZ (where S is a single digit)
        match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}):(\d)Z$', dt_str)
        if match:
            base_part = match.group(1)
            single_digit_second = match.group(2)
            # Pad the single digit second with a leading zero
            corrected_dt_str = f"{base_part}:{single_digit_second.zfill(2)}Z"
            print(f"   ⚠️  Fixed datetime string: {dt_str} -> {corrected_dt_str}")
            return corrected_dt_str
        # Add other common fixes here if needed
        # e.g., match and fix "2025-10-25T12Z" -> "2025-10-25T12:00:00Z"
        # For now, just return the original if no known fix applies
        return dt_str

    def process_dict(d):
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value)
            elif key in ['created_on', 'last_modified'] and isinstance(value, str):
                d[key] = fix_datetime_str(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        process_dict(item)

    process_dict(pkg_dict)
    return pkg_dict

def generate_comprehensive_requirement_packages(state: RequirementState):
    """Step 5: Generate N distinct requirement packages in ONE LLM CALL with VECTOR SIMILARITY CHECK"""

    # === NEW: Batch output model ===
    class RequirementPackageBatch(BaseModel):
        packages: List[RequirementPackage] = Field(
            ...,
            description="A list of distinct requirement packages. Each must differ significantly in design, risk, tooling, or compliance approach."
        )

    # === NEW: Approaches model ===
    class EngineeringApproach(BaseModel):
        name: str = Field(
            ..., description="A short, descriptive name for the approach (e.g., 'Integrated Heat Source', 'Cartridge-Based System')"
        )
        description: str = Field(
            ..., description="A detailed explanation of the engineering approach, including its core principle, potential advantages, and disadvantages or challenges."
        )

    class ApproachesList(BaseModel):
        approaches: List[EngineeringApproach] = Field(
            ..., description="A list of distinct engineering approaches."
        )

    parser_batch = PydanticOutputParser(pydantic_object=RequirementPackageBatch)
    parser_approaches = PydanticOutputParser(pydantic_object=ApproachesList)
    llm = ChatOpenAI(model=model_name, temperature=0.85)  # Slightly higher temp for diversity

    current_counter = state["id_counter"].copy()
    current_project = state["current_project"]

    # Check if this is a regeneration with user feedback
    is_regeneration = state.get("user_feedback") is not None
    regeneration_count = state.get("regeneration_count", 0)
    specific_id = state.get("regenerate_specific_id")

    if is_regeneration:
        if specific_id:
            print(
                f"\n🔄 REGENERATING SPECIFIC REQUIREMENT: {specific_id} (Attempt {regeneration_count + 1})"
            )
            print(f"📝 User Feedback: {state['user_feedback']}")
        else:
            print(
                f"\n🔄 REGENERATING ALL REQUIREMENT PACKAGES (Attempt {regeneration_count + 1})"
            )
            print(f"📝 User Feedback: {state['user_feedback']}")

    # --- Helper function to fix datetime strings ---
    def _fix_datetime_strings_in_package(pkg_dict: dict) -> dict:
        """
        Recursively fixes common datetime string formats in a package dictionary
        generated by the LLM to ensure Pydantic compatibility.
        """

        def fix_datetime_str(dt_str: str) -> str:
            # Example: "2025-10-25T12:14:0Z" -> "2025-10-25T12:14:00Z"
            match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}):(\d)Z$", dt_str)
            if match:
                corrected = f"{match.group(1)}:{match.group(2).zfill(2)}Z"
                print(f"   ⚠️  Fixed datetime string: {dt_str} -> {corrected}")
                return corrected
            return dt_str

        def process_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    process_dict(value)
                elif key in ["created_on", "last_modified"] and isinstance(value, str):
                    d[key] = fix_datetime_str(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            process_dict(item)

        process_dict(pkg_dict)
        return pkg_dict

    # === Regeneration logic ===
    if is_regeneration and specific_id:
        # Regenerate a single package
        try:
            req_number = specific_id.split("-")[1]
        except (IndexError, ValueError):
            req_number = f"{current_counter['RQ']:03d}"

        ids = {
            "req_id": specific_id,
            "ds_id": f"DS-{req_number}",
            "rk_id": f"RK-{req_number}",
            "mt_id": f"MT-{req_number}",
            "tc_id": f"TC-{req_number}",
            "tl_id": f"TL-{req_number}",
            "cf_id": f"CF-{req_number}",
            "mp_id": f"MP-{req_number}",
            "cr_id": f"CR-{req_number}",
        }

        single_parser = PydanticOutputParser(pydantic_object=RequirementPackage)
        prompt = ChatPromptTemplate.from_template("""
        You are a systems requirements analyst regenerating a SINGLE requirement package.
        PROJECT: {project_name}
        STAKEHOLDER NEED: {stakeholder_need}
        KEYWORD FOCUS: {selected_keyword}
        ORIGINAL REQUIREMENT: {original_requirement}
        USER FEEDBACK: {user_feedback}
        TARGET REQUIREMENT ID: {target_id}

        Please address the user feedback specifically and improve ONLY this requirement package.
        Generate a COMPLETE requirement package with ALL artifacts.
        CRITICAL FOR DATETIME FIELDS: Use ISO 8601 format for 'created_on' and 'last_modified'.
        Use these EXACT IDs:
        - Requirement: {req_id}
        - Design Spec: {ds_id}
        - Risk: {rk_id}
        - Mitigation: {mt_id}
        - Test Case: {tc_id}
        - Tooling: {tl_id}
        - Cost: {cf_id}
        - Manufacturing: {mp_id}
        - Compliance: {cr_id}
        {format_instructions}
        """)

        original_packages = state.get("original_packages", state["requirement_packages"])
        package_to_regenerate = next(
            (pkg for pkg in original_packages if pkg.requirement.id == specific_id), None
        )
        if not package_to_regenerate:
            print(f"❌ Could not find requirement with ID {specific_id} to regenerate")
            return {"requirement_packages": state["requirement_packages"], "id_counter": current_counter}

        chain = prompt | llm | single_parser
        try:
            new_package = chain.invoke({
                "project_name": current_project["name"],
                "stakeholder_need": state["stakeholder_need"].description,
                "selected_keyword": state["selected_keyword"],
                "original_requirement": package_to_regenerate.requirement.description,
                "user_feedback": state["user_feedback"],
                **ids,
                "target_id": specific_id,
                "format_instructions": single_parser.get_format_instructions(),
            })
        except Exception as e:
            print(f"⚠️ Error parsing regenerated package for {specific_id}: {e}")
            print("   Attempting to fix datetime strings...")
            json_parser = JsonOutputParser()
            json_chain = prompt | llm | json_parser
            try:
                raw_output = json_chain.invoke({
                    "project_name": current_project["name"],
                    "stakeholder_need": state["stakeholder_need"].description,
                    "selected_keyword": state["selected_keyword"],
                    "original_requirement": package_to_regenerate.requirement.description,
                    "user_feedback": state["user_feedback"],
                    **ids,
                    "target_id": specific_id,
                    "format_instructions": json_parser.get_format_instructions(),
                })
                fixed_output = _fix_datetime_strings_in_package(raw_output)
                new_package = RequirementPackage.model_validate(fixed_output)
                print(f"   ✅ Successfully fixed and parsed regenerated package for {specific_id}")
            except Exception as e2:
                print(f"❌ Failed to regenerate package for {specific_id}: {e2}")
                return {"requirement_packages": state["requirement_packages"], "id_counter": current_counter}

        new_package.requirement.project = current_project["id"]
        packages = state["requirement_packages"].copy()
        for i, pkg in enumerate(packages):
            if pkg.requirement.id == specific_id:
                packages[i] = new_package
                break

    elif is_regeneration and not specific_id:
        # Regenerate all packages individually
        packages = []
        original_packages = state.get("original_packages", state["requirement_packages"])
        for original_pkg in original_packages:
            original_req_id = original_pkg.requirement.id
            try:
                req_number = original_req_id.split("-")[1]
            except (IndexError, ValueError):
                req_number = f"{current_counter['RQ']:03d}"

            ids = {
                "req_id": original_req_id,
                "ds_id": f"DS-{req_number}",
                "rk_id": f"RK-{req_number}",
                "mt_id": f"MT-{req_number}",
                "tc_id": f"TC-{req_number}",
                "tl_id": f"TL-{req_number}",
                "cf_id": f"CF-{req_number}",
                "mp_id": f"MP-{req_number}",
                "cr_id": f"CR-{req_number}",
            }

            single_parser = PydanticOutputParser(pydantic_object=RequirementPackage)
            prompt = ChatPromptTemplate.from_template("""
            You are a systems requirements analyst regenerating a requirement package.
            PROJECT: {project_name}
            STAKEHOLDER NEED: {stakeholder_need}
            KEYWORD FOCUS: {selected_keyword}
            ORIGINAL REQUIREMENT: {original_requirement}
            USER FEEDBACK: {user_feedback}
            TARGET REQUIREMENT ID: {target_id}
            CRITICAL FOR DATETIME FIELDS: Use ISO 8601 format for 'created_on' and 'last_modified'.
            Use these EXACT IDs:
            - Requirement: {req_id}
            - Design Spec: {ds_id}
            - Risk: {rk_id}
            - Mitigation: {mt_id}
            - Test Case: {tc_id}
            - Tooling: {tl_id}
            - Cost: {cf_id}
            - Manufacturing: {mp_id}
            - Compliance: {cr_id}
            {format_instructions}
            """)

            chain = prompt | llm | single_parser
            try:
                new_package = chain.invoke({
                    "project_name": current_project["name"],
                    "stakeholder_need": state["stakeholder_need"].description,
                    "selected_keyword": state["selected_keyword"],
                    "original_requirement": original_pkg.requirement.description,
                    **ids,
                    "target_id": original_req_id,
                    "user_feedback": state["user_feedback"],
                    "format_instructions": single_parser.get_format_instructions(),
                })
            except Exception as e:
                print(f"⚠️ Error regenerating package {original_req_id}: {e}")
                # Optional: Add datetime fix fallback as above
                raise e

            new_package.requirement.project = current_project["id"]
            packages.append(new_package)

    else:
        # === ✅ MAIN BATCH GENERATION ===
        num_packages = DEFAULT_NUM_PACKAGES
        base_counter = current_counter["RQ"]
        id_sequences = [f"{base_counter + i:03d}" for i in range(num_packages)]

        formatted_id_blocks = "\n".join([
            f"- Package {i+1}:\n"
            f"  Requirement: RQ-{seq}\n"
            f"  DesignSpec: DS-{seq}\n"
            f"  Risk: RK-{seq}\n"
            f"  Mitigation: MT-{seq}\n"
            f"  TestCase: TC-{seq}\n"
            f"  Tooling: TL-{seq}\n"
            f"  Cost: CF-{seq}\n"
            f"  Manufacturing: MP-{seq}\n"
            f"  Compliance: CR-{seq}"
            for i, seq in enumerate(id_sequences)
        ])

        # --- Generate diverse approaches ---
        print(f"\n🔍 Generating diverse engineering approaches for '{state['selected_keyword']}'...")
        approaches_prompt = ChatPromptTemplate.from_template("""
        You are a senior systems engineer analyzing the following requirement input.
        PROJECT: {project_name}
        STAKEHOLDER NEED: {stakeholder_need}
        KEYWORD FOCUS: {selected_keyword}
        REQUIREMENT DESCRIPTION: {requirement_description}

        Generate exactly {num_packages} distinct and innovative engineering approaches.
        Ensure approaches are diverse and technically feasible.
        {format_instructions}
        """)

        approaches_chain = approaches_prompt | llm | parser_approaches
        try:
            approaches_result = approaches_chain.invoke({
                "project_name": current_project["name"],
                "stakeholder_need": state["stakeholder_need"].description,
                "selected_keyword": state["selected_keyword"],
                "requirement_description": state["requirement_description"],
                "num_packages": num_packages,
                "format_instructions": parser_approaches.get_format_instructions(),
            })
            dynamic_approaches = [a.description for a in approaches_result.approaches]
            print(f"✅ Generated {len(dynamic_approaches)} distinct approaches.")
        except Exception as e:
            print(f"⚠️ Error generating approaches: {e}. Using fallback prompt.")
            # fallback approaches logic here (omitted for brevity)
            dynamic_approaches = [f"Fallback Approach {i+1}" for i in range(num_packages)]

        # --- Batch generation prompt ---
        main_prompt = ChatPromptTemplate.from_template("""
        You are a senior systems engineer generating a DIVERSE SET of requirement packages.
        PROJECT: {project_name}
        STAKEHOLDER NEED: {stakeholder_need}
        KEYWORD FOCUS: {selected_keyword}
        REQUIREMENT DESCRIPTION: {requirement_description}

        CRITICAL: Generate exactly {num_packages} COMPLETE and DISTINCT requirement packages.
        Each package must represent a FUNDAMENTALLY DIFFERENT engineering approach chosen from:
        {dynamic_approaches_list}

        CRITICAL FOR DATETIME FIELDS: Use ISO 8601 format for 'created_on' and 'last_modified'.
        Use these EXACT IDs:
        {formatted_id_blocks}
        {format_instructions}
        """)

        chain = main_prompt | llm | parser_batch
        batch_result = chain.invoke({
            "project_name": current_project["name"],
            "stakeholder_need": state["stakeholder_need"].description,
            "selected_keyword": state["selected_keyword"],
            "requirement_description": state["requirement_description"],
            "num_packages": num_packages,
            "dynamic_approaches_list": "\n".join([f"{i+1}. {a}" for i, a in enumerate(dynamic_approaches)]),
            "formatted_id_blocks": formatted_id_blocks,
            "format_instructions": parser_batch.get_format_instructions(),
        })

        packages = batch_result.packages
        for pkg in packages:
            pkg.requirement.project = current_project["id"]
        current_counter["RQ"] = base_counter + num_packages

    # --- Perform similarity checks ---
    checked_packages = [check_all_similarities(pkg) for pkg in packages]
    for pkg in checked_packages:
        display_similarity_results(pkg)

    # --- Return state ---
    if not is_regeneration and state.get("original_packages") is None:
        return {
            "requirement_packages": checked_packages,
            "id_counter": current_counter,
            "original_packages": packages.copy()
        }
    return {"requirement_packages": checked_packages, "id_counter": current_counter}


def perform_dependency_analysis(state: RequirementState):
    """Step 6: Perform dependency analysis between requirements - FIXED VERSION"""
    print("\n🔗 Performing dependency analysis...")
    current_project = state.get("current_project")
    project_id = current_project['id'] if current_project else None
    # Check if we have existing requirements AND new packages
    existing_reqs = get_existing_requirements(project_id)
    new_packages = state.get("requirement_packages", [])
    if not existing_reqs or not new_packages:
        print("   No existing requirements or new packages for dependency analysis")
        return {"dependency_analysis": None}
    new_reqs = [pkg.requirement.id for pkg in new_packages]
    print(f"   Analyzing {len(new_reqs)} new requirements against {len(existing_reqs)} existing requirements in project {project_id}")
    # Analyze dependencies between new requirements and existing ones
    dependencies = []
    for new_req in new_reqs:
        for existing_req in existing_reqs[:3]:  # Check first 3 existing requirements
            print(f"   Checking dependency: {new_req} ↔ {existing_req}")
            analysis = check_requirement_dependency(new_req, existing_req)
            if analysis.connection_paths > 0 or analysis.shared_nodes:
                dependencies.append(analysis)
                print(f"     Found {analysis.connection_paths} connections, impact: {analysis.impact_severity}")
    if dependencies:
        print(f"\n⚠️  DEPENDENCY ANALYSIS RESULTS ({len(dependencies)} dependencies found):")
        for dep in dependencies:
            print(f"\n   {dep.requirement_a} ↔ {dep.requirement_b}")
            print(f"   Connections: {dep.connection_paths}")
            print(f"   Impact: {dep.impact_severity}")
            print(f"   Shared Nodes: {', '.join(dep.shared_nodes) if dep.shared_nodes else 'None'}")
            print(f"   Recommendation: {dep.recommendation}")
        # Return the first dependency for state tracking
        return {"dependency_analysis": dependencies[0]}
    print("   No dependencies found with existing requirements")
    return {"dependency_analysis": None}

def perform_impact_analysis_on_new_requirements(state: RequirementState):
    """NEW STEP: Perform impact analysis on newly created requirements"""
    print("\n🔍 Performing impact analysis on new requirements...")
    new_packages = state.get("requirement_packages", [])
    if not new_packages:
        print("   No new packages for impact analysis")
        return {"impact_analysis": None}
    # Perform impact analysis on the first requirement
    first_req_id = new_packages[0].requirement.id
    print(f"   Analyzing impact for requirement: {first_req_id}")
    impact = perform_impact_analysis(first_req_id)
    if impact.impacted_elements:
        print(f"\n📊 IMPACT ANALYSIS RESULTS for {first_req_id}:")
        print(f"   Impact Severity: {impact.severity}")
        print(f"   Total Impact Weight: {impact.total_impact_weight:.2f}")
        print(f"   Impacted Elements: {len(impact.impacted_elements)}")
        # Show top impacted elements
        for i, element in enumerate(impact.impacted_elements[:3]):
            element_type = element.get('Element_Type', ['Unknown'])[0]
            element_id = element.get('Impacted_Element_ID', 'Unknown')
            print(f"     {i+1}. {element_type}: {element_id}")
    else:
        print(f"   No impact analysis results for {first_req_id}")
    return {"impact_analysis": impact}

def display_comprehensive_packages_for_approval(state: RequirementState):
    """Step 7: Display complete packages with all analysis for approval - ENHANCED WITH SIMILARITY"""
    current_project = state.get("current_project")
    project_name = current_project['name'] if current_project else "Unknown Project"
    project_id = current_project['id'] if current_project else "Unknown"
    print("\n" + "="*80)
    # Check if this is a regeneration
    is_regeneration = state.get("user_feedback") is not None
    regeneration_count = state.get("regeneration_count", 0)
    specific_id = state.get("regenerate_specific_id")
    if is_regeneration:
        if specific_id:
            print(f"🔄 REGENERATED SPECIFIC REQUIREMENT - {specific_id} - ATTEMPT {regeneration_count} - APPROVAL REQUIRED")
        else:
            print(f"🔄 REGENERATED ALL REQUIREMENT PACKAGES - ATTEMPT {regeneration_count} - APPROVAL REQUIRED")
    else:
        print("📋 COMPREHENSIVE REQUIREMENT PACKAGES - APPROVAL REQUIRED")
    print(f"🏢 PROJECT: {project_name} ({project_id})")
    print("="*80)
    # Display stakeholder need
    print(f"\n🎯 STAKEHOLDER NEED: {state['stakeholder_need'].id}")
    print(f"   {state['stakeholder_need'].description}")
    # Display user feedback if this is a regeneration
    if is_regeneration:
        print(f"\n📝 USER FEEDBACK ADDRESSED:")
        print(f"   {state['user_feedback']}")
        if specific_id:
            print(f"   🔄 Target Requirement: {specific_id}")
    # Display shared nodes if any
    if state.get("shared_nodes_found"):
        print(f"\n🔗 SHARED NODES DETECTED ({len(state['shared_nodes_found'])}):")
        for node in state['shared_nodes_found'][:3]:  # Show first 3
            print(f"   • {node['node_id']} - Used by {node['req_count']} requirements")
    # Display dependency analysis if any
    if state.get("dependency_analysis"):
        dep = state["dependency_analysis"]
        print(f"\n⚠️  DEPENDENCY ANALYSIS:")
        print(f"   {dep.requirement_a} ↔ {dep.requirement_b}")
        print(f"   Impact Severity: {dep.impact_severity}")
        print(f"   Connections: {dep.connection_paths}")
        print(f"   Shared Nodes: {', '.join(dep.shared_nodes) if dep.shared_nodes else 'None'}")
        print(f"   Recommendation: {dep.recommendation}")
    # Display impact analysis if any
    if state.get("impact_analysis"):
        impact = state["impact_analysis"]
        print(f"\n📊 IMPACT ANALYSIS:")
        print(f"   Source Requirement: {impact.source_requirement}")
        print(f"   Impact Severity: {impact.severity}")
        print(f"   Total Impact Weight: {impact.total_impact_weight:.2f}")
        print(f"   Impacted Elements: {len(impact.impacted_elements)}")
    # Display each package in detail with similarity information
    for i, pkg in enumerate(state["requirement_packages"], 1):
        print(f"\n" + "─" * 60)
        if is_regeneration:
            if specific_id and pkg.requirement.id == specific_id:
                print(f"🔄 REGENERATED SPECIFIC PACKAGE - {specific_id}")
            else:
                print(f"🔄 REGENERATED PACKAGE {i}")
        else:
            print(f"📦 REQUIREMENT PACKAGE {i}")
        print("─" * 60)
        # Display similarity warnings for critical components
        high_similarity_components = []
        if pkg.stakeholder_need.similarity_info.similarity_score and pkg.stakeholder_need.similarity_info.similarity_score > 0.7:
            high_similarity_components.append(f"StakeholderNeed: {pkg.stakeholder_need.similarity_info.similarity_score:.3f}")
        if pkg.requirement.similarity_info.similarity_score and pkg.requirement.similarity_info.similarity_score > 0.7:
            high_similarity_components.append(f"Requirement: {pkg.requirement.similarity_info.similarity_score:.3f}")
        if pkg.risk.similarity_info.similarity_score and pkg.risk.similarity_info.similarity_score > 0.7:
            high_similarity_components.append(f"Risk: {pkg.risk.similarity_info.similarity_score:.3f}")
        if high_similarity_components:
            print(f"⚠️  HIGH SIMILARITY DETECTED: {', '.join(high_similarity_components)}")
        print(f"\n📋 REQUIREMENT [{pkg.requirement.id}]:")
        print(f"   {pkg.requirement.description}")
        print(f"   Project: {pkg.requirement.project}")
        print(f"   Type: {pkg.requirement.type}")
        print(f"   Priority: {pkg.requirement.priority}")
        print(f"\n🔧 DESIGN SPECIFICATION [{pkg.design_spec.id}]:")
        print(f"   {pkg.design_spec.description}")
        if pkg.design_spec.component:
            print(f"   Component: {pkg.design_spec.component}")
        print(f"\n⚠️  RISK ASSESSMENT [{pkg.risk.id}]:")
        print(f"   {pkg.risk.description}")
        print(f"   Severity: {pkg.risk.severity}")
        print(f"   Probability: {pkg.risk.probability}")
        print(f"\n🛡️  MITIGATION PLAN [{pkg.mitigation.id}]:")
        print(f"   {pkg.mitigation.description}")
        print(f"   Applies to Risk: {pkg.mitigation.applies_to_risk}")
        print(f"\n🧪 TEST CASE [{pkg.test_case.id}]:")
        print(f"   {pkg.test_case.description}")
        print(f"   Test Type: {pkg.test_case.test_type}")
        print(f"   Expected Result: {pkg.test_case.expected_result}")
        print(f"\n🔧 TOOLING REQUIREMENTS [{pkg.tooling.id}]:")
        print(f"   {pkg.tooling.description}")
        print(f"   Tool Type: {pkg.tooling.tool_type}")
        if pkg.tooling.lead_time_days:
            print(f"   Lead Time: {pkg.tooling.lead_time_days} days")
        print(f"\n💰 COST ANALYSIS [{pkg.cost.id}]:")
        print(f"   {pkg.cost.description}")
        print(f"   Estimated Cost: {pkg.cost.estimated_cost} {pkg.cost.currency}")
        if pkg.cost.lifecycle_cost:
            print(f"   Lifecycle Cost: {pkg.cost.lifecycle_cost}")
        print(f"\n🏭 MANUFACTURING PROCESS [{pkg.manufacturing.id}]:")
        print(f"   {pkg.manufacturing.description}")
        print(f"   Process Type: {pkg.manufacturing.process_type}")
        if pkg.manufacturing.cycle_time:
            print(f"   Cycle Time: {pkg.manufacturing.cycle_time}")
        print(f"\n📜 COMPLIANCE REQUIREMENTS [{pkg.compliance.id}]:")
        print(f"   {pkg.compliance.description}")
        print(f"   Standard: {pkg.compliance.standard_name}")
        print(f"   Mandatory: {pkg.compliance.mandatory}")
    # Get user approval with enhanced options including selective regeneration
    while True:
        print("\n" + "="*80)
        if is_regeneration:
            print("🔄 REGENERATION OPTIONS:")
        else:
            print("👉 APPROVAL OPTIONS:")
        print("Available Requirement IDs:", [pkg.requirement.id for pkg in state["requirement_packages"]])
        choice = input("Choose: (yes/no/regenerate/regenerate_specific/impact/dependency): ").strip().lower()
        if choice in ['yes', 'y']:
            return {"approval_status": "approved"}
        elif choice in ['no', 'n']:
            return {"approval_status": "rejected"}
        elif choice in ['regenerate', 'r']:
            # Get user feedback for regeneration of all packages
            print("\n📝 Please provide specific feedback for regeneration of ALL packages:")
            print("   (What didn't you like? What should be improved?)")
            feedback = input("Your feedback: ").strip()
            if not feedback:
                print("❌ Feedback cannot be empty. Please try again.")
                continue
            # Increment regeneration counter
            current_count = state.get("regeneration_count", 0)
            return {
                "approval_status": "regenerate", 
                "user_feedback": feedback,
                "regeneration_count": current_count + 1,
                "regenerate_specific_id": None  # Reset specific ID for full regeneration
            }
        elif choice in ['regenerate_specific', 'rs']:
            # Get specific requirement ID to regenerate
            available_ids = [pkg.requirement.id for pkg in state["requirement_packages"]]
            print(f"\n📝 Available Requirement IDs: {', '.join(available_ids)}")
            req_id = input("Enter the EXACT Requirement ID you want to regenerate: ").strip()
            # Validate the requirement ID exists in current packages
            if req_id not in available_ids:
                print(f"❌ Requirement ID {req_id} not found in current packages.")
                print(f"   Available IDs: {', '.join(available_ids)}")
                continue
            print(f"\n📝 Please provide specific feedback for requirement {req_id}:")
            print("   (What didn't you like? What should be improved?)")
            feedback = input("Your feedback: ").strip()
            if not feedback:
                print("❌ Feedback cannot be empty. Please try again.")
                continue
            # Increment regeneration counter
            current_count = state.get("regeneration_count", 0)
            return {
                "approval_status": "regenerate", 
                "user_feedback": feedback,
                "regeneration_count": current_count + 1,
                "regenerate_specific_id": req_id
            }
        elif choice in ['impact', 'i']:
            # Perform additional impact analysis
            if state["requirement_packages"]:
                req_id = state["requirement_packages"][0].requirement.id
                print(f"\n🔍 Performing detailed impact analysis for {req_id}...")
                impact = perform_impact_analysis(req_id)
                print(f"   Impact Severity: {impact.severity}")
                print(f"   Total Weight: {impact.total_impact_weight:.2f}")
                print(f"   Impacted Elements: {len(impact.impacted_elements)}")
                # Show detailed impacted elements
                if impact.impacted_elements:
                    print(f"\n   DETAILED IMPACTED ELEMENTS:")
                    for i, element in enumerate(impact.impacted_elements[:5]):
                        element_type = element.get('Element_Type', ['Unknown'])[0]
                        element_id = element.get('Impacted_Element_ID', 'Unknown')
                        rel_type = element.get('Relationship_Type', 'Unknown')
                        print(f"     {i+1}. {element_type} [{element_id}] via {rel_type}")
            continue
        elif choice in ['dependency', 'd']:
            # Perform additional dependency analysis
            if state["requirement_packages"] and state.get("existing_requirements"):
                new_req = state["requirement_packages"][0].requirement.id
                existing_req = state["existing_requirements"][0]
                print(f"\n🔗 Performing detailed dependency analysis: {new_req} ↔ {existing_req}")
                analysis = check_requirement_dependency(new_req, existing_req)
                print(f"   Connections: {analysis.connection_paths}")
                print(f"   Impact Severity: {analysis.impact_severity}")
                print(f"   Shared Nodes: {', '.join(analysis.shared_nodes) if analysis.shared_nodes else 'None'}")
                print(f"   Recommendation: {analysis.recommendation}")
            continue
        else:
            print("❌ Please enter 'yes', 'no', 'regenerate', 'regenerate_specific', 'impact', or 'dependency'")

def should_save_to_neo4j(state: RequirementState):
    """Conditional routing based on approval"""
    status = state.get("approval_status")
    if status == "approved":
        return "save_comprehensive_to_neo4j"
    elif status == "regenerate":
        return "generate_comprehensive_requirement_packages"  # Loop back to regenerate
    return END

# Replace the vector index display section in save_comprehensive_to_neo4j function with:
def display_vector_index_info():
    """Display vector index information using SHOW VECTOR INDEXES"""
    try:
        # Use SHOW VECTOR INDEXES (available in Neo4j 5.11+)
        vector_stats_query = "SHOW VECTOR INDEXES"
        vector_stats = neo4j_conn.execute_query(vector_stats_query)
        if vector_stats:
            print(f"\n🔢 VECTOR INDEXES:")
            for vs in vector_stats:
                index_name = vs.get('name', 'Unknown')
                entity_type = vs.get('entityType', 'Unknown')
                labels_or_types = vs.get('labelsOrTypes', ['Unknown'])[0] if vs.get('labelsOrTypes') else 'Unknown'
                dimensions = vs.get('options', {}).get('indexConfig', {}).get('vector.dimensions', 'Unknown')
                print(f"   • {index_name}: {labels_or_types} ({entity_type}), {dimensions} dimensions")
        else:
            print(f"\n🔢 VECTOR INDEXES: No vector indexes found")
            print(f"   ✅ Similarity search will use local embeddings")
    except Exception as e:
        # Fallback: Try to check if our specific indexes exist
        try:
            print(f"\n🔢 VECTOR INDEXES: Using SHOW INDEXES as fallback")
            fallback_query = """
            SHOW INDEXES 
            WHERE name CONTAINS 'similarity' OR type = 'VECTOR'
            YIELD name, type, labelsOrTypes, properties, options
            RETURN name, type, labelsOrTypes
            """
            fallback_results = neo4j_conn.execute_query(fallback_query)
            if fallback_results:
                for idx in fallback_results:
                    print(f"   • {idx['name']}: {idx['labelsOrTypes']} ({idx['type']})")
            else:
                print(f"   ✅ Similarity search will use local embeddings")
        except Exception as e2:
            print(f"\n🔢 VECTOR INDEXES: Using local embeddings for similarity search")
            print(f"   ℹ️  Vector index display not available")
            print(f"   ✅ Similarity functionality is unaffected")

# Call the function
display_vector_index_info()

def save_comprehensive_to_neo4j(state: RequirementState):
    """Step 8: Save complete requirement packages to Neo4j with ALL COMPONENTS AND EMBEDDINGS"""
    current_project = state.get("current_project")
    if not current_project:
        print("❌ No project selected. Cannot save to Neo4j.")
        return {}
    project_id = current_project['id']
    project_name = current_project['name']
    print(f"\n💾 SAVING COMPREHENSIVE REQUIREMENT PACKAGES TO NEO4J FOR PROJECT: {project_name}")
    print("   WITH VECTOR EMBEDDINGS...")
    # Check if this was a regeneration
    is_regeneration = state.get("user_feedback") is not None
    regeneration_count = state.get("regeneration_count", 0)
    specific_id = state.get("regenerate_specific_id")
    if is_regeneration:
        if specific_id:
            print(f"🔄 Saving regenerated specific requirement: {specific_id} (Attempt {regeneration_count})")
        else:
            print(f"🔄 Saving regenerated packages (Attempt {regeneration_count})")
    try:
        # Verify project exists (for existing projects) or create (for new projects)
        if current_project.get('is_new'):
            # Create the project if it's new
            create_query = """
            CREATE (p:Project {
                id: $id,
                name: $name,
                description: $description,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            RETURN p.id
            """
            neo4j_conn.execute_query(create_query, {
                "id": project_id,
                "name": project_name,
                "description": current_project.get('description', f"Project {project_id}"),
                "status": "Active",
                "version": "1.0",
                "created_by": "User",
                "created_on": datetime.utcnow(),
                "last_modified": datetime.utcnow()
            })
            print(f"✓ Created Project: {project_id}")
        else:
            # Verify existing project
            verify_query = "MATCH (p:Project {id: $id}) RETURN p.id"
            result = neo4j_conn.execute_query(verify_query, {"id": project_id})
            if not result:
                print(f"❌ Project {project_id} not found in database")
                return {}
            print(f"✓ Verified existing Project: {project_id}")
        # Create Stakeholder Need with all enhanced fields AND EMBEDDING
        sn = state["stakeholder_need"]
        sn_embedding = embedding_model.embed_query(sn.description)
        query = """
        CREATE (sn:StakeholderNeed {
            id: $id, 
            description: $description, 
            stakeholder: $stakeholder,
            priority: $priority,
            rationale: $rationale,
            status: $status,
            version: $version,
            created_by: $created_by,
            created_on: $created_on,
            last_modified: $last_modified,
            embedding: $embedding,
            similarity_check_performed: $sim_check,
            similarity_score: $sim_score,
            similar_node_id: $sim_node_id,
            similarity_reason: $sim_reason
        })
        RETURN sn.id
        """
        neo4j_conn.execute_query(query, {
            "id": sn.id,
            "description": sn.description,
            "stakeholder": sn.stakeholder,
            "priority": sn.priority.value,
            "rationale": sn.rationale,
            "status": sn.status.value,
            "version": sn.version,
            "created_by": sn.created_by,
            "created_on": sn.created_on,
            "last_modified": sn.last_modified,
            "embedding": sn_embedding,
            "sim_check": sn.similarity_info.similarity_check_performed,
            "sim_score": sn.similarity_info.similarity_score,
            "sim_node_id": sn.similarity_info.similar_node_id,
            "sim_reason": sn.similarity_info.similarity_reason
        })
        print(f"✓ Created StakeholderNeed with embedding: {sn.id}")
        # Create each complete requirement package with ALL components
        requirement_ids = []
        for pkg in state["requirement_packages"]:
            requirement_ids.append(pkg.requirement.id)
            # Generate embeddings for key components
            req_embedding = embedding_model.embed_query(pkg.requirement.description)
            risk_embedding = embedding_model.embed_query(pkg.risk.description)
            comp_embedding = embedding_model.embed_query(pkg.compliance.description)
            ds_embedding = embedding_model.embed_query(pkg.design_spec.description)
            # 1. REQUIREMENT with all enhanced fields AND EMBEDDING
            query = """
            MATCH (sn:StakeholderNeed {id: $sn_id})
            MATCH (p:Project {id: $project_id})
            CREATE (rq:Requirement {
                id: $id, 
                description: $description, 
                project: $project,
                type: $type,
                priority: $priority,
                acceptance_criteria: $acceptance_criteria,
                rationale: $rationale,
                trace_to_stakeholder: $trace_to_stakeholder,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified,
                embedding: $embedding,
                similarity_check_performed: $sim_check,
                similarity_score: $sim_score,
                similar_node_id: $sim_node_id,
                similarity_reason: $sim_reason
            })
            CREATE (rq)-[:SATISFIES {weight: 1.0}]->(sn)
            CREATE (p)-[:HAS_REQUIREMENT {created: datetime()}]->(rq)
            RETURN rq.id
            """
            neo4j_conn.execute_query(query, {
                "sn_id": sn.id,
                "project_id": project_id,
                "id": pkg.requirement.id,
                "description": pkg.requirement.description,
                "project": pkg.requirement.project,
                "type": pkg.requirement.type.value,
                "priority": pkg.requirement.priority.value,
                "acceptance_criteria": pkg.requirement.acceptance_criteria,
                "rationale": pkg.requirement.rationale,
                "trace_to_stakeholder": pkg.requirement.trace_to_stakeholder,
                "status": pkg.requirement.status.value,
                "version": pkg.requirement.version,
                "created_by": pkg.requirement.created_by,
                "created_on": pkg.requirement.created_on,
                "last_modified": pkg.requirement.last_modified,
                "embedding": req_embedding,
                "sim_check": pkg.requirement.similarity_info.similarity_check_performed,
                "sim_score": pkg.requirement.similarity_info.similarity_score,
                "sim_node_id": pkg.requirement.similarity_info.similar_node_id,
                "sim_reason": pkg.requirement.similarity_info.similarity_reason
            })
            if is_regeneration:
                if specific_id and pkg.requirement.id == specific_id:
                    print(f"✓ Created REGENERATED SPECIFIC Requirement with embedding: {pkg.requirement.id}")
                else:
                    print(f"✓ Created REGENERATED Requirement with embedding: {pkg.requirement.id}")
            else:
                print(f"✓ Created Requirement with embedding: {pkg.requirement.id}")
            # 2. DESIGN SPECIFICATION with enhanced fields AND EMBEDDING
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (ds:DesignSpec {
                id: $id, 
                description: $description, 
                component: $component,
                engineering_reference: $engineering_reference,
                feasibility: $feasibility,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified,
                embedding: $embedding,
                similarity_check_performed: $sim_check,
                similarity_score: $sim_score,
                similar_node_id: $sim_node_id,
                similarity_reason: $sim_reason
            })
            CREATE (ds)-[:IMPLEMENTS {weight: 0.8}]->(rq)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.design_spec.id,
                "description": pkg.design_spec.description,
                "component": pkg.design_spec.component,
                "engineering_reference": pkg.design_spec.engineering_reference,
                "feasibility": pkg.design_spec.feasibility,
                "status": pkg.design_spec.status.value,
                "version": pkg.design_spec.version,
                "created_by": pkg.design_spec.created_by,
                "created_on": pkg.design_spec.created_on,
                "last_modified": pkg.design_spec.last_modified,
                "embedding": ds_embedding,
                "sim_check": pkg.design_spec.similarity_info.similarity_check_performed,
                "sim_score": pkg.design_spec.similarity_info.similarity_score,
                "sim_node_id": pkg.design_spec.similarity_info.similar_node_id,
                "sim_reason": pkg.design_spec.similarity_info.similarity_reason
            })
            print(f"✓ Created DesignSpec with embedding: {pkg.design_spec.id}")
            # 3. RISK with enhanced fields AND EMBEDDING
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (rk:Risk {
                id: $id, 
                description: $description, 
                severity: $severity,
                probability: $probability,
                impact: $impact,
                risk_score: $risk_score,
                category: $category,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified,
                embedding: $embedding,
                similarity_check_performed: $sim_check,
                similarity_score: $sim_score,
                similar_node_id: $sim_node_id,
                similarity_reason: $sim_reason
            })
            CREATE (rq)-[:HAS_RISK {severity: $severity, weight: 0.9}]->(rk)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.risk.id,
                "description": pkg.risk.description,
                "severity": pkg.risk.severity.value,
                "probability": pkg.risk.probability.value,
                "impact": pkg.risk.impact.value,
                "risk_score": pkg.risk.risk_score,
                "category": pkg.risk.category,
                "status": pkg.risk.status.value,
                "version": pkg.risk.version,
                "created_by": pkg.risk.created_by,
                "created_on": pkg.risk.created_on,
                "last_modified": pkg.risk.last_modified,
                "embedding": risk_embedding,
                "sim_check": pkg.risk.similarity_info.similarity_check_performed,
                "sim_score": pkg.risk.similarity_info.similarity_score,
                "sim_node_id": pkg.risk.similarity_info.similar_node_id,
                "sim_reason": pkg.risk.similarity_info.similarity_reason
            })
            print(f"✓ Created Risk with embedding: {pkg.risk.id}")
            # 4. MITIGATION with enhanced fields
            query = """
            MATCH (rk:Risk {id: $rk_id})
            CREATE (mt:Mitigation {
                id: $id, 
                description: $description, 
                applies_to_risk: $applies_to_risk,
                effectiveness: $effectiveness,
                implementation_owner: $implementation_owner,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            CREATE (mt)-[:MITIGATES {weight: 0.7}]->(rk)
            """
            neo4j_conn.execute_query(query, {
                "rk_id": pkg.risk.id,
                "id": pkg.mitigation.id,
                "description": pkg.mitigation.description,
                "applies_to_risk": pkg.mitigation.applies_to_risk,
                "effectiveness": pkg.mitigation.effectiveness.value,
                "implementation_owner": pkg.mitigation.implementation_owner,
                "status": pkg.mitigation.status.value,
                "version": pkg.mitigation.version,
                "created_by": pkg.mitigation.created_by,
                "created_on": pkg.mitigation.created_on,
                "last_modified": pkg.mitigation.last_modified
            })
            print(f"✓ Created Mitigation: {pkg.mitigation.id}")
            # 5. TEST CASE with enhanced fields
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (tc:TestCase {
                id: $id, 
                description: $description, 
                test_type: $test_type,
                expected_result: $expected_result,
                test_method: $test_method,
                pass_fail_criteria: $pass_fail_criteria,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            CREATE (tc)-[:VALIDATES {weight: 0.6}]->(rq)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.test_case.id,
                "description": pkg.test_case.description,
                "test_type": pkg.test_case.test_type,
                "expected_result": pkg.test_case.expected_result,
                "test_method": pkg.test_case.test_method,
                "pass_fail_criteria": pkg.test_case.pass_fail_criteria,
                "status": pkg.test_case.status.value,
                "version": pkg.test_case.version,
                "created_by": pkg.test_case.created_by,
                "created_on": pkg.test_case.created_on,
                "last_modified": pkg.test_case.last_modified
            })
            print(f"✓ Created TestCase: {pkg.test_case.id}")
            # 6. TOOLING with enhanced fields
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (tl:Tooling {
                id: $id, 
                description: $description, 
                tool_type: $tool_type,
                lead_time_days: $lead_time_days,
                supplier: $supplier,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            CREATE (rq)-[:REQUIRES_TOOLING {weight: 0.5}]->(tl)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.tooling.id,
                "description": pkg.tooling.description,
                "tool_type": pkg.tooling.tool_type,
                "lead_time_days": pkg.tooling.lead_time_days,
                "supplier": pkg.tooling.supplier,
                "status": pkg.tooling.status.value,
                "version": pkg.tooling.version,
                "created_by": pkg.tooling.created_by,
                "created_on": pkg.tooling.created_on,
                "last_modified": pkg.tooling.last_modified
            })
            print(f"✓ Created Tooling: {pkg.tooling.id}")
            # 7. COST with enhanced fields
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (cf:Cost {
                id: $id, 
                description: $description, 
                estimated_cost: $estimated_cost,
                currency: $currency,
                lifecycle_cost: $lifecycle_cost,
                cost_driver: $cost_driver,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            CREATE (rq)-[:AFFECTS_COST {weight: 0.8}]->(cf)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.cost.id,
                "description": pkg.cost.description,
                "estimated_cost": pkg.cost.estimated_cost,
                "currency": pkg.cost.currency,
                "lifecycle_cost": pkg.cost.lifecycle_cost,
                "cost_driver": pkg.cost.cost_driver,
                "status": pkg.cost.status.value,
                "version": pkg.cost.version,
                "created_by": pkg.cost.created_by,
                "created_on": pkg.cost.created_on,
                "last_modified": pkg.cost.last_modified
            })
            print(f"✓ Created Cost: {pkg.cost.id}")
            # 8. MANUFACTURING with enhanced fields
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (mp:Manufacturing {
                id: $id, 
                description: $description, 
                process_type: $process_type,
                cycle_time: $cycle_time,
                machine_requirement: $machine_requirement,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified
            })
            CREATE (rq)-[:IMPACTS_MANUFACTURING {weight: 0.7}]->(mp)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.manufacturing.id,
                "description": pkg.manufacturing.description,
                "process_type": pkg.manufacturing.process_type,
                "cycle_time": pkg.manufacturing.cycle_time,
                "machine_requirement": pkg.manufacturing.machine_requirement,
                "status": pkg.manufacturing.status.value,
                "version": pkg.manufacturing.version,
                "created_by": pkg.manufacturing.created_by,
                "created_on": pkg.manufacturing.created_on,
                "last_modified": pkg.manufacturing.last_modified
            })
            print(f"✓ Created Manufacturing: {pkg.manufacturing.id}")
            # 9. COMPLIANCE with enhanced fields AND EMBEDDING
            query = """
            MATCH (rq:Requirement {id: $rq_id})
            CREATE (cr:Compliance {
                id: $id, 
                description: $description, 
                standard_name: $standard_name,
                jurisdiction: $jurisdiction,
                mandatory: $mandatory,
                status: $status,
                version: $version,
                created_by: $created_by,
                created_on: $created_on,
                last_modified: $last_modified,
                embedding: $embedding,
                similarity_check_performed: $sim_check,
                similarity_score: $sim_score,
                similar_node_id: $sim_node_id,
                similarity_reason: $sim_reason
            })
            CREATE (rq)-[:REQUIRES_COMPLIANCE {weight: 0.9}]->(cr)
            """
            neo4j_conn.execute_query(query, {
                "rq_id": pkg.requirement.id,
                "id": pkg.compliance.id,
                "description": pkg.compliance.description,
                "standard_name": pkg.compliance.standard_name,
                "jurisdiction": pkg.compliance.jurisdiction,
                "mandatory": pkg.compliance.mandatory,
                "status": pkg.compliance.status.value,
                "version": pkg.compliance.version,
                "created_by": pkg.compliance.created_by,
                "created_on": pkg.compliance.created_on,
                "last_modified": pkg.compliance.last_modified,
                "embedding": comp_embedding,
                "sim_check": pkg.compliance.similarity_info.similarity_check_performed,
                "sim_score": pkg.compliance.similarity_info.similarity_score,
                "sim_node_id": pkg.compliance.similarity_info.similar_node_id,
                "sim_reason": pkg.compliance.similarity_info.similarity_reason
            })
            print(f"✓ Created Compliance with embedding: {pkg.compliance.id}")
        print(f"\n✅ ALL COMPREHENSIVE PACKAGES SAVED SUCCESSFULLY TO PROJECT: {project_name}!")
        print("🔍 View in Neo4j Browser: http://localhost:7474")
        print("📊 All components (TestCase, Tooling, Cost, Manufacturing, Compliance) now properly created")
        print("🔢 Vector embeddings stored for similarity search")
        # Display final statistics for this project
        try:
            stats_query = """
            MATCH (p:Project {id: $project_id})-[:HAS_REQUIREMENT]->(rq)
            WITH p, COUNT(rq) AS requirement_count
            MATCH (p)-[:HAS_REQUIREMENT]->(rq)-[]->(component)
            RETURN p.id AS project_id, p.name AS project_name, 
                   requirement_count,
                   COUNT(DISTINCT component) AS component_count,
                   COLLECT(DISTINCT labels(component)[0]) AS component_types
            """
            stats = neo4j_conn.execute_query(stats_query, {"project_id": project_id})
            if stats:
                stat = stats[0]
                print(f"\n📈 PROJECT STATISTICS for {stat['project_name']}:")
                print(f"   • Requirements: {stat['requirement_count']}")
                print(f"   • Total Components: {stat['component_count']}")
                print(f"   • Component Types: {', '.join(stat['component_types'])}")
        except Exception as e:
            print(f"⚠️  Error displaying project statistics: {e}")
        # Show vector index information using SHOW VECTOR INDEXES
        try:
            print(f"\n🔢 VECTOR INDEXES:")
            vector_stats_query = "SHOW VECTOR INDEXES"
            vector_stats = neo4j_conn.execute_query(vector_stats_query)
            if vector_stats:
                for vs in vector_stats:
                    index_name = vs.get('name', 'Unknown')
                    entity_type = vs.get('entityType', 'Unknown')
                    labels_or_types = vs.get('labelsOrTypes', ['Unknown'])[0] if vs.get('labelsOrTypes') else 'Unknown'
                    dimensions = vs.get('options', {}).get('indexConfig', {}).get('vector.dimensions', 'Unknown')
                    print(f"   • {index_name}: {labels_or_types} ({entity_type}), {dimensions} dimensions")
            else:
                print(f"   • No vector indexes found - using local embeddings for similarity search")
        except Exception as e:
            # Fallback: Try to check if our specific indexes exist using SHOW INDEXES
            try:
                print(f"\n🔢 VECTOR INDEXES (fallback):")
                fallback_query = """
                SHOW INDEXES 
                WHERE name CONTAINS 'similarity' OR type = 'VECTOR'
                YIELD name, type, labelsOrTypes
                RETURN name, type, labelsOrTypes
                """
                fallback_results = neo4j_conn.execute_query(fallback_query)
                if fallback_results:
                    for idx in fallback_results:
                        print(f"   • {idx['name']}: {idx['labelsOrTypes']} ({idx['type']})")
                else:
                    print(f"   • Using local embeddings for similarity search")
            except Exception as e2:
                print(f"   • Vector index display not available - similarity search uses local embeddings")
    except Exception as e:
        print(f"\n❌ Error saving to Neo4j: {e}")
        import traceback
        traceback.print_exc()
    return {}

# =============================================================================
# BUILD COMPREHENSIVE LANGGRAPH
# =============================================================================
def build_comprehensive_graph():
    builder = StateGraph(RequirementState)
    # Add all nodes for comprehensive workflow
    builder.add_node("initialize_workflow", initialize_workflow)
    builder.add_node("generate_keywords", generate_keywords)
    builder.add_node("human_select_keyword", human_select_keyword)
    builder.add_node("generate_stakeholder_need", generate_stakeholder_need)
    builder.add_node("detect_shared_nodes", detect_shared_nodes)
    builder.add_node("generate_comprehensive_requirement_packages", generate_comprehensive_requirement_packages)
    builder.add_node("perform_dependency_analysis", perform_dependency_analysis)
    builder.add_node("perform_impact_analysis_on_new_requirements", perform_impact_analysis_on_new_requirements)
    builder.add_node("display_comprehensive_packages_for_approval", display_comprehensive_packages_for_approval)
    builder.add_node("save_comprehensive_to_neo4j", save_comprehensive_to_neo4j)
    # Build comprehensive workflow
    builder.add_edge(START, "initialize_workflow")
    builder.add_edge("initialize_workflow", "generate_keywords")
    builder.add_edge("generate_keywords", "human_select_keyword")
    builder.add_conditional_edges(
        "human_select_keyword",
        should_continue_to_requirements,
        {
            "generate_stakeholder_need": "generate_stakeholder_need",
            END: END
        }
    )
    builder.add_edge("generate_stakeholder_need", "detect_shared_nodes")
    builder.add_edge("detect_shared_nodes", "generate_comprehensive_requirement_packages")
    builder.add_edge("generate_comprehensive_requirement_packages", "perform_dependency_analysis")
    builder.add_edge("perform_dependency_analysis", "perform_impact_analysis_on_new_requirements")
    builder.add_edge("perform_impact_analysis_on_new_requirements", "display_comprehensive_packages_for_approval")
    builder.add_conditional_edges(
        "display_comprehensive_packages_for_approval",
        should_save_to_neo4j,
        {
            "save_comprehensive_to_neo4j": "save_comprehensive_to_neo4j",
            "generate_comprehensive_requirement_packages": "generate_comprehensive_requirement_packages",  # Regeneration loop
            END: END
        }
    )
    builder.add_edge("save_comprehensive_to_neo4j", END)
    # Compile with memory
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Build and run comprehensive graph
    graph = build_comprehensive_graph()
    thread = {"configurable": {"thread_id": "comprehensive_req_session_1"}}
    # Initialize state - project will be selected in initialize_workflow
    initial_state = {
        "requirement_description": "",
        "keyword_output": None,
        "selected_keyword": None,
        "stakeholder_need": None,
        "requirement_packages": None,
        "approval_status": None,
        "impact_analysis": None,
        "dependency_analysis": None,
        "change_request": None,
        "existing_requirements": None,
        "shared_nodes_found": None,
        "modification_mode": False,
        "target_requirement_id": None,
        "id_counter": None,
        "user_feedback": None,
        "regeneration_count": 0,
        "original_packages": None,
        "regenerate_specific_id": None,
        "current_project": None
    }
    try:
        print("🚀 Starting Comprehensive Requirements Management System with Dynamic Project Selection...")
        for event in graph.stream(initial_state, thread, stream_mode="values"):
            pass  # All output is handled in nodes
        print("\n✅ COMPREHENSIVE WORKFLOW COMPLETED SUCCESSFULLY!")
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ System Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_conn.close()
        print("🔌 Neo4j connection closed")