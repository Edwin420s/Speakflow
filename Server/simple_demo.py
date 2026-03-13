#!/usr/bin/env python3
"""
Simple demo test for SpeakFlow Omi hackathon.
Tests core functionality without complex authentication.
"""

import requests
import json

def test_simple_endpoints():
    """Test the basic functionality of SpeakFlow."""
    
    base_url = "http://localhost:8000"
    
    print("🚀 SpeakFlow Omi Builder Friday Demo")
    print("=" * 50)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Check Passed")
            print(f"   OpenAI: {'✅' if data.get('services', {}).get('openai') else '❌'}")
            print(f"   Trello: {'✅' if data.get('services', {}).get('trello') else '❌'}")
            print(f"   WhatsApp: {'✅' if data.get('services', {}).get('whatsapp') else '❌'}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
    
    print()
    
    # Test Omi endpoints without auth (should work with demo fallback)
    kenyan_transcript = """
    Edwin: Team, let's discuss our fintech app for the Kenyan market. We need proper M-Pesa integration.
    Sarah: I'll handle the UI design for the mobile app. I can have mockups ready by next week.
    John: I should contact KCB and Equity Bank about partnership discussions. Let me schedule that for Tuesday.
    Mary: We need to finalize the API documentation for the developers. Edwin, can you get that done by Friday?
    Edwin: Sure, I'll complete the API docs by Friday. Also, someone needs to register the company name.
    John: I'll take care of the business registration next month after we secure funding.
    """
    
    # Test direct AI processing (bypassing auth for demo)
    try:
        from ai_processor import extract_tasks_and_summary
        result = extract_tasks_and_summary(kenyan_transcript)
        
        print("🧠 AI Processing Test")
        print("-" * 30)
        print(f"✅ Tasks extracted: {len(result.get('tasks', []))}")
        print(f"📝 Summary: {result.get('summary', 'No summary')}")
        
        if result.get('tasks'):
            print("\n📋 Extracted Tasks:")
            for i, task in enumerate(result.get('tasks', []), 1):
                task_text = task.get('task', 'No description')
                assigned = task.get('assigned_to', 'Unassigned')
                deadline = task.get('deadline', 'No deadline')
                priority = task.get('priority', 'medium')
                
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "📌"}.get(priority, "📌")
                
                print(f"  {i}. {priority_emoji} {task_text}")
                if assigned and assigned != 'null':
                    print(f"     👤 {assigned}")
                if deadline and deadline != 'null':
                    print(f"     📅 {deadline}")
        
    except Exception as e:
        print(f"❌ AI processing error: {str(e)}")
    
    print()
    
    # Test Omi integration
    try:
        from omi_integration import get_omi_integration
        omi = get_omi_integration()
        
        print("🎤 Omi Device Integration Test")
        print("-" * 30)
        
        # Test connection
        connected = omi.simulate_omi_connection()
        print(f"✅ Omi Connection: {'Success' if connected else 'Failed'}")
        
        # Test processing
        if connected:
            result = omi.process_conversation_chunk(b"", kenyan_transcript)
            tasks_found = len(result.get('tasks', []))
            print(f"✅ Omi Processing: {tasks_found} tasks extracted")
        
    except Exception as e:
        print(f"❌ Omi integration error: {str(e)}")
    
    print()
    
    # Test WhatsApp formatting
    try:
        from whatsapp_integration import format_whatsapp_summary
        from ai_processor import extract_tasks_and_summary
        
        result = extract_tasks_and_summary(kenyan_transcript)
        formatted_message = format_whatsapp_summary(
            result.get('summary', ''), 
            len(result.get('tasks', [])), 
            result.get('tasks', [])
        )
        
        print("💬 WhatsApp Integration Test")
        print("-" * 30)
        print("✅ WhatsApp message formatted successfully:")
        print(formatted_message[:200] + "..." if len(formatted_message) > 200 else formatted_message)
        
    except Exception as e:
        print(f"❌ WhatsApp formatting error: {str(e)}")
    
    print()
    print("🎉 SpeakFlow Demo Complete!")
    print("🇰🇪 Ready for Omi Builder Friday Hackathon!")
    print("🎤 Turning conversations into productivity with AI!")

if __name__ == "__main__":
    test_simple_endpoints()
