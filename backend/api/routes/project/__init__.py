"""Project routes package."""
from api.routes.project.creation import router as creation_router
from api.routes.project.regeneration import router as regeneration_router
from api.routes.project.saving import router as saving_router
from api.routes.project.risks import router as risks_router
from api.routes.project.neo4j_operations import router as neo4j_router
from api.routes.project.state_management import router as state_router
from api.routes.project.projects import router as project_router

# Combine all project routers
routers = [
    creation_router,
    regeneration_router,
    saving_router,
    risks_router,
    neo4j_router,
    state_router,
    creation_router,
    project_router
]