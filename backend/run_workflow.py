import requests
import json

BASE_URL = "http://localhost:8000"

def run_complete_workflow():
    """Run the complete requirements management workflow."""
    
    # Step 1: Create project and generate keywords
    print("=" * 80)
    print("STEP 1: Creating Project and Generating Keywords")
    print("=" * 80)
    
    create_response = requests.post(
        f"{BASE_URL}/project/create",
        json={
            "requirement_description": "The benefits of adopting LangGraph as an agent framework for building complex AI applications with state management and tool calling",
            "project_name": "LangGraph_Adoption_2025"
        }
    )
    
    if create_response.status_code != 200:
        print(f"❌ Error: {create_response.text}")
        return
    
    data = create_response.json()
    thread_id = data["thread_id"]
    keywords = data["keywords"]
    
    print(f"✅ Project Created: {thread_id}")
    print(f"\n📋 Generated Keywords:")
    for i, kw in enumerate(keywords):
        print(f"  {i}. {kw}")
    
    # Step 2: Select a keyword
    print("\n" + "=" * 80)
    print("STEP 2: Selecting Keyword")
    print("=" * 80)
    
    # Automatically select the first keyword (index 0)
    # Or prompt user: keyword_index = int(input("\nSelect keyword (0-4): "))
    keyword_index = 0
    
    select_response = requests.post(
        f"{BASE_URL}/project/select-keyword",
        json={
            "thread_id": thread_id,
            "keyword_index": keyword_index
        }
    )
    
    if select_response.status_code != 200:
        print(f"❌ Error: {select_response.text}")
        return
    
    data = select_response.json()
    print(f"✅ Selected Keyword: {data['selected_keyword']}")
    
    print(f"\n📝 Generated Requirements:")
    for i, req in enumerate(data['requirements'], 1):
        print(f"  {i}. {req}")
    
    print(f"\n⚠️  Generated Risks:")
    for i, risk in enumerate(data['risks'], 1):
        print(f"  {i}. {risk}")
    
    # Step 3: Optional - Regenerate if needed
    print("\n" + "=" * 80)
    print("STEP 3 (Optional): Regeneration")
    print("=" * 80)
    
    regenerate = input("\nWould you like to regenerate? (requirements/risks/both/no): ").strip().lower()
    
    if regenerate in ['requirements', 'risks', 'both']:
        print(f"\n🔄 Regenerating {regenerate}...")
        
        regen_response = requests.post(
            f"{BASE_URL}/project/regenerate",
            json={
                "thread_id": thread_id,
                "regenerate_type": regenerate
            }
        )
        
        if regen_response.status_code != 200:
            print(f"❌ Error: {regen_response.text}")
            return
        
        data = regen_response.json()
        
        if regenerate in ['requirements', 'both']:
            print(f"\n📝 Regenerated Requirements:")
            for i, req in enumerate(data['requirements'], 1):
                print(f"  {i}. {req}")
        
        if regenerate in ['risks', 'both']:
            print(f"\n⚠️  Regenerated Risks:")
            for i, risk in enumerate(data['risks'], 1):
                print(f"  {i}. {risk}")
    
    # Step 4: Save to Neo4j
    print("\n" + "=" * 80)
    print("STEP 4: Saving to Neo4j")
    print("=" * 80)
    
    save_response = requests.post(
        f"{BASE_URL}/project/save",
        params={"thread_id": thread_id}
    )
    
    if save_response.status_code != 200:
        print(f"❌ Error: {save_response.text}")
        return
    
    print("✅ Successfully saved to Neo4j!")
    
    # Get final project status
    print("\n" + "=" * 80)
    print("FINAL PROJECT STATUS")
    print("=" * 80)
    
    status_response = requests.get(f"{BASE_URL}/project/{thread_id}")
    final_data = status_response.json()
    
    print(f"\n🎯 Project: {final_data['thread_id']}")
    print(f"📊 Status: {final_data['status']}")
    print(f"🔑 Selected Keyword: {final_data['selected_keyword']}")
    print(f"📝 Requirements: {len(final_data['requirements'])} generated")
    print(f"⚠️  Risks: {len(final_data['risks'])} identified")
    
    print("\n" + "=" * 80)
    print("✅ WORKFLOW COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_complete_workflow()
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")