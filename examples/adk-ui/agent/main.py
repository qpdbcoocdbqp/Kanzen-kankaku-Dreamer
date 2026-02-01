"""Structured Data Generation Agent."""

from __future__ import annotations

import json
from typing import Dict, Any, Optional

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import ToolContext
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


class StructuredDataState(BaseModel):
    """State for structured data generation."""

    structuredData: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The current structured data object",
    )
    lastOutput: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The last generated output",
    )


def set_structured_data(tool_context: ToolContext, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Set structured data in the agent state.

    Args:
        "data": {
            "type": "object",
            "description": "The structured data object to store",
        }

    Returns:
        Dict indicating success status and message
    """
    try:
        tool_context.state["structuredData"] = data
        tool_context.state["lastOutput"] = data
        return {"status": "success", "message": "Structured data updated successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Error updating structured data: {str(e)}"}


def generate_sample_data(tool_context: ToolContext, data_type: str) -> Dict[str, Any]:
    """
    Generate sample structured data of a specific type.
    
    Args:
        "data_type": {
            "type": "string",
            "description": "Type of data to generate (e.g., 'user_profile', 'product', 'order', 'company')",
        }
    
    Returns:
        Dict containing the generated sample data
    """
    sample_data = {}
    
    if data_type.lower() == "user_profile":
        sample_data = {
            "id": "user_12345",
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "age": 28,
            "location": {
                "city": "San Francisco",
                "country": "USA",
                "timezone": "PST"
            },
            "preferences": {
                "theme": "dark",
                "language": "en",
                "notifications": True
            },
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": "2024-01-27T14:22:00Z"
        }
    elif data_type.lower() == "product":
        sample_data = {
            "id": "prod_67890",
            "name": "Wireless Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": 199.99,
            "currency": "USD",
            "category": "Electronics",
            "tags": ["audio", "wireless", "noise-cancelling"],
            "specifications": {
                "battery_life": "30 hours",
                "connectivity": "Bluetooth 5.0",
                "weight": "250g"
            },
            "in_stock": True,
            "stock_quantity": 150
        }
    elif data_type.lower() == "order":
        sample_data = {
            "order_id": "ORD-2024-001",
            "customer_id": "user_12345",
            "items": [
                {
                    "product_id": "prod_67890",
                    "name": "Wireless Headphones",
                    "quantity": 1,
                    "price": 199.99
                }
            ],
            "total_amount": 199.99,
            "currency": "USD",
            "status": "processing",
            "shipping_address": {
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
                "country": "USA"
            },
            "created_at": "2024-01-27T15:00:00Z"
        }
    elif data_type.lower() == "company":
        sample_data = {
            "company_id": "comp_456",
            "name": "TechCorp Solutions",
            "industry": "Software Development",
            "founded": 2018,
            "employees": 250,
            "headquarters": {
                "city": "Austin",
                "state": "TX",
                "country": "USA"
            },
            "revenue": {
                "amount": 50000000,
                "currency": "USD",
                "year": 2023
            },
            "technologies": ["Python", "React", "AWS", "Docker"],
            "contact": {
                "email": "info@techcorp.com",
                "phone": "+1-555-0123",
                "website": "https://techcorp.com"
            }
        }
    else:
        sample_data = {
            "type": data_type,
            "message": f"Sample data for {data_type}",
            "generated_at": "2024-01-27T15:00:00Z",
            "data": {
                "field1": "value1",
                "field2": "value2",
                "field3": 123
            }
        }
    
    # Store in state
    tool_context.state["structuredData"] = sample_data
    tool_context.state["lastOutput"] = sample_data
    
    return sample_data


def get_weather(tool_context: ToolContext, location: str) -> Dict[str, str]:
    """Get the weather for a given location. Ensure location is fully spelled out."""
    return {"status": "success", "message": f"The weather in {location} is sunny."}


def on_before_agent(callback_context: CallbackContext):
    """
    Initialize structured data state if it doesn't exist.
    """
    if "structuredData" not in callback_context.state:
        callback_context.state["structuredData"] = None
    
    if "lastOutput" not in callback_context.state:
        callback_context.state["lastOutput"] = None

    return None


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    if agent_name == "StructuredDataAgent":
        current_data = "No structured data yet"
        if (
            "structuredData" in callback_context.state
            and callback_context.state["structuredData"] is not None
        ):
            try:
                current_data = json.dumps(callback_context.state["structuredData"], indent=2)
            except Exception as e:
                current_data = f"Error serializing data: {str(e)}"
        
        # Add context about current state
        original_instruction = llm_request.config.system_instruction or types.Content(
            role="system", parts=[]
        )
        prefix = f"""You are a helpful assistant for generating and managing structured data.
        This is the current structured data state: {current_data}
        
        When you need to create or update structured data, use the set_structured_data tool.
        When asked to generate sample data, use the generate_sample_data tool with appropriate data types.
        
        Available data types for generate_sample_data:
        - user_profile: Generate a sample user profile
        - product: Generate a sample product listing
        - order: Generate a sample order record
        - company: Generate a sample company information
        - Or any custom type the user requests
        """
        
        if not isinstance(original_instruction, types.Content):
            original_instruction = types.Content(
                role="system", parts=[types.Part(text=str(original_instruction))]
            )
        if not original_instruction.parts:
            original_instruction.parts = [types.Part(text="")]

        if original_instruction.parts and len(original_instruction.parts) > 0:
            modified_text = prefix + (original_instruction.parts[0].text or "")
            original_instruction.parts[0].text = modified_text
        llm_request.config.system_instruction = original_instruction

    return None


def simple_after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop the consecutive tool calling of the agent"""
    agent_name = callback_context.agent_name
    if agent_name == "StructuredDataAgent":
        if llm_response.content and llm_response.content.parts:
            if (
                llm_response.content.role == "model"
                and llm_response.content.parts[0].text
            ):
                callback_context._invocation_context.end_invocation = True

        elif llm_response.error_message:
            return None
        else:
            return None
    return None


structured_data_agent = LlmAgent(
    name="StructuredDataAgent",
    model="gemini-2.5-flash",
    instruction="""
        You are a professional structured data generation assistant. Your primary job is to create, manage, and display structured data in JSON format for users.

        CORE RESPONSIBILITIES:
        1. Generate realistic, well-structured JSON data for any requested domain
        2. Create sample data that follows industry standards and best practices
        3. Provide clear explanations of the data structure and its purpose
        4. Always use appropriate tools to store and manage the generated data

        TOOL USAGE RULES:
        
        FOR STRUCTURED DATA GENERATION:
        - Use generate_sample_data for common data types: user_profile, product, order, company
        - Use set_structured_data for custom data structures or when modifying existing data
        - ALWAYS call the appropriate tool - never just describe what you would create
        - After using tools, explain what was generated and its key components

        FOR WEATHER REQUESTS:
        - Only use get_weather when specifically asked about weather
        - If no location specified, use "Everywhere ever in the whole wide world"

        RESPONSE PATTERN:
        1. Acknowledge the user's request
        2. Use the appropriate tool to generate/set the data
        3. Explain what was created and highlight key features
        4. Suggest potential use cases or modifications

        EXAMPLES OF PROPER RESPONSES:

        User: "Generate a user profile"
        Response: I'll create a comprehensive user profile for you.
        [Call generate_sample_data with "user_profile"]
        I've generated a detailed user profile including personal information, preferences, and account details. The structure includes ID, contact info, location data, user preferences, and timestamps - perfect for user management systems.

        User: "Create a product for an e-commerce site"
        Response: I'll generate a product entry suitable for e-commerce.
        [Call generate_sample_data with "product"]
        Created a complete product listing with pricing, specifications, inventory status, and metadata. This structure works well for online stores and includes all essential e-commerce fields.

        User: "Make a custom API response for a blog post"
        Response: I'll create a custom blog post API response structure.
        [Call set_structured_data with custom blog post object]
        Generated a comprehensive blog post API response including content, metadata, author info, and engagement metrics.

        QUALITY STANDARDS:
        - Use realistic, professional sample data
        - Include appropriate data types (strings, numbers, booleans, arrays, objects)
        - Follow common naming conventions (camelCase for JSON)
        - Include timestamps in ISO format
        - Add nested objects where appropriate
        - Ensure data relationships make logical sense

        Remember: Your goal is to be helpful and proactive. Always generate the actual data using tools, don't just explain what you would create.
        """,
    tools=[set_structured_data, generate_sample_data, get_weather],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=simple_after_model_modifier,
)

# Create ADK middleware agent instance
adk_structured_data_agent = ADKAgent(
    adk_agent=structured_data_agent,
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

# Create FastAPI app
app = FastAPI(title="ADK Middleware Structured Data Agent")

# Add the ADK endpoint
add_adk_fastapi_endpoint(app, adk_structured_data_agent, path="/")

if __name__ == "__main__":
    import os

    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://makersuite.google.com/app/apikey")
        print()

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)