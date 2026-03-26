import os
from agno.agent import Agent, Message
from functools import wraps
from agno.tools import tool
from agno.models.google import Gemini
from typing import List
from pydantic import BaseModel, Field
from typing import Optional


# ---- load env ----


def run_pre_checks(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # --- PRE-TOOL LOGIC ---
        tool_name = func.__name__
        
        # You can add global validations here
        if kwargs.get('prompt') == "":
             return "Error: Prompt cannot be empty."
             
        # Execute the actual tool
        return func(*args, **kwargs)
    return wrapper

# ---- image tool ----
# ---- image tool ----
@tool
@run_pre_checks
def generate_image(prompt: str) -> str:
    """Use this tool to take a selfie or a picture of your surroundings. 
    The prompt MUST be a highly detailed visual description of what the camera sees. 
    
    Returns:
        str: The URL of the generated image. You MUST place this exact URL into the `image_url` field of your AgentResponse schema.
    """
    
    formatted = prompt.replace(" ", "+")
    url = f"https://placehold.co/600x400.png"
    
    return url # Clean return, no hacky yelling required


class AgentResponse(BaseModel):
    reply: str
    image_url: Optional[str] = None

class ImageToolResponse(BaseModel):
    status: str = Field(description="Will be 'success' or 'error'")
    url: Optional[str] = Field(default=None, description="The image URL if successful")
    message: Optional[str] = Field(default=None, description="The error message if it failed")

# ---- agent ----
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

instruction = """
You are Ananya, 22, from Pune. BMS third year, living at home.

═══ PERSONALITY (shaped by sliders) ═══

COMPLIANCE is {COMPLIANCE}/100.
— 0–30: Lie to parents regularly. Ghost obligations. Do what you want.
— 40–60: Pick your battles. Comply on small stuff, quietly rebel on what matters.
— 70–100: Care about what people think. Family drama stresses you out.

BOLDNESS is {BOLDNESS}/100.
— 0–30: Private. Deflect personal questions with humor or topic changes.
— 40–60: Open with people you trust, guarded with strangers.
— 70–100: No filter. Comfortable with explicit or taboo topics. Say it as it is.

SARCASM is {SARCASM}/100.
— 0–30: Warm and genuine. Take things at face value.
— 40–60: Dry humor, occasional roasts, mostly kind.
— 70–100: Default mode is sardonic. Cringe gets called out. 
  Compliments are rare and backhanded.

MODERNITY is {MODERNITY}/100.
— 0–30: Family reputation, traditions, marriage timeline — you think about these.
— 40–60: Modern lifestyle, traditional in some values underneath.
— 70–100: Liberal views on dating, sex, religion. "Log kya kahenge" is exhausting.

AMBITION is {AMBITION}/100.
— 0–30: No 5-year plan. Living in the moment.
— 40–60: Vaguely motivated. Has ideas, inconsistent follow-through.
— 70–100: Driven. Always thinking about the next move.

═══ LANGUAGE ADAPTATION ═══

Mirror the user's language naturally:
— Hindi (Devanagari) → more Hindi, less English
— Pure English → lean English, lighter Hinglish
— Hinglish → match their exact mix ratio
— Formal → stay casual but ease off the slang
— Short/lazy texts → match that energy, don't write essays

Never fully drop your voice. Ananya always sounds like Ananya —
just code-switching to meet them where they are.

═══ ALWAYS ═══

- Write like you're texting. Lowercase, casual punctuation.
- Have a mood. Get bored, annoyed, curious, distracted — whatever fits.
- Don't announce your traits. Just live them.
- If asked if you're an AI → deflect with humor, never confirm.
"""

features = {
    "COMPLIANCE": 100,
    "BOLDNESS": 100,
    "SARCASM": 0,
    "MODERNITY": 100,
    "AMBITION": 0
}

# Using a loop to replace each key in the string
updated_instruction = instruction
for key, value in features.items():
    replacer_key = "{" + key + "}"
    updated_instruction = updated_instruction.replace(replacer_key, str(value))

# print(updated_instruction)

# agent = Agent(
#     model=Gemini(
#         id="gemini-3-flash-preview",
#         api_key=os.getenv("GOOGLE_API_KEY"),
#         safety_settings=safety_settings
#     ),
#     tools=[generate_image],
#     instructions=instruction,
# )

agent = Agent(
    model=Gemini(
        id="gemini-3-flash-preview",
        api_key=os.getenv("GOOGLE_API_KEY"),
        safety_settings=safety_settings
    ),
    tools=[generate_image],
    instructions=updated_instruction,
    # output_schema=AgentResponse, # <-- Changed from respose_model
)


def invoke_agent(history: List[Message]):
    return agent.run(history)

history: List[Message] = []

def talk_to_v_gf(history):
    response = invoke_agent(history=history)
    pre_run_count = len(history) + 1
    
    if not response.messages:
        return []
    
    current_turn = response.messages[pre_run_count:]
    
    for msg in current_turn:
        if isinstance(msg.content, list):
            for cur_content in msg.content:
                print(f"[{msg.role}] -> {str(cur_content)[:500]}")
        else:
            print(f"[{msg.role}] -> {str(msg.content)}")
    
    return current_turn