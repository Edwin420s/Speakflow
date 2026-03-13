#!/usr/bin/env python3
"""
Demo script for SpeakFlow with realistic Kenyan business meeting scenarios.
Perfect for Omi Builder Friday hackathon demonstrations.
"""

import requests
import json
import time
import sys

# Demo scenarios for Kenyan business context
DEMO_SCENARIOS = [
    {
        "name": "Tech Startup Planning",
        "transcript": """
Edwin: Alright team, let's discuss our fintech app for the Kenyan market. We need to integrate M-Pesa properly.
Sarah: I'll handle the UI design for the mobile app. I can have the mockups ready by next week.
John: I should contact KCB and Equity Bank about partnership discussions. Let me schedule that for Tuesday.
Mary: We need to finalize the API documentation for the developers. Edwin, can you get that done by Friday?
Edwin: Sure, I'll complete the API docs by Friday. Also, someone needs to register the company name with the registrar.
John: I'll take care of the business registration next month after we secure funding.
Sarah: Don't forget we need to test the app on Safaricom's network before launch.
Mary: Right, I'll coordinate with the Safaricom developer team for testing access.
        """,
        "expected_tasks": 6
    },
    {
        "name": "E-commerce Business Meeting",
        "transcript": """
David: Our online marketplace for local artisans needs improvement. The payment gateway is causing issues.
Grace: I'll fix the M-Pesa integration bugs by tomorrow. The checkout process needs to be smoother.
Sam: We should add more product categories for Kenyan handicrafts. I'll research this by end of week.
Faith: The delivery logistics in Nairobi need optimization. I'll contact Sendy for partnership next week.
David: Good idea. Also, we need to photograph more products for the website. Grace, can you coordinate with photographers?
Grace: Yes, I'll schedule product shoots for next month. We need at least 50 new products listed.
Sam: I'll update the inventory system to handle the new categories. That should be done by Friday.
Faith: Let's also expand to Mombasa market. I'll research delivery partners there by end of month.
        """,
        "expected_tasks": 6
    },
    {
        "name": "Agricultural Tech Planning",
        "transcript": """
Joseph: Our farm management app for smallholder farmers is gaining traction. What are our priorities?
Esther: The weather integration system needs work. I'll fix the rainfall data API by next week.
Peter: We should add support for local languages. I'll implement Swahili and Kikuyu interfaces this month.
Alice: The farmer registration process is too complicated. I'll simplify it by Friday.
Joseph: Great. Also, someone needs to present at the agricultural summit next month in Kisumu.
Peter: I'll prepare the presentation and travel arrangements. The summit is crucial for user acquisition.
Esther: Don't forget we need to integrate with Kenya Seed Company's catalog. I'll start those discussions next week.
Alice: I'll test the app with farmers in Nakuru county this weekend to get feedback.
        """,
        "expected_tasks": 5
    },
    {
        "name": "Healthcare Startup Sync",
        "transcript": """
Dr. Kamau: Our telemedicine platform for rural Kenya needs urgent improvements. Patient data security is critical.
Lucy: I'll update the encryption protocols by tomorrow. We need to comply with Kenya's data protection laws.
Tom: The appointment booking system is failing frequently. I'll debug and fix it by Friday.
Nancy: We should partner with more hospitals in Western Kenya. I'll contact Moi Teaching and Referral Hospital next week.
Dr. Kamau: Excellent. Also, we need to add prescription tracking functionality.
Lucy: I'll design the prescription module by end of month. Integration with pharmacies will be key.
Tom: The mobile app crashes on older Android phones. I'll optimize performance this week.
Nancy: I'll create user training materials for community health workers. That should be ready in two weeks.
        """,
        "expected_tasks": 6
    }
]

def test_api_endpoint(base_url="http://localhost:8000", api_key=None):
    """Test the SpeakFlow API with demo scenarios."""
    
    if not api_key:
        print("❌ No API key provided. Use default demo key...")
        api_key = "sk-demo-key-omi-hackathon"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🚀 Starting SpeakFlow Demo for Omi Builder Friday")
    print("=" * 60)
    
    for i, scenario in enumerate(DEMO_SCENARIOS, 1):
        print(f"\n📱 Scenario {i}: {scenario['name']}")
        print("-" * 40)
        
        payload = {"text": scenario["transcript"]}
        
        try:
            response = requests.post(
                f"{base_url}/api/analyze",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                tasks = result.get("tasks", [])
                summary = result.get("summary", "")
                
                print(f"✅ Success! Extracted {len(tasks)} tasks")
                print(f"📝 Summary: {summary}")
                
                if tasks:
                    print("\n📋 Action Items:")
                    for j, task in enumerate(tasks, 1):
                        task_text = task.get("task", "No description")
                        assigned = task.get("assigned_to", "Unassigned")
                        deadline = task.get("deadline", "No deadline")
                        priority = task.get("priority", "medium")
                        
                        priority_emoji = {"high": "🔥", "medium": "⚡", "low": "📌"}.get(priority, "📌")
                        
                        print(f"  {j}. {priority_emoji} {task_text}")
                        if assigned and assigned != 'null':
                            print(f"     👤 {assigned}")
                        if deadline and deadline != 'null':
                            print(f"     📅 {deadline}")
                
                # Check if we got expected number of tasks
                if len(tasks) >= scenario["expected_tasks"] - 2:  # Allow some flexibility
                    print(f"✅ Task extraction working well ({len(tasks)}/{scenario['expected_tasks']} expected)")
                else:
                    print(f"⚠️  Fewer tasks than expected ({len(tasks)}/{scenario['expected_tasks']})")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout - API might be slow")
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - is the API running?")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
        
        # Small delay between scenarios
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed! This is SpeakFlow turning conversations into productivity!")
    print("🇰🇪 Perfect for Kenyan businesses and the Omi AI wearable")
    print("🚀 Ready for Omi Builder Friday hackathon!")

def test_health_check(base_url="http://localhost:8000"):
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Health Check Passed")
            print(f"   OpenAI: {'✅' if data.get('services', {}).get('openai') else '❌'}")
            print(f"   Trello: {'✅' if data.get('services', {}).get('trello') else '❌'}")
            print(f"   WhatsApp: {'✅' if data.get('services', {}).get('whatsapp') else '❌'}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🔍 Testing API health...")
    if test_health_check(base_url):
        test_api_endpoint(base_url, api_key)
    else:
        print("❌ API is not healthy. Please check the server.")
