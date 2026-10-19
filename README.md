# Medical-voice-mcp

## Problem & Purpose

### The Problem
During surgery, the surgeon's hands are sterile and their eyes must remain fixed on the patient.
Manually checking monitors or retrieving patient data interrupts the surgical workflow, while conventional equipment only sounds generic alarms rather than alerting based on individualized thresholds.

### Primary Goal
**ScrubVoice** is a completely hands-free, voice-controlled medical assistant that queries and updates patient records in real time via the Model Context Protocol (MCP) and monitors telemetry—eliminating the need for surgeons or staff to look away or break the sterile field.

## Core Features
- **Hands-Free EHR (via MCP):** Safely queries and updates the patient database while preserving surgical sterility.
- **Real-Time Telemetry:** Verbally reports live vital signs (e.g., blood pressure, SpO2) on demand.
- **Proactive Alerts:** Monitors patient-specific critical limits and verbally alerts the team when vitals deteriorate.
- **Voice-to-Record:** Converts spoken intraoperative notes and administered medication dosages directly into structured records.

---

## Setup & Configuration

### 1. Install & Run Ollama

- **Windows:** Download and install `OllamaSetup.exe` from [ollama.com](https://ollama.com/).
- **Linux:** Run the installation script in your terminal:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
- **macOS:** Download the `.dmg` installer from [ollama.com](https://ollama.com/) or install via Homebrew:
  ```bash
  brew install ollama
  ```

Pull the local language model:
```bash
ollama run llama3.2
```

---

### 2. Python Virtual Environment & Dependencies

Create and activate a virtual environment, then install the required dependencies:

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

# Install required packages
pip install langgraph langchain-ollama langchain-core pydantic speechrecognition pyttsx3
```

---

### 3.Voice Command & Testing

| Scenario / Branch | What You Say (Doctor Input) | Target LangGraph Node | Expected Response / System Output |
| :--- | :--- | :--- | :--- |
| **Patient DB Query** | `"What is the blood pressure of John Doe?"` | `query_prompt` | Verbal report from `PATIENTS_DB` (e.g., *"Blood pressure is 120 over 80. Oxygen saturation is 98 percent..."*). |
| **Patient DB Query** | `"Check vitals for Jane Smith."` | `query_prompt` | Verbal report confirming Jane's records and allergy status. |
| **Telemetry / Device** | `"Check the pulse oximeter."` | `device_prompt` | Real-time device readout (e.g., *"Pulse oximeter: 98%"*). |
| **Telemetry / Device** | `"What are the current monitor readings?"` | `device_prompt` | Combined telemetry report from `CurrentDevice` (blood pressure & SpO2). |
| **Record Creation** | `"Add a new patient record for Mark Taylor."` | `create_prompt` | Confirmation prompt (e.g., *"I recorded the new information into the registry."*). |
| **System Shutdown** | `"Exit"` or `"Stop ScrubVoice"` | `END` | Agent responds: *"ScrubVoice shutting down."* and cleanly terminates loop. |

