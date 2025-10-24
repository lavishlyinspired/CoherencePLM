# backend/traceability/schema.py
from backend.config.config import settings

class TraceabilitySchema:
    @staticmethod
    def create_schema(driver):
        """
        Create traceability graph schema with proper relationships
        """
        constraints = [
            "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT testcase_id IF NOT EXISTS FOR (tc:TestCase) REQUIRE tc.id IS UNIQUE",
            "CREATE CONSTRAINT risk_id IF NOT EXISTS FOR (risk:Risk) REQUIRE risk.id IS UNIQUE",
            "CREATE CONSTRAINT design_id IF NOT EXISTS FOR (d:Design) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT stakeholder_id IF NOT EXISTS FOR (sn:StakeholderNeed) REQUIRE sn.id IS UNIQUE"
        ]

        with driver.session(database=settings.neo4j_database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")

    @staticmethod
    def create_sample_data(driver):
        """
        Create sample traceability data for demonstration
        """
        sample_queries = [
            # Create Projects
            """
            MERGE (p1:Project {id: 'project_1', name: 'E-Commerce Platform', description: 'Online shopping platform'})
            MERGE (p2:Project {id: 'project_2', name: 'Mobile Banking App', description: 'Mobile banking application'})
            """,

            # Create Requirements
            """
            MERGE (r1:Requirement {id: 'REQ_001', description: 'User must be able to login with email and password', priority: 'High'})
            MERGE (r2:Requirement {id: 'REQ_002', description: 'System shall allow password reset via email', priority: 'Medium'})
            MERGE (r3:Requirement {id: 'REQ_003', description: 'User session shall expire after 30 minutes of inactivity', priority: 'High'})
            """,

            # Create Test Cases
            """
            MERGE (tc1:TestCase {id: 'TC_001', description: 'Verify successful login with valid credentials', test_type: 'Functional', steps: ['Navigate to login page', 'Enter valid email', 'Enter valid password', 'Click login'], expected_result: 'User is redirected to dashboard'})
            MERGE (tc2:TestCase {id: 'TC_002', description: 'Verify login fails with invalid password', test_type: 'Functional', steps: ['Navigate to login page', 'Enter valid email', 'Enter invalid password', 'Click login'], expected_result: 'Error message is displayed'})
            MERGE (tc3:TestCase {id: 'TC_003', description: 'Verify password reset functionality', test_type: 'Functional', steps: ['Click forgot password', 'Enter email address', 'Check email for reset link', 'Set new password'], expected_result: 'Password is successfully reset'})
            """,

            # Create Risks
            """
            MERGE (risk1:Risk {id: 'RISK_001', description: 'Weak password policy may lead to security breaches', severity: 'High', mitigation: 'Implement strong password complexity requirements'})
            MERGE (risk2:Risk {id: 'RISK_002', description: 'Session timeout too short may frustrate users', severity: 'Medium', mitigation: 'Provide warning before session expiration'})
            MERGE (risk3:Risk {id: 'RISK_003', description: 'Password reset process vulnerable to email interception', severity: 'High', mitigation: 'Implement multi-factor authentication for sensitive operations'})
            """,

            # Create Relationships
            """
            // Project to Requirements
            MATCH (p:Project {id: 'project_1'}), (r1:Requirement {id: 'REQ_001'}), (r2:Requirement {id: 'REQ_002'}), (r3:Requirement {id: 'REQ_003'})
            MERGE (p)-[:HAS_REQUIREMENT]->(r1)
            MERGE (p)-[:HAS_REQUIREMENT]->(r2)
            MERGE (p)-[:HAS_REQUIREMENT]->(r3)

            // Requirements to Test Cases
            MATCH (r1:Requirement {id: 'REQ_001'}), (tc1:TestCase {id: 'TC_001'}), (tc2:TestCase {id: 'TC_002'})
            MATCH (r2:Requirement {id: 'REQ_002'}), (tc3:TestCase {id: 'TC_003'})
            MERGE (r1)-[:VERIFIED_BY]->(tc1)
            MERGE (r1)-[:VERIFIED_BY]->(tc2)
            MERGE (r2)-[:VERIFIED_BY]->(tc3)

            // Requirements to Risks
            MATCH (r1:Requirement {id: 'REQ_001'}), (risk1:Risk {id: 'RISK_001'})
            MATCH (r3:Requirement {id: 'REQ_003'}), (risk2:Risk {id: 'RISK_002'})
            MATCH (r2:Requirement {id: 'REQ_002'}), (risk3:Risk {id: 'RISK_003'})
            MERGE (r1)-[:HAS_RISK]->(risk1)
            MERGE (r3)-[:HAS_RISK]->(risk2)
            MERGE (r2)-[:HAS_RISK]->(risk3)
            """
        ]

        with driver.session(database=settings.neo4j_database) as session:
            for query in sample_queries:
                try:
                    session.run(query)
                except Exception as e:
                    logger.error(f"Error executing sample data query: {e}")
