import speech_recognition as sr
import pyttsx3
from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

llm = ChatOllama(model="llama3.2", temperature=0)

# Currently, this is a local mock dictionary.
# Later, this dictionary should NOT be stored here. Instead, an MCP client will be initialized:
PATIENTS_DB = {
    "john doe": "Blood pressure is 120 over 80. Oxygen saturation is 98 percent. Allergic to Penicillin.",
    "jane smith": "Blood pressure is 90 over 60. Oxygen saturation is 95 percent. No known allergies.",
}

CurrentDevice = {
    "Bloodpressure": "120",
    "Pulse oximeter": "98%"
}


# 2. Hangmotorok (TTS & STT)
def speak(text: str):
    print(f"\n[ScrubVoice answer]: {text}")
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.say(text)
    engine.runAndWait()


def listen_to_doctor() -> str | None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n" + "=" * 45)
        print("[ScrubVoice] I'm listening... (Speak into the microphone)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[Doctor]: \"{text}\"")
        return text
    except sr.UnknownValueError:
        print("[System]: Unable to interpret the audio.")
        return None
    except sr.RequestError as e:
        print(f"[System]: Network error: {e}")
        return None

class IntentClassifier(BaseModel):
    message_intent: Literal["device", "query", "create"] = Field(
        ...,
        description=(
            "Classify user intention: "
            "'device' to check telemetry/vital monitors, "
            "'query' to read or look up patient data from database, "
            "'create' to add, note, or save new patient records."
        )
    )


class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_intent: str | None


# 4. Csomópontok (Jelzik ha elérte őket a vezérlés)
def classify_intent(state: State):
    print("\n>>> [NODE: Classifier] Determining intent in progress...")
    structured_llm = llm.with_structured_output(IntentClassifier)

    user_msg = state['messages'][-1].content
    result = structured_llm.invoke([
        {'role': 'system', 'content': 'Classify user intent into: device, query, or create.'},
        {'role': 'user', 'content': user_msg}
    ])

    print(f">>> [NODE: Classifier] Selected Route: {result.message_intent}")
    return {'message_intent': result.message_intent}


def prompt_llm_device(state: State):
    print("\n>>> [NODE: Device] Running the Device/Telemetry branch...")
    system_prompt = f"You are ScrubVoice. Current operating room devices: {CurrentDevice}. Answer very briefly."
    messages = [{'role': 'system', 'content': system_prompt}] + state['messages']

    response = llm.invoke(messages)
    speak(response.content)
    return {'messages': [{'role': 'assistant', 'content': response.content}]}


def prompt_llm_query(state: State):
    print("\n>>> [NODE: Query] Running a database query thread...")
    system_prompt = f"You are ScrubVoice. Clinical patient records: {PATIENTS_DB}. Answer clinical queries briefly."
    messages = [{'role': 'system', 'content': system_prompt}] + state['messages']

    response = llm.invoke(messages)
    speak(response.content)
    return {'messages': [{'role': 'assistant', 'content': response.content}]}


def prompt_llm_create(state: State):
    print("\n>>> [NODE: Create] Running the “Set Record” branch...")
    confirmation = "I recorded the new information into the registry."
    speak(confirmation)
    return {'messages': [{'role': 'assistant', 'content': confirmation}]}

graph_builder = StateGraph(State)

graph_builder.add_node('classifier', classify_intent)
graph_builder.add_node('device_prompt', prompt_llm_device)
graph_builder.add_node('query_prompt', prompt_llm_query)
graph_builder.add_node('create_prompt', prompt_llm_create)

graph_builder.add_edge(START, 'classifier')

graph_builder.add_conditional_edges(
    'classifier',
    lambda state: state['message_intent'],
    {
        'device': 'device_prompt',
        'query': 'query_prompt',
        'create': 'create_prompt'
    }
)

graph_builder.add_edge('device_prompt', END)
graph_builder.add_edge('query_prompt', END)
graph_builder.add_edge('create_prompt', END)

checkpointer = InMemorySaver()
app = graph_builder.compile(checkpointer=checkpointer)
if __name__ == "__main__":
    speak("ScrubVoice online.")

    config = {"configurable": {"thread_id": "operating_room_1"}}

    while True:
        doctor_text = listen_to_doctor()
        if not doctor_text:
            continue

        if any(exit_word in doctor_text.lower() for exit_word in ["exit", "quit", "stop"]):
            speak("ScrubVoice shutting down.")
            break
        app.invoke(
            {
                "messages": [{'role': 'user', 'content': doctor_text}],
                "message_intent": None
            },
            config=config
        )