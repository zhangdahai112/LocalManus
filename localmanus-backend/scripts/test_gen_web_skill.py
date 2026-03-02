#!/usr/bin/env python3
"""
Test script for gen-web skill with new sandbox integration
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from skills.gen_web.gen_web import GenWebSkill

async def test_gen_web_skill():
    """Test the gen-web skill methods"""
    print("\n" + "="*60)
    print("Testing gen-web Skill with Sandbox Integration")
    print("="*60)
    
    skill = GenWebSkill()
    user_id = "test_gen_web_user"
    
    try:
        # Test 1: Get sandbox info
        print("\n✓ Test 1: Get Sandbox Info")
        result = await skill.get_sandbox_info(user_id=user_id)
        print(f"Result: {result.content[0].text[:300]}...")
        
        # Test 2: List files in home directory
        print("\n✓ Test 2: List Files in Home Directory")
        from core.firecracker_sandbox import sandbox_manager
        sandbox_info = sandbox_manager.get_sandbox(user_id)
        result = await skill.list_files(directory=sandbox_info.home_dir, user_id=user_id)
        print(f"Result: {result.content[0].text[:300]}...")
        
        # Test 3: Run shell command
        print("\n✓ Test 3: Run Shell Command")
        result = await skill.run_shell_command(command="node --version && npm --version", user_id=user_id)
        print(f"Result: {result.content[0].text}")
        
        # Test 4: Write and read file
        print("\n✓ Test 4: Write and Read File")
        test_file = f"{sandbox_info.home_dir}/test_gen_web.txt"
        write_result = await skill.write_file(
            file_path=test_file,
            content="Hello from gen-web skill test!",
            user_id=user_id
        )
        print(f"Write: {write_result.content[0].text}")
        
        read_result = await skill.read_file(file_path=test_file, user_id=user_id)
        print(f"Read: {read_result.content[0].text[:200]}...")
        
        # Test 5: Create a small project (optional, takes longer)
        create_project = input("\n\nCreate a test React project? (y/n): ").lower() == 'y'
        
        if create_project:
            print("\n✓ Test 5: Create Full-Stack Project")
            result = await skill.create_fullstack_project(
                project_name="test-react-app",
                tech_stack="React",
                user_id=user_id
            )
            print(f"Result:\n{result.content[0].text}")
            
            # Test 6: Start dev server (optional)
            start_server = input("\nStart development server? (y/n): ").lower() == 'y'
            if start_server:
                print("\n✓ Test 6: Start Development Server")
                result = await skill.start_dev_server(
                    project_dir=f"{sandbox_info.home_dir}/test-react-app",
                    user_id=user_id,
                    port=3000
                )
                print(f"Result:\n{result.content[0].text}")
        
        print("\n" + "="*60)
        print("All Tests Completed Successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gen_web_skill())
