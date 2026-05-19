"""
Main agent orchestrator: multi-turn conversation with LangChain + Groq.
"""
import json
import logging
from typing import Any, AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool as langchain_tool

from config import settings
from database import SessionLocal
from models import ChatMessage, ChatSession
from agent.tools import LANGCHAIN_TOOLS, execute_tool
from agent.prompts import SYSTEM_PROMPT_EN
from agent.llm import get_chat_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(db, session_id: str, language: str = "en") -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(session_id=session_id, language=language)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _load_history(db, session_id: str) -> list[dict]:
    """Load conversation history, excluding internal tool messages."""
    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = []
    for msg in messages:
        if msg.content:
            history.append({"role": msg.role, "content": msg.content})
    return history


def _save_message(db, session_id: str, role: str, content: str, tool_name: str = None):
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tool_name=tool_name,
    )
    db.add(msg)
    db.commit()


def _extract_quick_replies(text: str) -> list[str]:
    """
    Extract quick replies from assistant message.
    Only extract if the message contains suggestions/options for the user, not questions.
    """
    # Don't show quick replies if the message is asking questions (contains question marks)
    if text.count('?') >= 2:
        return []
    
    # Don't show quick replies if the message contains numbered lists (asking for info)
    if any(line.strip().startswith(f"{i}.") for i in range(1, 10) for line in text.split('\n')):
        return []
    
    lines = text.strip().split("\n")
    quick = []
    for line in reversed(lines):
        stripped = line.strip().lstrip("•-*123456789. ").strip()
        # Skip lines that are questions
        if '?' in stripped:
            continue
        if stripped and len(stripped) < 80 and len(quick) < 4:
            quick.insert(0, stripped)
        elif quick:
            break
    return quick[:4] if len(quick) >= 2 else []


# ---------------------------------------------------------------------------
# Core agent loop
# ---------------------------------------------------------------------------

async def process_chat(
    session_id: str,
    message: str,
    language: str = "en",
) -> dict:
    """
    Process one user message through the agent.
    Returns: {message, quick_replies, actions_taken}
    """
    db = SessionLocal()
    try:
        _get_or_create_session(db, session_id, language)
        history = _load_history(db, session_id)

        # Save user message
        _save_message(db, session_id, "user", message)

        # Build LangChain messages
        lc_messages = []
        for h in history:
            if h["role"] == "user":
                lc_messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_messages.append(AIMessage(content=h["content"]))
        
        lc_messages.append(HumanMessage(content=message))

        # Get LangChain model with tools
        model = get_chat_model()
        model_with_tools = model.bind_tools(LANGCHAIN_TOOLS)

        actions_taken = []
        final_text = ""

        # Agentic loop — keep calling until we get a text response without tool calls
        max_iterations = 10
        for iteration in range(max_iterations):
            print(f"🔄 Agent iteration {iteration + 1}/{max_iterations}")
            logger.info(f"Agent iteration {iteration + 1}/{max_iterations}")
            
            # Invoke model with system prompt
            response = model_with_tools.invoke(
                [{"role": "system", "content": SYSTEM_PROMPT_EN}] + lc_messages
            )

            # Check if there are tool calls
            tool_calls = getattr(response, "tool_calls", [])
            print(f"🔧 Tool calls in response: {len(tool_calls)}")
            logger.info(f"Tool calls in response: {len(tool_calls)}")

            if tool_calls:
                # Add assistant response to messages
                lc_messages.append(response)

                # Execute each tool and collect results
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    print(f"⚙️ Executing tool: {tool_name}")
                    logger.info(f"Executing tool: {tool_name}")
                    result = execute_tool(db, tool_name, tool_input)
                    print(f"✅ Tool result: {result}")
                    logger.info(f"Tool result: {result}")
                    actions_taken.append({"tool": tool_name, "result": result})

                    # Add tool result message
                    lc_messages.append(
                        ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tool_call_id,
                        )
                    )
                # Continue loop to get final response after tool execution
                print(f"➡️ Continuing to iteration {iteration + 2} after tool execution")
                logger.info(f"Continuing to iteration {iteration + 2} after tool execution")
            else:
                # No more tool calls — extract final text response
                content = response.content
                print(f"📝 Final response type: {type(content)}, content: {content}")
                logger.info(f"Final response type: {type(content)}, content: {content}")
                
                # Handle different content formats
                if isinstance(content, str) and content.strip():
                    final_text = content
                elif isinstance(content, list):
                    # Content might be a list of content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, str):
                            text_parts.append(block)
                        elif hasattr(block, 'text'):
                            text_parts.append(block.text)
                        elif isinstance(block, dict) and 'text' in block:
                            text_parts.append(block['text'])
                    final_text = '\n'.join(text_parts)
                
                print(f"✨ Extracted final_text: {final_text}")
                logger.info(f"Extracted final_text: {final_text}")
                break
        
        print(f"🏁 Exited loop after {iteration + 1} iterations. Final text: {final_text}")
        logger.info(f"Exited loop after {iteration + 1} iterations. Final text: {final_text}")

        # Save assistant message
        if final_text:
            _save_message(db, session_id, "assistant", final_text)
        else:
            final_text = "I'm here to help. How can I assist you today?"
            _save_message(db, session_id, "assistant", final_text)

        quick_replies = _extract_quick_replies(final_text)

        return {
            "message": final_text,
            "quick_replies": quick_replies,
            "actions_taken": actions_taken,
        }

    except Exception as e:
        logger.error(f"LangChain API error: {e}")
        fallback = "I'm temporarily unavailable. Please try again in a moment."
        _save_message(db, session_id, "assistant", fallback)
        return {"message": fallback, "quick_replies": [], "actions_taken": []}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Streaming variant (for WebSocket)
