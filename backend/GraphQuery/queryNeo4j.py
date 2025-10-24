"""Complete Fixed Neo4j Graph Query Tool with Proper Answer Formatting."""
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_groq import ChatGroq
from backend.config.config import settings
from collections import Counter
import re

class CompleteGraphQuery:
    def __init__(self, model_name="openai/gpt-oss-120b"):
        self.graph = Neo4jGraph(
            url=settings.neo4j_url,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        self.model_name = model_name
        self.chain = self._initialize_chain()
    
    def _initialize_chain(self):
        return GraphCypherQAChain.from_llm(
            llm=ChatGroq(
                temperature=0,
                model_name=self.model_name,
                groq_api_key=settings.groq_api_key
            ),
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True
        )
    
    def query(self, question):
        """Main query method with comprehensive answer formatting."""
        try:
            # Use the chain but intercept and format the response
            result = self.chain.invoke({"query": question})
            
            # Extract context from intermediate steps
            context = []
            if 'intermediate_steps' in result and result['intermediate_steps']:
                context = result['intermediate_steps'][0].get('context', [])
            
            raw_answer = result.get('result', '')
            
            # If chain says "I don't know" but we have context, format it properly
            if ("I don't know" in raw_answer or "I cannot answer" in raw_answer) and context:
                return self._format_context_based_answer(question, context)
            elif context:
                # Even if we have an answer, make sure it's properly formatted
                return self._enhance_answer_with_context(raw_answer, question, context)
            else:
                return raw_answer
                
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def _format_context_based_answer(self, question, context):
        """Format proper answers based on the context data."""
        question_lower = question.lower()
        
        # Handle project finding queries
        if any(keyword in question_lower for keyword in ['project', 'find project', 'related to']):
            return self._format_project_query_answer(question, context)
        
        # Handle requirement queries
        elif 'requirement' in question_lower:
            return self._format_requirement_query_answer(question, context)
        
        # Handle risk queries
        elif 'risk' in question_lower:
            return self._format_risk_query_answer(question, context)
        
        # Handle count queries
        elif any(keyword in question_lower for keyword in ['how many', 'count', 'number of']):
            return self._format_count_query_answer(question, context)
        
        # Generic formatting for other queries
        else:
            return self._format_generic_answer(context)
    
    def _format_project_query_answer(self, question, context):
        """Format answers for project-related queries."""
        if not context:
            return "No projects found matching your criteria."
        
        # Extract project names from various possible context structures
        projects = set()
        for item in context:
            if 'p.name' in item:
                projects.add(item['p.name'])
            elif 'project' in item:
                projects.add(item['project'])
            elif 'p' in item and isinstance(item['p'], dict) and 'name' in item['p']:
                projects.add(item['p']['name'])
        
        if not projects:
            return "No projects found matching your criteria."
        
        projects_list = list(projects)
        
        # Check if it's a keyword search
        if 'related to' in question.lower() or 'keyword' in question.lower():
            # Extract the search term from question
            search_term = self._extract_search_term(question)
            return f"Projects with requirements related to '{search_term}': {', '.join(projects_list)}"
        else:
            return f"Found projects: {', '.join(projects_list)}"
    
    def _format_requirement_query_answer(self, question, context):
        """Format answers for requirement-related queries."""
        if not context:
            return "No requirements found."
        
        requirements = []
        for item in context:
            if 'r.description' in item:
                requirements.append(item['r.description'])
            elif 'requirement' in item:
                requirements.append(item['requirement'])
            elif 'r' in item and isinstance(item['r'], dict) and 'description' in item['r']:
                requirements.append(item['r']['description'])
        
        if not requirements:
            return "No requirements found matching your criteria."
        
        if len(requirements) == 1:
            return f"Requirement: {requirements[0]}"
        else:
            response = "Requirements found:\n"
            for i, req in enumerate(requirements, 1):
                response += f"{i}. {req}\n"
            return response
    
    def _format_risk_query_answer(self, question, context):
        """Format answers for risk-related queries."""
        if not context:
            return "No risks found."
        
        risks = []
        for item in context:
            if 'risk.description' in item:
                risks.append(item['risk.description'])
            elif 'risk' in item:
                risks.append(item['risk'])
            elif 'rk.description' in item:
                risks.append(item['rk.description'])
        
        if not risks:
            return "No risks found matching your criteria."
        
        if len(risks) == 1:
            return f"Risk: {risks[0]}"
        else:
            response = f"Found {len(risks)} risks:\n"
            for i, risk in enumerate(risks, 1):
                response += f"{i}. {risk}\n"
            return response
    
    def _format_count_query_answer(self, question, context):
        """Format answers for count-related queries."""
        if not context:
            return "No data found for counting."
        
        # Look for count fields in context
        for item in context:
            for key, value in item.items():
                if 'count' in key.lower():
                    return f"Total count: {value}"
        
        # If no count field, count the items
        return f"Found {len(context)} items matching your query."
    
    def _format_generic_answer(self, context):
        """Generic formatting for any context data."""
        if not context:
            return "No data found."
        
        # Try to extract meaningful information
        all_data = []
        for item in context:
            for key, value in item.items():
                if key not in ['id', '_id'] and not key.startswith('_'):
                    if isinstance(value, (str, int, float)):
                        all_data.append(f"{key}: {value}")
        
        if all_data:
            return "Found data:\n" + "\n".join(all_data[:10])  # Limit output
        else:
            return f"Found {len(context)} records matching your query."
    
    def _extract_search_term(self, question):
        """Extract search term from question."""
        # Look for phrases like "related to X", "about X", "containing X"
        patterns = [
            r"related to ['\"]([^'\"]+)['\"]",
            r"related to (\w+)",
            r"about ['\"]([^'\"]+)['\"]",
            r"about (\w+)",
            r"containing ['\"]([^'\"]+)['\"]",
            r"containing (\w+)",
            r"keyword ['\"]([^'\"]+)['\"]",
            r"keyword (\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question.lower())
            if match:
                return match.group(1)
        
        # Fallback: return the last word or a generic term
        words = question.split()
        if len(words) > 1:
            return words[-1].strip('?.!')
        
        return "your search term"
    
    def _enhance_answer_with_context(self, raw_answer, question, context):
        """Enhance the raw answer with context information."""
        # If the raw answer is already good, use it
        if raw_answer and len(raw_answer) > 10 and "I don't know" not in raw_answer:
            return raw_answer
        
        # Otherwise format from context
        return self._format_context_based_answer(question, context)

    # Specialized query methods for common use cases
    def find_projects_by_keyword(self, keyword):
        """Find projects by keyword in requirements."""
        query = """
        MATCH (p:Project)-[:HAS_REQUIREMENT]->(r:Requirement)
        WHERE toLower(r.description) CONTAINS toLower($keyword)
        RETURN DISTINCT p.name AS project_name, 
               p.keyword AS project_keyword,
               r.description AS matching_requirement
        ORDER BY p.name
        """
        result = self.graph.query(query, {"keyword": keyword})
        return result
    
    def get_project_requirements(self, project_name):
        """Get all requirements for a specific project."""
        query = """
        MATCH (p:Project {name: $project_name})-[:HAS_REQUIREMENT]->(r:Requirement)
        RETURN r.description AS requirement, r.index AS index
        ORDER BY r.index
        """
        result = self.graph.query(query, {"project_name": project_name})
        return result
    
    def get_requirements_with_risks(self, project_name):
        """Get requirements and their associated risks for a project."""
        query = """
        MATCH (p:Project {name: $project_name})-[:HAS_REQUIREMENT]->(r:Requirement)-[:HAS_RISK]->(rk:Risk)
        RETURN r.description AS requirement, 
               r.index AS req_index,
               rk.description AS risk,
               rk.index AS risk_index
        ORDER BY r.index, rk.index
        """
        result = self.graph.query(query, {"project_name": project_name})
        return result

def interactive_query_tool():
    """Interactive tool with complete answer formatting."""
    query_tool = CompleteGraphQuery()
    
    # Get all projects first
    projects_result = query_tool.graph.query("MATCH (p:Project) RETURN p.name AS project_name")
    project_names = [project['project_name'] for project in projects_result]
    
    print("🔍 Complete Neo4j Graph Query Tool")
    print("=" * 60)
    print(f"📂 Available projects: {', '.join(project_names)}")
    
    sample_queries = [
        "Find projects that have requirements related to fuel",
        "What are all the projects in the database?",
        "Show me all requirements for project_6375b7af",
        "What risks are associated with project_6375b7af?",
        "How many requirements does each project have?",
        "Which projects have the most risks?",
        "Show me the riskiest requirements across all projects",
        "What are the common risks across different projects?",
        "Find projects with requirements about manufacturing",
        "Get requirements containing technology"
    ]
    
    while True:
        print("\n📝 Sample questions you can ask:")
        for i, query in enumerate(sample_queries, 1):
            print(f"{i}. {query}")
        
        print(f"\n💡 Tip: Try these specific project names: {', '.join(project_names[:3])}")
        print("\nEnter your question (or 'quit' to exit):")
        user_question = input("> ").strip()
        
        if user_question.lower() in ['quit', 'exit', 'q']:
            break
            
        if user_question:
            try:
                print(f"\n🤔 Query: {user_question}")
                print("⏳ Processing...")
                
                result = query_tool.query(user_question)
                
                print(f"\n✅ Answer:")
                print(result)
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        else:
            print("Please enter a valid question.")

def demonstrate_fixed_queries():
    """Demonstrate that the fixed queries work properly."""
    query_tool = CompleteGraphQuery()
    
    test_queries = [
        "Find projects that have requirements related to fuel",
        "What are all the projects in the database?",
        "How many requirements does LangGraph_Adoption_2025 have?",
        "Show me risks for project_6375b7af"
    ]
    
    print("🧪 Testing Fixed Query System")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        print("-" * 40)
        result = query_tool.query(query)
        print(f"Result: {result}")
        print("-" * 40)

if __name__ == "__main__":
    # Demonstrate that the fixes work
    demonstrate_fixed_queries()
    
    # Run the interactive tool
    interactive_query_tool()