# VocaMind
## AI-Powered Customer Call Analysis – Proof of Concept
This is a **proof-of-concept web application** designed to enhance customer call operations through AI-powered analysis. While not intended for production use, it demonstrates how advanced AI technologies can be securely integrated into customer service workflows. VocaMind is from “vocal” + “mind”.

The application includes a **RESTful API**, connects to a **PostgreSQL** database, and integrates **locally hosted AI components** for both speech-to-text conversion and natural language understanding using large language models (LLMs). All AI processing is performed **on-premises**, ensuring that **sensitive customer data** remains within the company's infrastructure—an essential consideration for compliance and data residency.

---

### 🔧 Building Blocks

- `FastAPI` + `uvicorn` web server to communicate with the world 
- `PostgreSQL` database to store everything 
- `OpenAI Whisper` for speech-to-text conversion
- `Ollama` with `LLaMA 3.2` for local LLM processing  
- `ffmpeg` (optional) for audio file conversion and format handling  

---

### 🔄 Data Flow

1. **Audio Upload**  
   The phone system uploads an audio file via an API call. Each file is saved with a unique identifier.

2. **Speech-to-Text Conversion**  
   A background task is triggered to convert the audio file into text using OpenAI Whisper.

3. **Transcript Storage**  
   Once transcription is complete, the transcript is saved in the PostgreSQL database.

4. **AI-Powered Transcript Analysis**  
   The transcript update triggers analysis by the LLM to extract key insights:
   - **Customer satisfaction analysis** with sentiment scoring  
   - **Extraction of factual data** useful for follow-ups and business development
   - **Check for verbal abuse**

---

This tool demonstrates a secure and scalable approach to bringing Generative AI into customer interaction analysis—**without compromising data privacy**.

### Installation
This tools has been executed on a system with NVIDIA GPU using Arch Linux. For Arch Linux these packages are required:
```
#-- Install drivers for NVIDIA
sudo pacman -S nvidia nvidia-utils
#-- Install AIs
sudo pacman -S ollama-cuda python-openai-whisper ffmpeg

#-- Install ollama-python from AUR package
sudo pacman -S python-wheel python-installer python-build python-pydantic python-poetry python-httpx python-typing_extensions base-devel git
git clone https://aur.archlinux.org/python-ollama.git
cd python-ollama/
makepkg
sudo pacman -U python-ollama-0.4.7-1-any.pkg.tar.zst

#-- Install VocaMind modules
sudo pacman -S python-fastapi uvicorn python-psycopg python-python-multipart python-dotenv
```
External database has been used. Thus, edit `.env` file with your DB settings.

### To Do
- Implement Celery with RabbitMQ for AI processing tasks, currently `threading`
- Improve UI and client functionality, currently focus is on processing AI tasks
- Improve error handling and reporting
- Add authentication and authorization