# ---------------------------------------------------------------------------

async def process_chat_stream(
    session_id: str,
    message: str,
    language: str = "en",
) -> AsyncGenerator[dict, None]:
    """
    Stream tokens from the agent response via generator.
    Yields dicts: {"token": str} or {"done": True, "quick_replies": [...], "actions_taken": [...]}
    """
    db = SessionLocal()
    try:
        _get_or_create_session(db, session_id, language)
        history = _load_history(db, session_id)
        _save_message(db, session_id, "user", message)

        # Build LangChain messages
        lc_messages = []
        for h in history:
            if h["role"] == "user":
                lc_messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_messages.append(AIMessage(content=h["content"]))
        
        lc_messages.append(HumanMessage(content=message))

        model = get_chat_model()
        model_with_tools = model.bind_tools(LANGCHAIN_TOOLS)

        actions_taken = []
        collected_text = ""

        # Run the tool loop first (non-streaming) until we get final text
        max_iterations = 10
        for iteration in range(max_iterations):
            print(f"🔄 Stream iteration {iteration + 1}/{max_iterations}")
            
            response = model_with_tools.invoke(
                [{"role": "system", "content": SYSTEM_PROMPT_EN}] + lc_messages
            )

            tool_calls = getattr(response, "tool_calls", [])
            print(f"🔧 Tool calls in stream response: {len(tool_calls)}")

            if tool_calls:
                lc_messages.append(response)
                for tool_call in tool_calls:
                    print(f"⚙️ Stream executing tool: {tool_call['name']}")
                    result = execute_tool(db, tool_call["name"], tool_call["args"])
                    print(f"✅ Stream tool result: {result}")
                    actions_taken.append({"tool": tool_call["name"], "result": result})
                    lc_messages.append(
                        ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tool_call["id"],
                        )
                    )
                print(f"➡️ Stream continuing to iteration {iteration + 2}")
            else:
                # No more tool calls - extract final text
                content = response.content
                print(f"📝 Stream final response type: {type(content)}, content: {content}")
                
                if isinstance(content, str) and content.strip():
                    collected_text = content
                elif isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, str):
                            text_parts.append(block)
                        elif hasattr(block, 'text'):
                            text_parts.append(block.text)
                        elif isinstance(block, dict) and 'text' in block:
                            text_parts.append(block['text'])
                    collected_text = '\n'.join(text_parts)
                
                print(f"✨ Stream extracted text: {collected_text}")
                break
        
        print(f"🏁 Stream exited loop after {iteration + 1} iterations")

        final_text = collected_text or "I'm here to help. How can I assist you today?"
        _save_message(db, session_id, "assistant", final_text)

        # Stream the text word by word
        words = final_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            yield {"token": token}

        quick_replies = _extract_quick_replies(final_text)
        yield {"done": True, "quick_replies": quick_replies, "actions_taken": actions_taken}

    except Exception as e:
        logger.exception(f"Streaming error: {e}")
        yield {"token": "I'm temporarily unavailable. Please try again."}
        yield {"done": True, "quick_replies": [], "actions_taken": []}
    finally:
        db.close()
