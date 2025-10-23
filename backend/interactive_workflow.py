import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class RequirementsWorkflow:
    def __init__(self):
        self.thread_id: Optional[str] = None
        self.keywords = []
        self.selected_keyword = None
    
    def create_project(self):
        """Step 1: Create project and generate keywords."""
        print("\n" + "=" * 80)
        print("🚀 REQUIREMENTS MANAGEMENT WORKFLOW")
        print("=" * 80)
        
        requirement_desc = input("\n📝 Enter requirement description: ").strip()
        if not requirement_desc:
            requirement_desc = "The benefits of adopting LangGraph as an agent framework"
            print(f"Using default: {requirement_desc}")
        
        project_name = input("📁 Enter project name (or press Enter for auto-generated): ").strip()
        
        payload = {"requirement_description": requirement_desc}
        if project_name:
            payload["project_name"] = project_name
        
        print("\n⏳ Generating keywords...")
        response = requests.post(f"{BASE_URL}/project/create", json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        data = response.json()
        self.thread_id = data["thread_id"]
        self.keywords = data["keywords"]
        
        print(f"\n✅ Project Created: {self.thread_id}")
        print(f"\n📋 Generated Keywords:")
        for i, kw in enumerate(self.keywords):
            print(f"  {i}. {kw}")
        
        return True
    
    def select_keyword(self):
        """Step 2: Select keyword and generate requirements/risks."""
        print("\n" + "=" * 80)
        print("🔑 KEYWORD SELECTION")
        print("=" * 80)
        
        while True:
            try:
                choice = input(f"\nSelect keyword (0-{len(self.keywords)-1}): ").strip()
                keyword_index = int(choice)
                
                if 0 <= keyword_index < len(self.keywords):
                    break
                else:
                    print(f"❌ Please enter a number between 0 and {len(self.keywords)-1}")
            except ValueError:
                print("❌ Please enter a valid number")
        
        print("\n⏳ Generating requirements and risks...")
        response = requests.post(
            f"{BASE_URL}/project/select-keyword",
            json={"thread_id": self.thread_id, "keyword_index": keyword_index}
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        data = response.json()
        self.selected_keyword = data["selected_keyword"]
        
        print(f"\n✅ Selected: {self.selected_keyword}")
        print(f"\n📝 Requirements:")
        for i, req in enumerate(data['requirements'], 1):
            print(f"\n  {i}. {req}")
        
        print(f"\n⚠️  Risks:")
        for i, risk in enumerate(data['risks'], 1):
            print(f"\n  {i}. {risk}")
        
        return True
    
    def regenerate_option(self):
        """Step 3: Optional regeneration."""
        print("\n" + "=" * 80)
        print("🔄 REGENERATION OPTIONS")
        print("=" * 80)
        
        print("\n1. Regenerate requirements")
        print("2. Regenerate risks")
        print("3. Regenerate both")
        print("4. Skip (proceed to save)")
        
        choice = input("\nYour choice (1-4): ").strip()
        
        regen_map = {
            "1": "requirements",
            "2": "risks",
            "3": "both",
            "4": None
        }
        
        regenerate_type = regen_map.get(choice)
        
        if not regenerate_type:
            return True
        
        print(f"\n⏳ Regenerating {regenerate_type}...")
        response = requests.post(
            f"{BASE_URL}/project/regenerate",
            json={"thread_id": self.thread_id, "regenerate_type": regenerate_type}
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        data = response.json()
        
        if regenerate_type in ['requirements', 'both']:
            print(f"\n📝 New Requirements:")
            for i, req in enumerate(data['requirements'], 1):
                print(f"\n  {i}. {req}")
        
        if regenerate_type in ['risks', 'both']:
            print(f"\n⚠️  New Risks:")
            for i, risk in enumerate(data['risks'], 1):
                print(f"\n  {i}. {risk}")
        
        # Ask if they want to regenerate again
        again = input("\n🔄 Regenerate again? (y/n): ").strip().lower()
        if again == 'y':
            return self.regenerate_option()
        
        return True
    
    def save_project(self):
        """Step 4: Save to Neo4j."""
        print("\n" + "=" * 80)
        print("💾 SAVING TO NEO4J")
        print("=" * 80)
        
        confirm = input("\n⚠️  Save to database? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Save cancelled")
            return False
        
        print("\n⏳ Saving to Neo4j...")
        response = requests.post(
            f"{BASE_URL}/project/save",
            params={"thread_id": self.thread_id}
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        print("\n✅ Successfully saved to Neo4j!")
        return True
    
    def run(self):
        """Run the complete workflow."""
        if not self.create_project():
            return
        
        if not self.select_keyword():
            return
        
        if not self.regenerate_option():
            return
        
        self.save_project()
        
        print("\n" + "=" * 80)
        print("🎉 WORKFLOW COMPLETE!")
        print("=" * 80)
        print(f"\n✅ Project ID: {self.thread_id}")
        print(f"✅ Keyword: {self.selected_keyword}")
        print(f"✅ Data saved to Neo4j")

if __name__ == "__main__":
    workflow = RequirementsWorkflow()
    try:
        workflow.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")