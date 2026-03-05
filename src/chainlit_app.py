import chainlit as cl
from rag_chain import RAGChain

rag_chain = RAGChain()

def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return content.get("text", "") or content.get("content", "") or str(content)
    return str(content)

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("chat_history", [])


@cl.on_message
async def handle_message(message: cl.Message):
    chat_history = cl.user_session.get("chat_history") or []

    response_message = await cl.Message(content="🤔 Réflexion…\n").send()

    session_id = cl.user_session.get("id")
    full_response = ""
    async for chunk in rag_chain.ask(extract_text(message.content), chat_history, session_id):
        full_response += chunk
        await response_message.stream_token(chunk)

    await response_message.update()

    chat_history.append({"role": "user", "content": message.content})
    chat_history.append({"role": "assistant", "content": full_response})  # ← string, pas l'objet
    print(f"AI response :'{full_response}'")
    cl.user_session.set("chat_history", chat_history)